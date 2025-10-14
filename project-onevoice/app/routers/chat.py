import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import crud, schemas, security, database, models

router = APIRouter(
    prefix="/api/v1/sessions/{session_id}/chat",
    tags=["Chat"]
)

@router.post("/", response_model=schemas.MessageOut)
def send_chat_message(
    session_id: uuid.UUID,
    message: schemas.MessageCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Authorization: Check if user is an active participant
    participant = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not participant or participant.leave_time is not None:
        raise HTTPException(status_code=403, detail="User is not an active participant in this session")

    new_message = crud.create_chat_message(db, session_id=session_id, user_id=current_user.id, content=message.content)
    
    return {
        "id": new_message.id,
        "session_id": new_message.session_id,
        "user_id": new_message.user_id,
        "user_full_name": current_user.full_name,
        "content": new_message.content,
        "created_at": new_message.created_at
    }


@router.get("/", response_model=schemas.MessageListResponse)
def get_chat_history(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Authorization: Check if user is an active participant
    participant = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not participant:
        raise HTTPException(status_code=403, detail="User is not a participant in this session")

    messages = crud.get_chat_messages_for_session(db, session_id=session_id)
    
    # Format the response
    messages_out = [
        {
            "id": msg.id,
            "session_id": msg.session_id,
            "user_id": msg.user_id,
            "user_full_name": msg.user.full_name,
            "content": msg.content,
            "created_at": msg.created_at
        }
        for msg in messages
    ]
    return {"data": messages_out}