from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.db.models.ai_chat_message import AIChatMessage
from app.services.ai_chatbot import answer_question

router = APIRouter()


class ChatQuery(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    messages: List[MessageOut]


@router.post("/ai-chat", response_model=ChatResponse, summary="Ask the AI chatbot a question")
def ai_chat(
    query: ChatQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ask a question about restaurants, menus, cuisines, locations, etc."""

    # Save the user's message
    user_msg = AIChatMessage(
        user_id=current_user.id,
        role="user",
        content=query.message,
    )
    db.add(user_msg)
    # Flush so the message is available to subsequent queries (autoflush is False)
    db.flush()

    # Get recent chat history for context — newest messages first, then reverse
    # so the last message is always the current user's question
    recent_history = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.user_id == current_user.id)
        .order_by(AIChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    recent_history.reverse()

    reply = answer_question(db, history=recent_history)

    # Save the assistant's reply
    assistant_msg = AIChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=reply,
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(reply=reply)


@router.get("/ai-chat/history", response_model=HistoryResponse, summary="Get the current user's AI chat history")
def get_ai_chat_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all AI chat messages for the current user, ordered by creation time."""
    messages = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.user_id == current_user.id)
        .order_by(AIChatMessage.created_at.asc())
        .all()
    )

    return HistoryResponse(
        messages=[
            MessageOut(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat() if msg.created_at else "",
            )
            for msg in messages
        ]
    )


@router.delete("/ai-chat/history", status_code=204, summary="Clear the current user's AI chat history")
def clear_ai_chat_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete all AI chat messages for the current user."""
    db.query(AIChatMessage).filter(AIChatMessage.user_id == current_user.id).delete()
    db.commit()


@router.delete("/ai-chat/messages/{message_id}", status_code=204, summary="Delete a message and all messages after it")
def delete_ai_chat_message(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a specific message and all messages created after it.
    Used when a user edits a previous message — the old conversation branch is removed.
    """
    import uuid

    try:
        msg_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    target = db.query(AIChatMessage).filter(
        AIChatMessage.id == msg_uuid,
        AIChatMessage.user_id == current_user.id,
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="Message not found")

    # Delete this message and all later messages for this user
    db.query(AIChatMessage).filter(
        AIChatMessage.user_id == current_user.id,
        AIChatMessage.created_at >= target.created_at,
    ).delete()
    db.commit()
