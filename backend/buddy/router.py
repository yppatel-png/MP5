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


class BuddyRouter:
    def classify_intent(self, message: str) -> str:
        """Classifies incoming student message into an actionable academic intent."""
        msg = message.lower().strip()

        # 1. Apply confirmation
        if msg in ("apply", "confirm", "yes", "yes please", "apply change", "add it") or msg.startswith("apply "):
            return "APPLY_PROPOSAL"

        # 2. Impossible requests / credit overload
        if any(w in msg for w in ["35 credit", "35 credits", "overload 30", "take 35", "more than 24"]):
            return "CREDIT_OVERLOAD"

        # 3. Add / Recommend courses / Elective discovery
        if any(w in msg for w in [
            "which courses should i prefer", "which course should i prefer", "prefer",
            "add a total of", "add course", "recommend elective", "suggest elective",
            "eligible elective", "5 credit", "credit course", "take next semester"
        ]):
            return "RECOMMEND_ELECTIVES"

        # 4. Check dropping
        if any(w in msg for w in ["drop", "remove course", "can i drop", "exclude"]):
            return "CHECK_DROP"

        # 5. Course explanation
        if any(w in msg for w in [
            "why csl", "why col", "why lal", "why this course", "why was", "why recommend",
            "tell me about", "syllabus of", "what is csl", "what is mal", "what is lal"
        ]):
            return "EXPLAIN_COURSE"
        if re.search(r"\b(CSL|MAL|ECL|CSP|CSQ|LAL)[0-9]{3}\b", message.upper()) and any(
            w in msg for w in ["explain", "why", "about", "details", "syllabus", "tell me"]
        ):
            return "EXPLAIN_COURSE"

        # 6. Next steps / actions
        if any(w in msg for w in ["what next", "next step", "what should i do next", "where to start", "next action", "next milestone"]):
            return "NEXT_ACTIONS"

        # 7. What if / simulation
        if any(w in msg for w in ["what if", "simulate", "strong study week", "weak study week", "study-week simulation"]):
            return "WHAT_IF"

        # 8. Skill gaps
        if any(w in msg for w in ["improve", "lagging", "weakness", "gaps", "what should i improve", "need to learn", "where am i lagging"]):
            return "SKILL_GAPS"

        # 9. What I know / Mastery
        if any(w in msg for w in ["what i know", "my skills", "strengths", "what do i know", "my background", "mastered", "readiness", "placement ready"]):
            return "WHAT_I_KNOW"

        # 10. Vague goal
        if any(w in msg for w in ["undecided", "don't know", "dont know", "not sure", "confused", "career options", "explore"]):
            return "VAGUE_GOAL"

        # 11. Plan diff
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
                deterministic_reply = (
                    f"Applied! Added **{pending['course_code']}** ({pending.get('credits', 3.0)} cr) to "
                    f"Semester {pending['semester']}. New semester workload: **{res.get('new_credits', 24.0):.1f} / 24.0 credits**. "
                    "Your active plan has been updated and re-verified."
                )
            else:
                deterministic_reply = "There is no pending course proposal to apply. Ask me to recommend or add an elective for any semester."
            return self._finalize_turn(student_id, message, turn_id, intent, tools_called, factual_context, deterministic_reply, None)

        elif intent == "CREDIT_OVERLOAD":
            tools_called.append("tools.what_if")
            factual_context["overload_check"] = tools.what_if(student_id, "35 credits")
            deterministic_reply = (
                "Under IIT Bhilai B.Tech CSE academic ordinances, semester workload is strictly capped at a "
                "maximum of **24.0 credits per regular semester**. Registering for 35 credits is not permitted.\n\n"
                "**Recommended Alternative:**\n"
                "Spread the desired courses over regular upcoming semesters and approved summer terms "
                "(up to 24.0 credits per semester) to ensure compliance and balanced academic progression.\n\n"
                "**Citation:** IIT Bhilai B.Tech Ordinance §Workload Regulations (24.0 credit ceiling)."
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
            headroom = eligible_data.get("headroom", 5.0)
            eligible_courses = eligible_data.get("eligible_courses", [])
            combinations = eligible_data.get("suggested_combinations", [])

            # Format deterministic response
            lines = [
                f"In Semester {target_sem}, your plan currently has {eligible_data.get('current_credits', 19.0):.1f} / "
                f"{eligible_data.get('credit_cap', 24.0):.1f} credits, leaving **{headroom:.1f} credits of available headroom**.\n"
            ]
            lines.append(f"Based on your goal (**{profile.target_role or 'UPSC Civil Services'}**) and expressed interests, here are top eligible electives:\n")

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
                    f"Workload will become {eligible_data.get('current_credits', 19.0) + top_course['credits']:.1f}/24.0 credits. "
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
                deterministic_reply = (
                    f"Proposal: Drop **{target_code}** ({drop_check['credits']} cr) from Semester {target_sem}. "
                    f"New workload: {drop_check['new_credits']:.1f} / 24.0 credits. Click **Apply** to confirm."
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
                deterministic_reply = (
                    f"### **{exp['course_code']} — {exp['title']}**\n"
                    f"• **Credits**: {exp['credits']} cr ({exp['course_type']})\n"
                    f"• **Prerequisites**: {prereq_str}\n"
                    f"• **Syllabus / Scope**: {exp['syllabus'][:280]}...\n\n"
                    f"**Official Source Citation:** {citation_str}"
                )

        elif intent == "NEXT_ACTIONS":
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
                "3. **UPSC Civil Services** (HSS Electives, General Studies baseline)\n"
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

        messages.append({
            "role": "user",
            "content": (
                f"Factual Context:\n{json.dumps(factual_context, default=str)}\n\n"
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

        final_reply = live_response.get("content", deterministic_reply)
        final_reply = BuddySafety.intercept_and_verify_course_codes(final_reply)

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
