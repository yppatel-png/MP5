"""Source-backed IIT Bhilai CSE programmes and course catalogue."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/curricula", tags=["Programmes and curriculum"])
CURRICULA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "seed"
    / "iit_bhilai_cse_curricula.json"
)


class CatalogueSource(BaseModel):
    title: str
    applicable_from: str
    file: str
    pages: List[int]
    source_register: str
    code_variants: List["CourseCodeVariant"] = Field(default_factory=list)
    limitations: List[str]


class CourseCodeVariant(BaseModel):
    programme_id: str
    codes: List[str]
    note: str


class CatalogueCourse(BaseModel):
    code: str
    title: str
    credits: float
    ltp: Tuple[int, int, int]
    page: int
    programme_table_status: str
    note: Optional[str] = None


class CurriculumCourse(BaseModel):
    code: str
    title: str
    credits: Optional[float] = None
    category: Optional[str] = None
    choice: Optional[bool] = None
    placeholder: Optional[bool] = None
    note: Optional[str] = None


class CurriculumSemester(BaseModel):
    semester: int
    stated_credits: float
    courses: List[CurriculumCourse]


class CurriculumProgramme(BaseModel):
    id: str
    institution: str
    department: str
    degree: str
    name: str
    applicable_from: Optional[str] = None
    status: str
    minimum_credits: Optional[float] = None
    additional_non_graded_core_units: Optional[int] = None
    credit_categories: Dict[str, float]
    non_graded_core: List[CurriculumCourse] = Field(default_factory=list)
    semesters: List[CurriculumSemester] = Field(default_factory=list)
    note: Optional[str] = None


class ProgrammeCatalog(BaseModel):
    source: CatalogueSource
    catalogue_courses: List[CatalogueCourse]
    programmes: List[CurriculumProgramme]


@lru_cache(maxsize=1)
def load_programme_catalog() -> ProgrammeCatalog:
    if not CURRICULA_FILE.is_file():
        raise FileNotFoundError(f"Required curriculum data is missing: {CURRICULA_FILE}")
    raw = json.loads(CURRICULA_FILE.read_text(encoding="utf-8"))
    return ProgrammeCatalog.model_validate(raw)


@router.get("", response_model=ProgrammeCatalog)
def list_programmes() -> ProgrammeCatalog:
    return load_programme_catalog()


@router.get("/{programme_id}", response_model=CurriculumProgramme)
def get_programme(programme_id: str) -> CurriculumProgramme:
    catalogue = load_programme_catalog()
    programme = next(
        (item for item in catalogue.programmes if item.id == programme_id),
        None,
    )
    if programme is None:
        raise HTTPException(status_code=404, detail="Programme not found.")
    return programme
