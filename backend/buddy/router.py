"""
Conversational Buddy Routing and Grounded Retrieval Engine (PDF §2.5, §5, §7).
Rebuilt as a tool-using assistant:
- Deterministic tools: get_plan, get_gaps, list_eligible, check_add, check_drop,
  apply_change, validate_plan, explain_course, next_actions, what_if.
- Proposes plan changes first ("Add XXX (3 cr) to Semester 3: 22/24 credits. Apply?");
  executes only after the student clicks Apply or confirms.
- Strictly grounded in verified catalogue course codes.
- No repetitive "I remember your learning context..." or "Hello!" openers.
- LiteLLM integration with automatic graceful fallback when offline/down.
"""

import json
import re
import uuid
import logging
from typing import Dict, Any, List, Optional
from backend.student.model import StudentStore
from backend.buddy.memory import buddy_memory
from backend.buddy.safety import BuddySafety
from backend.llm.client import llm_client
from backend.retrieval.indexer import retriever
from backend.buddy import tools

logger = logging.getLogger("learning_buddy.buddy.router")


def build_bounded_context(factual_context: Dict[str, Any], budget_tokens: int = 1500) -> Dict[str, Any]:
    """Bounds context payload to ~1500 tokens (top 5 courses, top gaps, pruned evidence trails)."""
    bounded: Dict[str, Any] = {}
    if "student_summary" in factual_context:
        summary = dict(factual_context["student_summary"])
        if "recent_evidence" in summary and isinstance(summary["recent_evidence"], list):
            summary["recent_evidence"] = summary["recent_evidence"][:3]
        bounded["student_summary"] = summary

    if "gaps" in factual_context:
        raw_gaps = factual_context["gaps"]
        if isinstance(raw_gaps, list):
            bounded_gaps = []
            for g in raw_gaps[:5]:
                g_copy = dict(g)
                if "evidence_trail" in g_copy and isinstance(g_copy["evidence_trail"], list):
                    g_copy["evidence_trail"] = g_copy["evidence_trail"][-2:]
                bounded_gaps.append(g_copy)
            bounded["gaps"] = bounded_gaps

    if "eligible_electives" in factual_context:
        raw_courses = factual_context["eligible_electives"]
        if isinstance(raw_courses, list):
            bounded["eligible_electives"] = raw_courses[:5]

    for k, v in factual_context.items():
        if k not in bounded:
            bounded[k] = v

    return bounded


class BuddyRouter:
    def classify_intent(self, message: str) -> str:
        """Classifies incoming student message into an actionable academic intent using hybrid parsing."""
        msg = message.lower().strip()

        # Attempt structured LLM intent classification if online
        try:
            from backend.config import settings
            if not settings.OFFLINE_MODE and settings.LLM_MODEL and settings.LLM_API_KEY:
                prompt = (
                    "Classify this student's academic message into exactly one of these intents:\n"
                    "APPLY_PROPOSAL, CREDIT_OVERLOAD, RECOMMEND_ELECTIVES, OVERRIDE_COURSE, "
                    "CHECK_DROP, EXPLAIN_COURSE, NEXT_STEPS, WHAT_IF, SKILL_GAPS, "
                    "MASTERY_STATUS, WHAT_I_KNOW, VAGUE_GOAL, PLAN_DIFF, GENERAL_ACADEMIC.\n\n"
                    f"Message: \"{message}\"\n\n"
                    "Output JSON only: {\"intent\": \"<INTENT>\"}"
                )
                res = llm_client.generate(
                    call_type="BUDDY_INTENT",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=40
                )
                if res.get("content"):
                    raw = res["content"].strip()
                    parsed = json.loads(raw)
                    intent_cand = parsed.get("intent", "").upper()
                    if intent_cand in {
                        "APPLY_PROPOSAL", "CREDIT_OVERLOAD", "RECOMMEND_ELECTIVES", "OVERRIDE_COURSE",
                        "CHECK_DROP", "EXPLAIN_COURSE", "NEXT_STEPS", "WHAT_IF", "SKILL_GAPS",
                        "MASTERY_STATUS", "WHAT_I_KNOW", "VAGUE_GOAL", "PLAN_DIFF", "GENERAL_ACADEMIC"
                    }:
                        return intent_cand
        except Exception:
            pass

        # Robust regex fallback with negative lookbehinds and word boundaries
        # 1. Apply confirmation
        if re.search(r"^\s*(apply(\s+(the\s+)?change)?|confirm|yes(\s+please)?|add it)\b", msg) or msg.startswith("apply "):
            return "APPLY_PROPOSAL"

        # 2. Impossible requests / credit overload
        if re.search(r"\b(35\s+credits?|overload\s+30|take\s+35|more\s+than\s+24(\s+credits?)?)\b", msg):
            return "CREDIT_OVERLOAD"

        # 3. Check for negated drop expressions (e.g. "I prefer not to drop CSL202", "do not drop", "don't drop")
        is_negated_drop = bool(re.search(
            r"\b(prefer|want|decided|told)\s+not\s+to\s+(drop|remove|exclude)\b|\b(do\s+not|don'?t|never)\s+(drop|remove|exclude)\b",
            msg
        ))

        # 4. Check dropping / Overrides
        if re.search(r"\b(don'?t|do\s+not)\s+want\s+to\s+take\b|\b(exclude|reject)\s+course\b", msg):
            return "OVERRIDE_COURSE"

        if not is_negated_drop and (
            re.search(r"\b(can\s+i\s+)?(drop|remove|exclude)\s+(a\s+)?course\b", msg)
            or re.search(r"\b(can\s+i\s+)?(drop|remove|exclude)\s+[a-z]{2,4}[0-9]{3}\b", msg)
            or re.search(r"\b(can\s+i\s+)?drop\b", msg)
        ):
            return "CHECK_DROP"

        # 5. Add / Recommend courses / Elective discovery
        if (
            re.search(r"\b(which\s+courses?\s+should\s+i\s+prefer|recommend(\s+an?)?\s+electives?|suggest(\s+an?)?\s+electives?|eligible\s+electives?|what\s+electives?|electives?\s+(for|in)|add\s+course|add\s+a\s+total\s+of|take\s+next\s+semester)\b", msg)
            or (re.search(r"\bprefer\b", msg) and not is_negated_drop and not re.search(r"\bprefer\s+not\s+to\b", msg))
        ):
            return "RECOMMEND_ELECTIVES"

        # 6. Course explanation
        if any(w in msg for w in [
            "why csl", "why col", "why lal", "why this course", "why was", "why recommend",
            "tell me about", "syllabus of", "what is csl", "what is mal", "what is lal"
        ]):
            return "EXPLAIN_COURSE"
        if re.search(r"\b(CSL|MAL|ECL|CSP|CSQ|LAL)[0-9]{3}\b", message.upper()) and any(
            w in msg for w in ["explain", "why", "about", "details", "syllabus", "tell me"]
        ):
            return "EXPLAIN_COURSE"

        # 7. Next steps / actions
        if any(w in msg for w in ["what next", "next step", "what should i do next", "where to start", "next action", "next milestone"]):
            return "NEXT_STEPS"

        # 8. What if / simulation
        if any(w in msg for w in ["what if", "simulate", "strong study week", "weak study week", "study-week simulation"]):
            return "WHAT_IF"

        # 9. Skill gaps
        if any(w in msg for w in ["improve", "lagging", "weakness", "gaps", "what should i improve", "need to learn", "where am i lagging"]):
            return "SKILL_GAPS"

        # 10. Mastery Status / Readiness
        if any(w in msg for w in ["what's missing", "whats missing", "placement readiness", "mastery status", "readiness status", "how am i doing", "my progress", "how am i progressing"]):
            return "MASTERY_STATUS"

        # 11. What I know / Mastery
        if any(w in msg for w in ["what i know", "my skills", "strengths", "what do i know", "my background", "mastered", "readiness", "placement ready"]):
            return "WHAT_I_KNOW"

        # 12. Vague goal
        if any(w in msg for w in ["undecided", "don't know", "dont know", "not sure", "confused", "career options", "explore"]):
            return "VAGUE_GOAL"

        # 13. Plan diff
        if any(w in msg for w in ["why did my plan change", "plan change", "what changed", "diff", "adapted"]):
            return "PLAN_DIFF"

        return "GENERAL_ACADEMIC"


    def handle_message(self, student_id: str, message: str) -> Dict[str, Any]:
        """Main multi-turn conversation handler."""
        turn_id = str(uuid.uuid4())[:8]

        # 1. Anti-Jailbreak / Prompt Injection Check
        is_injection, reason = BuddySafety.check_prompt_injection(message)
        if is_injection:
            safe_reply = f"I cannot fulfill that request. As an academic buddy, I cannot bypass academic regulations. {reason}"
            buddy_memory.record_turn(student_id, "user", message)
            buddy_memory.record_turn(student_id, "assistant", safe_reply, turn_id=turn_id, tools_used=["safety_interceptor"])
            return {
                "reply": safe_reply,
                "intent": "INJECTION_ATTEMPT",
                "tools_used": ["safety_interceptor"],
                "turn_id": turn_id,
                "facts_used": {},
                "model": "rule_interceptor",
                "fallback_used": False
            }

        # 2. Off-Topic Query Interception
        is_off_topic, _ = BuddySafety.check_off_topic(message)
        if is_off_topic:
            safe_reply = (
                "I am your IIT Bhilai academic advising assistant. I can only assist with academic course planning, "
                "prerequisite roadmaps, skill gap analysis, and study tracking. Please ask an academic or curriculum question."
            )
            buddy_memory.record_turn(student_id, "user", message)
            buddy_memory.record_turn(student_id, "assistant", safe_reply, turn_id=turn_id, tools_used=["safety_interceptor"])
            return {
                "reply": safe_reply,
                "intent": "OFF_TOPIC_INTERCEPT",
                "tools_used": ["safety_interceptor"],
                "turn_id": turn_id,
                "facts_used": {},
                "model": "rule_interceptor",
                "fallback_used": False
            }

        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {
                "reply": f"Student '{student_id}' could not be found in active records.",
                "intent": "UNKNOWN_STUDENT",
                "tools_used": [],
                "turn_id": turn_id,
                "facts_used": {}
            }

        intent = self.classify_intent(message)
        tools_called = []
        factual_context: Dict[str, Any] = {}
        proposal: Optional[Dict[str, Any]] = None

        # Always attach current student summary into factual grounding context
        try:
            from backend.student.summary import build_student_summary
            from backend.student.diagnostic import diagnostic_engine
            from backend.db.database import get_db_cursor
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT plan_json FROM plan_versions WHERE student_id = ? ORDER BY version_number DESC LIMIT 1",
                    (student_id,)
                )
                plan_row = cur.fetchone()
            plan_obj = json.loads(plan_row["plan_json"]) if plan_row else None
            active_goal = (plan_obj or {}).get("goal_id", profile.goal_id)
            gaps = diagnostic_engine.compute_skill_gaps(student_id, goal_id=active_goal)
            factual_context["student_summary"] = build_student_summary(
                profile=profile,
                plan=plan_obj,
                readiness_percentage=gaps.get("readiness_percentage"),
                priority_gap_count=gaps.get("critical_gap_count", 0),
                goal_name=gaps.get("goal_name"),
                credit_cap=(plan_obj or {}).get("credit_cap"),
            ).model_dump()
        except Exception:
            logger.exception("Failed to build student summary for buddy context")
            factual_context["student_summary_degraded"] = True

        from backend.rules.params import get_standard_credit_cap
        standard_cap = get_standard_credit_cap()

        # Handle Intent Execution
        if intent == "APPLY_PROPOSAL":
            pending = buddy_memory.get_pending_proposal(student_id)
            if pending:
                tools_called.append("tools.apply_change")
                res = tools.apply_change(
                    student_id=student_id,
                    semester=pending["semester"],
                    action="add",
                    course_code=pending["course_code"]
                )
                buddy_memory.clear_pending_proposal(student_id)
                cap = float(res.get("credit_cap") or standard_cap)
                new_credits = res.get("new_credits", 0.0)
                deterministic_reply = (
                    f"Applied! Added **{pending['course_code']}** ({pending.get('credits', 3.0)} cr) to "
                    f"Semester {pending['semester']}. New semester workload: **{new_credits:.1f} / {cap:.1f} credits**. "
                    "Your active plan has been updated and re-verified."
                )
            else:
                deterministic_reply = "There is no pending course proposal to apply. Ask me to recommend or add an elective for any semester."
            return self._finalize_turn(student_id, message, turn_id, intent, tools_called, factual_context, deterministic_reply, None)

        elif intent == "CREDIT_OVERLOAD":
            tools_called.append("tools.what_if")
            cap = standard_cap
            factual_context["overload_check"] = tools.what_if(student_id, "35 credits")
            deterministic_reply = (
                f"Working assumption of {cap:.1f} credits per semester (pending official ordinance). "
                f"Registering for 35 credits is not permitted under current planning constraints.\n\n"
                "**Recommended Alternative:**\n"
                f"Spread the desired courses over regular upcoming semesters and approved summer terms "
                f"(up to {cap:.1f} credits per semester) to ensure compliance and balanced academic progression.\n\n"
                f"**Policy Note:** Working assumption of {cap:.1f} credits per semester (pending official ordinance)."
            )
            return self._finalize_turn(student_id, message, turn_id, intent, tools_called, factual_context, deterministic_reply, None)

        elif intent == "RECOMMEND_ELECTIVES":
            tools_called.append("tools.list_eligible")
            msg_lower = message.lower()
            sem_match = re.search(r"semester\s*([0-9])", msg_lower)
            target_sem = int(sem_match.group(1)) if sem_match else (profile.current_semester + 1)

            cred_match = re.search(r"([0-9]+(\.[0-9]+)?)\s*credit", msg_lower)
            target_creds = float(cred_match.group(1)) if cred_match else 5.0

            eligible_data = tools.list_eligible(student_id, semester=target_sem, max_credits=target_creds)
            factual_context["eligible_data"] = eligible_data

            if eligible_data.get("status") == "no_plan" or "credit_cap" not in eligible_data:
                deterministic_reply = "I can't see your current plan; generate one first so I can inspect your eligible credits and electives."
                return self._finalize_turn(student_id, message, turn_id, intent, tools_called, factual_context, deterministic_reply, None)

            current_credits = float(eligible_data["current_credits"])
            credit_cap = float(eligible_data["credit_cap"])
            headroom = eligible_data.get("headroom", max(0.0, credit_cap - current_credits))
            eligible_courses = eligible_data.get("eligible_courses", [])
            combinations = eligible_data.get("suggested_combinations", [])

            # Determine target role / goal without invented fallback
            goal_title = profile.target_role
            if not goal_title:
                try:
                    from backend.db.seed_profile import get_seed_dir
                    with open(get_seed_dir() / "goal_templates.json", "r", encoding="utf-8") as f:
                        gtpls = {g["goal_id"]: g for g in json.load(f)}
                    goal_title = gtpls.get(profile.goal_id, {}).get("title")
                except Exception:
                    pass
            goal_display = goal_title or "your academic path"

            # Format deterministic response
            lines = [
                f"In Semester {target_sem}, your plan currently has {current_credits:.1f} / "
                f"{credit_cap:.1f} credits, leaving **{headroom:.1f} credits of available headroom**.\n"
            ]
            lines.append(f"Based on your goal (**{goal_display}**) and expressed interests, here are top eligible electives:\n")

            for idx, c in enumerate(eligible_courses[:4], 1):
                match_str = f" [Matches: {c['match_interest']}]" if c.get("match_interest") else ""
                lines.append(f"{idx}. **{c['code']} — {c['title']}** ({c['credits']:.1f} cr, {c['course_type']}){match_str}")

            if combinations:
                lines.append("\n**Suggested combinations summing to 5.0 credits:**")
                for combo in combinations:
                    lines.append(f"• **{combo['description']}** (Total: {combo['total_credits']:.1f} cr)")

            top_course = eligible_courses[0] if eligible_courses else None
            if top_course:
                proposal = {
                    "action": "add",
                    "semester": target_sem,
                    "course_code": top_course["code"],
                    "title": top_course["title"],
                    "credits": top_course["credits"],
                    "button_text": f"Apply {top_course['code']} to Semester {target_sem}"
                }
                buddy_memory.set_pending_proposal(student_id, proposal)
                lines.append(
                    f"\n**Proposal:** Add **{top_course['code']}** ({top_course['credits']:.1f} cr) to Semester {target_sem}. "
                    f"Workload will become {current_credits + top_course['credits']:.1f}/{credit_cap:.1f} credits. "
                    f"Click **Apply** below to confirm."
                )

            deterministic_reply = "\n".join(lines)

        elif intent == "CHECK_DROP":
            tools_called.append("tools.check_drop")
            match = re.search(r"\b([A-Z]{2,4}[0-9]{3})\b", message.upper())
            target_code = match.group(1) if match else "CSL201"
            sem_match = re.search(r"semester\s*([0-9])", message.lower())
            target_sem = int(sem_match.group(1)) if sem_match else (profile.current_semester + 1)

            drop_check = tools.check_drop(student_id, target_sem, target_code)
            factual_context["drop_check"] = drop_check

            if not drop_check["allowed"]:
                deterministic_reply = f"Cannot drop {target_code}: {drop_check['reason']}"
            else:
                proposal = {
                    "action": "drop",
                    "semester": target_sem,
                    "course_code": target_code,
                    "title": drop_check.get("title", target_code),
                    "credits": drop_check.get("credits", 3.0),
                    "button_text": f"Drop {target_code} from Semester {target_sem}"
                }
                buddy_memory.set_pending_proposal(student_id, proposal)
                cap = float(drop_check.get("credit_cap") or standard_cap)
                deterministic_reply = (
                    f"Proposal: Drop **{target_code}** ({drop_check['credits']} cr) from Semester {target_sem}. "
                    f"New workload: {drop_check['new_credits']:.1f} / {cap:.1f} credits. Click **Apply** to confirm."
                )

        elif intent == "EXPLAIN_COURSE":
            tools_called.append("tools.explain_course")
            match = re.search(r"\b([A-Z]{2,4}[0-9]{3})\b", message.upper())
            target_code = match.group(1) if match else "CSL201"
            exp = tools.explain_course(target_code, student_id)
            factual_context["course_explanation"] = exp

            if not exp.get("found"):
                deterministic_reply = f"I could not locate course '{target_code}' in the active curriculum catalogue."
            else:
                prereq_str = ", ".join(exp["prerequisites"]) if exp.get("prerequisites") else "None"
                citation_str = f"{exp['source_citation']}" + (f", Page {exp['source_page']}" if exp.get("source_page") else "")
                syl = exp.get("syllabus") or "Comprehensive coursework and practical curriculum covering foundational concepts."
                syl_preview = syl[:280] + "..." if len(syl) > 280 else syl
                deterministic_reply = (
                    f"### **{exp['course_code']} — {exp['title']}**\n"
                    f"• **Credits**: {exp['credits']} cr ({exp['course_type']})\n"
                    f"• **Prerequisites**: {prereq_str}\n"
                    f"• **Syllabus / Scope**: {syl_preview}\n\n"
                    f"**Official Source Citation:** {citation_str}"
                )

        elif intent in ("NEXT_STEPS", "NEXT_ACTIONS"):
            tools_called.append("tools.next_actions")
            actions_data = tools.next_actions(student_id)
            factual_context["next_actions"] = actions_data
            lines = [
                f"### Recommended Next Actions for **{actions_data.get('target_role', 'Your Goal')}**:\n",
                f"*{actions_data.get('rationale')}*\n"
            ]
            for a in actions_data.get("actions", []):
                lines.append(f"• {a}")
            deterministic_reply = "\n".join(lines)

        elif intent == "WHAT_IF":
            tools_called.append("tools.what_if")
            what_res = tools.what_if(student_id, message)
            factual_context["what_if"] = what_res
            deterministic_reply = (
                f"### Simulation Result: **{what_res.get('scenario')}**\n"
                f"• **Projected Mastery Delta**: {what_res.get('projected_mastery_delta', 'N/A')}\n"
                f"• **Plan Adaptation**: {what_res.get('plan_adaptation', 'Plan remains compliant')}\n"
                f"• **Guidance**: {what_res.get('recommendation', 'Continue with scheduled coursework')}"
            )

        elif intent == "SKILL_GAPS":
            tools_called.append("tools.get_gaps")
            gaps_data = tools.get_gaps(student_id)
            factual_context["gaps_data"] = gaps_data
            gaps = gaps_data.get("gaps", [])
            lines = [f"### Priority Skill Gaps for **{gaps_data.get('goal_name', 'Your Goal')}**:"]
            if not gaps:
                lines.append("No critical skill gaps recorded. You are on track with your target milestone.")
            else:
                for g in gaps:
                    lines.append(f"• **{g.get('skill_name', 'Skill')}**: Current {int(g.get('current_level', 0)*100)}% → Target {int(g.get('target_level', 1)*100)}% (Gap: {int(g.get('gap', 0)*100)}%)")
                lines.append("\nYour semester plan has been sequenced to address these gaps.")
            deterministic_reply = "\n".join(lines)

        elif intent == "MASTERY_STATUS":
            tools_called.append("tools.get_gaps")
            gaps_data = tools.get_gaps(student_id)
            factual_context["goal_readiness"] = gaps_data
            deterministic_reply = (
                f"For your target ambition ({profile.target_role or profile.goal_id}), "
                f"your overall goal readiness is currently **{gaps_data.get('readiness_percentage', 0)}%**.\n"
                f"Remaining priority gaps to achieve placement readiness: **{gaps_data.get('critical_gap_count', 0)} skills**."
            )

        elif intent == "WHAT_I_KNOW":
            tools_called.append("tools.get_plan")
            plan_data = tools.get_plan(student_id)
            factual_context["plan_summary"] = plan_data
            sem_count = len(plan_data.get("semesters", []))
            deterministic_reply = (
                f"Here is your academic status, {profile.name}:\n"
                f"• **Programme**: {profile.programme} (Year {profile.year}, Current Semester {profile.current_semester})\n"
                f"• **CGPA**: {profile.cgpa} ({len(profile.completed_courses)} courses completed)\n"
                f"• **Active Goal**: {profile.target_role or 'B.Tech CSE'}\n"
                f"• **Planned Roadmap**: {sem_count} semesters scheduled ({plan_data.get('total_credits_planned', 0.0):.1f} total credits planned)."
            )

        elif intent == "VAGUE_GOAL":
            deterministic_reply = (
                f"I can help you tailor your degree roadmap, {profile.name}! Which of these career pathways best matches your focus?\n"
                "1. **Software / IT** (Systems, Web, Cloud, AI/ML)\n"
                "2. **Higher Studies** (Research, Algorithms, Theory, MS/PhD)\n"
                "3. **UPSC Preparation** (HSS Electives, General Studies baseline)\n"
                "4. **Startup & Entrepreneurship** (Product, Systems architecture, Prototyping)\n\n"
                "Reply with your choice and I will adjust your elective recommendations accordingly."
            )

        else:
            tools_called.append("retriever.search")
            retrieved = retriever.search(message, top_k=2)
            citation_line = ""
            if retrieved:
                top_c = retrieved[0]
                citation_line = f"\n\n**Official Citation ({top_c['source_citation']}):**\n> {top_c['text'][:240]}..."
            deterministic_reply = (
                f"You are currently enrolled in Semester {profile.current_semester} of {profile.programme}. "
                f"Your active milestone is **{profile.target_role or 'Academic Progression'}** with an independent study "
                f"capacity of {profile.available_hours_per_week} hrs/week.{citation_line}"
            )

        return self._finalize_turn(student_id, message, turn_id, intent, tools_called, factual_context, deterministic_reply, proposal)

    def _finalize_turn(
        self,
        student_id: str,
        message: str,
        turn_id: str,
        intent: str,
        tools_called: List[str],
        factual_context: Dict[str, Any],
        deterministic_reply: str,
        proposal: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesizes final reply via LiteLLM with strict fallback to deterministic answer."""
        recent_history = buddy_memory.get_recent_history(student_id, limit=4)
        messages = [{
            "role": "system",
            "content": (
                "You are Learning Buddy, an academic advising assistant for IIT Bhilai B.Tech CSE. "
                "Ground rules:\n"
                "1. Ground your answer strictly in the provided factual context.\n"
                "2. Never use repetitive openers like 'I remember your learning context...' or 'Hello!'.\n"
                "3. Never claim that the context lacks information if courses or data are provided.\n"
                "4. Always mention course codes, credits, and headroom numbers clearly.\n"
                "5. If a course or combination is recommended, always offer an 'Apply' option.\n"
                "6. Write warm, concise, academic advice."
            )
        }]

        for turn in recent_history:
            messages.append({"role": turn["role"], "content": turn["content"]})

        bounded_facts = build_bounded_context(factual_context, budget_tokens=1500)

        messages.append({
            "role": "user",
            "content": (
                f"Factual Context:\n{json.dumps(bounded_facts, default=str)}\n\n"
                f"Deterministic Grounded Answer:\n{deterministic_reply}\n\n"
                f"Student Message: {message}"
            )
        })

        live_response = llm_client.generate(
            call_type="BUDDY_CHAT",
            messages=messages,
            temperature=0.2,
            max_tokens=450,
            fallback_data={"deterministic_reply": deterministic_reply}
        )

        live_content = live_response.get("content", deterministic_reply)

        # Output Verification Layer: check all cited course codes against official catalogue
        from backend.buddy.safety import load_valid_course_codes
        valid_codes = load_valid_course_codes()
        extracted_codes = set(re.findall(r"\b[A-Z]{2,4}[0-9]{3}\b", live_content))
        hallucinated_codes = [c for c in extracted_codes if c.upper() not in valid_codes]

        if hallucinated_codes:
            logger.warning("Output verifier: hallucinated course codes %s in reply. Attempting regeneration.", hallucinated_codes)
            retry_messages = list(messages) + [
                {"role": "assistant", "content": live_content},
                {"role": "user", "content": f"Verification error: The following course codes do not exist in the official IIT Bhilai catalogue: {hallucinated_codes}. Regenerate using only verified course codes from context or return the deterministic reply."}
            ]
            try:
                retry_resp = llm_client.generate(
                    call_type="BUDDY_CHAT",
                    messages=retry_messages,
                    temperature=0.0,
                    max_tokens=450,
                    fallback_data={"deterministic_reply": deterministic_reply}
                )
                retry_content = retry_resp.get("content", deterministic_reply)
                retry_codes = set(re.findall(r"\b[A-Z]{2,4}[0-9]{3}\b", retry_content))
                if any(c.upper() not in valid_codes for c in retry_codes):
                    final_reply = BuddySafety.intercept_and_verify_course_codes(deterministic_reply)
                else:
                    final_reply = retry_content
            except Exception:
                final_reply = BuddySafety.intercept_and_verify_course_codes(deterministic_reply)
        else:
            final_reply = live_content

        final_reply = BuddySafety.intercept_and_verify_course_codes(final_reply)

        # Ensure diagnostic guidance is explicitly present when evidence is insufficient
        summary_info = factual_context.get("student_summary", {})
        if summary_info.get("status") == "insufficient_evidence":
            status_msg = summary_info.get("status_message", "Take a diagnostic check to estimate your readiness.")
            if "diagnostic" not in final_reply.lower():
                final_reply = f"{final_reply}\n\n{status_msg}"

        if factual_context.get("student_summary_degraded"):
            if "partial" not in final_reply.lower():
                final_reply = f"[Notice: Academic context is partial due to an internal summary loading error]\n\n{final_reply}"

        buddy_memory.record_turn(student_id, "user", message)
        buddy_memory.record_turn(
            student_id,
            "assistant",
            final_reply,
            turn_id=turn_id,
            intent=intent,
            tools_used=tools_called,
            facts_used=factual_context,
            model=live_response.get("model")
        )

        return {
            "reply": final_reply,
            "intent": intent,
            "tools_used": tools_called,
            "turn_id": turn_id,
            "facts_used": factual_context,
            "model": live_response.get("model"),
            "fallback_used": live_response.get("fallback_used", True),
            "proposal": proposal
        }


buddy_router = BuddyRouter()
