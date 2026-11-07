"""
Multi-Layer Conversational Memory Engine.
Manages:
1. Working context (active turns).
2. Rolling session summary (compact contextual anchor).
3. Persistent DB memory (stored in chat_memory table, surviving server restarts).
4. 'What I remember about you' profile memory synthesis.
"""

import json
from typing import List, Dict, Any, Optional
from backend.db.database import get_db_cursor
from backend.student.model import StudentStore

class BuddyMemory:
    @staticmethod
    def record_turn(
        student_id: str,
        role: str,
        content: str,
        turn_id: Optional[str] = None,
        tools_used: Optional[List[str]] = None,
        intent: Optional[str] = None,
        **kwargs
    ) -> int:
        return BuddyMemory.save_turn(
            student_id, role, content, intent=intent, tools_called=tools_used, **kwargs
        )

    @staticmethod
    def save_turn(
        student_id: str,
        role: str,  # 'user' or 'assistant'
        content: str,
        intent: Optional[str] = None,
        tools_called: Optional[List[str]] = None,
        **kwargs
    ) -> int:
        """Persists a conversation turn into SQLite chat_memory."""
        with get_db_cursor() as cur:
            cur.execute("""
            INSERT INTO chat_memory (student_id, role, content, intent, tools_called_json)
            VALUES (?, ?, ?, ?, ?);
            """, (
                student_id,
                role,
                content,
                intent,
                json.dumps(tools_called or [])
            ))
            return cur.lastrowid

    @staticmethod
    def get_recent_history(student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent conversation turns for working context."""
        with get_db_cursor() as cur:
            cur.execute("""
            SELECT id, role, content, intent, tools_called_json, timestamp
            FROM chat_memory
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT ?;
            """, (student_id, limit))
            rows = cur.fetchall()

        history = []
        for r in reversed(rows):
            history.append({
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "intent": r["intent"],
                "tools_called": json.loads(r["tools_called_json"]) if r["tools_called_json"] else [],
                "timestamp": str(r["timestamp"])
            })
        return history

    @staticmethod
    def get_student_memory_facts(student_id: str) -> Dict[str, Any]:
        """
        Synthesizes 'What I remember about you' by combining
        persistent profile attributes with historical dialogue context.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"known": False, "summary": f"No profile record found for {student_id}."}

        # Query past intents to identify discussed topics
        with get_db_cursor() as cur:
            cur.execute("""
            SELECT DISTINCT intent FROM chat_memory
            WHERE student_id = ? AND intent IS NOT NULL;
            """, (student_id,))
            intents = [r["intent"] for r in cur.fetchall()]

        completed_codes = [c.course_code for c in profile.completed_courses]
        top_interests = profile.interests[:3]
        prog_name = "Computer Science and Engineering" if "cse" in profile.programme.lower() else profile.programme

        facts = [
            f"Programme: {profile.programme} ({prog_name}, Year {profile.year}, Current Semester {profile.current_semester})",
            f"Target Career Goal: {profile.goal_id.replace('goal_', '').title()}",
            f"Academic Standing: CGPA {profile.cgpa} with {len(completed_codes)} accredited courses completed ({', '.join(completed_codes[:4])}...)",
            f"Weekly Independent Study Budget: {profile.available_hours_per_week} hours/week",
            f"Expressed Interests: {', '.join(top_interests) if top_interests else 'Software Systems'}"
        ]

        if "EXPLAIN_COURSE" in intents:
            facts.append("Previously asked for course selection explanations.")
        if "OVERRIDE_COURSE" in intents:
            facts.append("Has explored course overrides and trade-off comparisons.")

        summary_text = (
            f"You are {profile.name}, a Year {profile.year} student in {profile.programme} with a {profile.cgpa} CGPA. "
            f"Your active milestone is preparing for {profile.goal_id.replace('goal_', '').replace('_', ' ').title()} roles, "
            f"with an independent study capacity of {profile.available_hours_per_week} hrs/week."
        )

        return {
            "known": True,
            "student_name": profile.name,
            "programme": profile.programme,
            "cgpa": profile.cgpa,
            "goal": profile.goal_id,
            "available_hours_per_week": profile.available_hours_per_week,
            "completed_courses": completed_codes,
            "facts": facts,
            "summary": summary_text
        }

    @staticmethod
    def clear_history(student_id: str) -> None:
        """Clears memory for a student (used for test isolation and resets)."""
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM chat_memory WHERE student_id = ?;", (student_id,))

buddy_memory = BuddyMemory()
