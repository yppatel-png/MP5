"""Student-led onboarding for the source-backed IIT Bhilai CSE programmes."""

import re
from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.api.programmes import CurriculumProgramme, load_programme_catalog
from backend.db.onboarding_store import (
    get_onboarding_profile,
    save_onboarding_profile,
    update_onboarding_profile,
)
from backend.llm.client import llm_client

router = APIRouter(prefix="/onboarding", tags=["Student onboarding"])
SUPPORTED_STATUS = "curriculum_available"


class OnboardingProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    programme_id: str
    current_semester: int = Field(ge=1)
    cgpa: float = Field(ge=0, le=10)
    available_hours_per_week: float = Field(ge=0, le=80)
    goal: str = Field(min_length=1, max_length=160)
    interests: List[str] = Field(default_factory=list, max_length=12)
    completed_course_codes: List[str] = Field(default_factory=list, max_length=80)
    shortlisted_course_codes: List[str] = Field(default_factory=list, max_length=40)


class OnboardingProfileResponse(OnboardingProfileRequest):
    student_id: str


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class OnboardingAssistantRequest(BaseModel):
    profile_id: str = Field(min_length=1, max_length=32)
    question: str = Field(min_length=1, max_length=2000)
    share_with_gemini: bool = False
    history: List[ChatTurn] = Field(default_factory=list, max_length=8)


class OnboardingAssistantResponse(BaseModel):
    reply: str
    mode: Literal["local", "offline", "gemini"]
    privacy_note: str


def _programme(programme_id: str) -> CurriculumProgramme:
    programme = next(
        (
            item
            for item in load_programme_catalog().programmes
            if item.id == programme_id
        ),
        None,
    )
    if programme is None or programme.status != SUPPORTED_STATUS:
        raise HTTPException(
            status_code=422,
            detail="Choose a programme with a curriculum in the supplied IIT Bhilai source.",
        )
    return programme


def _programme_course_codes(programme: CurriculumProgramme) -> set[str]:
    codes = set()
    for semester in programme.semesters:
        for course in semester.courses:
            if course.placeholder:
                continue
            for code in re.split(r"\s+or\s+", course.code):
                if re.fullmatch(r"[A-Z]{2,3}\d{3}", code):
                    codes.add(code)
    codes.update(
        code
        for variant in load_programme_catalog().source.code_variants
        if variant.programme_id == programme.id
        for code in variant.codes
    )
    return codes


def _validate_profile_choices(
    payload: OnboardingProfileRequest,
    programme: CurriculumProgramme,
) -> tuple[list[str], list[str]]:
    if payload.current_semester > len(programme.semesters):
        raise HTTPException(
            status_code=422,
            detail=f"{programme.degree} CSE has {len(programme.semesters)} semesters in this source.",
        )

    completed = [code.strip().upper() for code in payload.completed_course_codes]
    if len(set(completed)) != len(completed):
        raise HTTPException(status_code=422, detail="A completed course may only be entered once.")
    allowed_completed = _programme_course_codes(programme)
    unknown_completed = sorted(set(completed) - allowed_completed)
    if unknown_completed:
        raise HTTPException(
            status_code=422,
            detail=f"These completed course codes are not named in this programme sequence: {', '.join(unknown_completed)}.",
        )

    catalogue_codes = {
        course.code for course in load_programme_catalog().catalogue_courses
    }
    shortlisted = [code.strip().upper() for code in payload.shortlisted_course_codes]
    if len(set(shortlisted)) != len(shortlisted):
        raise HTTPException(status_code=422, detail="A catalogue course may only be shortlisted once.")
    unknown_shortlisted = sorted(set(shortlisted) - catalogue_codes)
    if unknown_shortlisted:
        raise HTTPException(
            status_code=422,
            detail=f"These codes are not in the supplied CSE catalogue: {', '.join(unknown_shortlisted)}.",
        )
    return completed, shortlisted


def _validated_request_profile(
    payload: OnboardingProfileRequest,
) -> dict:
    programme = _programme(payload.programme_id)
    completed, shortlisted = _validate_profile_choices(payload, programme)
    return {
        **payload.model_dump(exclude={"completed_course_codes", "shortlisted_course_codes"}),
        "completed_course_codes": completed,
        "shortlisted_course_codes": shortlisted,
    }


@router.post(
    "/profiles",
    response_model=OnboardingProfileResponse,
    status_code=201,
)
def create_onboarding_profile(
    payload: OnboardingProfileRequest,
) -> OnboardingProfileResponse:
    profile = _validated_request_profile(payload)
    profile["student_id"] = f"BH-{uuid4().hex[:10].upper()}"
    save_onboarding_profile(profile)
    return OnboardingProfileResponse.model_validate(profile)


@router.get(
    "/profiles/{student_id}",
    response_model=OnboardingProfileResponse,
)
def read_onboarding_profile(student_id: str) -> OnboardingProfileResponse:
    profile = get_onboarding_profile(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Onboarding profile not found.")
    return OnboardingProfileResponse.model_validate(profile)


@router.put(
    "/profiles/{student_id}",
    response_model=OnboardingProfileResponse,
)
def update_onboarding_profile_route(
    student_id: str,
    payload: OnboardingProfileRequest,
) -> OnboardingProfileResponse:
    if get_onboarding_profile(student_id) is None:
        raise HTTPException(status_code=404, detail="Onboarding profile not found.")
    profile = _validated_request_profile(payload)
    profile["student_id"] = student_id
    if not update_onboarding_profile(profile):
        raise HTTPException(status_code=404, detail="Onboarding profile not found.")
    return OnboardingProfileResponse.model_validate(profile)


def _grounded_local_reply(
    profile: dict,
    programme: CurriculumProgramme,
    question: str,
) -> str:
    semester = next(
        item
        for item in programme.semesters
        if item.semester == profile["current_semester"]
    )
    named_courses = [
        f"{course.code} — {course.title}"
        for course in semester.courses
        if not course.placeholder
    ]
    course_summary = ", ".join(named_courses) or "No named course is listed for this semester."
    electives_note = (
        "The supplied curriculum lists PE/OE credit slots but does not map the catalogue "
        "courses to those slots; confirm eligibility with IIT Bhilai before enrollment."
    )
    if "elective" in question.casefold() or "catalog" in question.casefold():
        return (
            f"For {programme.name}, the source lists these courses for semester "
            f"{semester.semester}: {course_summary}. {electives_note} "
            "This prototype can shortlist catalogue interests, but it does not enroll students."
        )
    return (
        f"Your source-backed starting point is {programme.name}, semester "
        f"{semester.semester}. Review the listed courses: {course_summary}. "
        "Next, confirm your completed courses and grades, review any PE/OE choices with "
        "your programme office, and complete registration through IIT Bhilai. "
        f"{electives_note} This prototype provides guidance; it does not enroll students."
    )


@router.post(
    "/assistant",
    response_model=OnboardingAssistantResponse,
)
def ask_onboarding_assistant(
    payload: OnboardingAssistantRequest,
) -> OnboardingAssistantResponse:
    profile = get_onboarding_profile(payload.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Onboarding profile not found.")
    programme = _programme(profile["programme_id"])
    local_reply = _grounded_local_reply(profile, programme, payload.question)
    if not payload.share_with_gemini:
        return OnboardingAssistantResponse(
            reply=local_reply,
            mode="local",
            privacy_note="Your profile details and message were not sent to Gemini.",
        )

    semester = next(
        item
        for item in programme.semesters
        if item.semester == profile["current_semester"]
    )
    context = {
        "source": load_programme_catalog().source.title,
        "source_pages": {
            "BTech curriculum": [21, 22],
            "MTech curriculum": [42],
            "course catalogue": [course.page for course in load_programme_catalog().catalogue_courses],
        },
        "programme": programme.name,
        "current_semester": profile["current_semester"],
        "current_semester_courses": [
            course.model_dump()
            for course in semester.courses
        ],
        "completed_course_codes_reported_by_student": profile["completed_course_codes"],
        "shortlisted_course_codes": profile["shortlisted_course_codes"],
        "goal": profile["goal"],
        "interests": profile["interests"],
        "available_hours_per_week": profile["available_hours_per_week"],
        "catalogue_courses": [
            course.model_dump()
            for course in load_programme_catalog().catalogue_courses
        ],
        "source_limitation": (
            "The PDF does not identify which catalogue-only courses are PE/OE eligible. "
            "Do not claim elective eligibility or invent courses."
        ),
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful IIT Bhilai CSE onboarding guide. Use only the supplied "
                "official curriculum context. Distinguish required programme-table courses "
                "from catalogue-only courses. The source does not establish PE/OE eligibility "
                "for catalogue-only courses; say so clearly. Cite supplied page references "
                "when useful. Explain next steps in plain language. This app is an advisor, "
                "not IIT Bhilai registration, and cannot confirm enrollment."
            ),
        },
        {
            "role": "system",
            "content": f"Verified source context:\n{context}",
        },
        *[turn.model_dump() for turn in payload.history],
        {"role": "user", "content": payload.question},
    ]
    result = llm_client.generate(
        call_type="BUDDY_CHAT",
        messages=messages,
        temperature=1.0,
        max_tokens=500,
        timeout_seconds=6.0,
        max_retries=0,
        known_valid_courses=sorted(
            {course.code for course in load_programme_catalog().catalogue_courses}
            | _programme_course_codes(programme)
        ),
        fallback_data={"deterministic_reply": local_reply},
    )
    used_fallback = bool(result["fallback_used"])
    return OnboardingAssistantResponse(
        reply=result["content"],
        mode="offline" if used_fallback else "gemini",
        privacy_note=(
            "The profile name and ID were not sent. Your programme, academic details, "
            "interests, shortlist, and conversation were sent to Gemini for this reply."
            if not used_fallback
            else "Gemini was requested, but no live response was used; the local course-grounded fallback answered."
        ),
    )
