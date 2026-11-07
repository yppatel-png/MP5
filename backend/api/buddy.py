"""
Conversational Buddy API Endpoints.
Provides multi-turn dialogue, intent-routed advice, memory inspection, and safety verification.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from backend.buddy.router import buddy_router
from backend.buddy.memory import buddy_memory

router = APIRouter(prefix="/buddy", tags=["Conversational Buddy & Explainability"])

class ChatRequest(BaseModel):
    student_id: str = "BH-SW-001"
    message: str

class ChatResponse(BaseModel):
    reply: str
    intent: str
    tools_used: List[str]
    turn_id: Optional[Union[int, str]] = None
    facts_used: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    fallback_used: bool = True

@router.post("/chat", response_model=ChatResponse)
def send_chat_message(req: ChatRequest) -> Dict[str, Any]:
    """
    Handles student multi-turn conversational interaction.
    Executes safety checks, intent routing, dynamic domain tools, and grounded answer synthesis.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    return buddy_router.handle_message(
        student_id=req.student_id,
        message=req.message
    )

@router.get("/memory/{student_id}")
def get_student_memory(student_id: str) -> Dict[str, Any]:
    """
    Returns 'What I remember about you' persistent profile facts
    and recent working context dialogue history.
    """
    facts = buddy_memory.get_student_memory_facts(student_id)
    history = buddy_memory.get_recent_history(student_id, limit=20)
    return {
        "student_id": student_id,
        "memory_summary": facts,
        "recent_history": history
    }

@router.post("/clear-memory/{student_id}")
def clear_student_memory(student_id: str) -> Dict[str, Any]:
    """Clears conversational history for the student."""
    buddy_memory.clear_history(student_id)
    return {"status": "cleared", "student_id": student_id}
