from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.services.ai_chatbot import answer_question

router = APIRouter()


class ChatQuery(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/ai-chat", response_model=ChatResponse, summary="Ask the AI chatbot a question")
def ai_chat(
    query: ChatQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ask a question about restaurants, menus, cuisines, locations, etc."""
    reply = answer_question(db, query.message)
    return ChatResponse(reply=reply)
