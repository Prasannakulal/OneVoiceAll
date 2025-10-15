import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
import json
from sqlalchemy.orm import Session
from .. import crud, schemas, security, database, models
from ..signaling import manager

router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["Sessions"]
)

@router.post("/{session_id}/participants", response_model=schemas.JoinResponse)
def join_session(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # --- ADD THIS STATUS CHECK ---
    session = crud.get_session_by_id(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != 'LIVE':
        raise HTTPException(status_code=400, detail="This session is not live and cannot be joined.")
    # --- END OF STATUS CHECK ---

    crud.add_participant_to_session(db=db, session_id=session_id, user_id=current_user.id)
    return {"message": "Successfully joined the session.", "role": "PARTICIPANT"}

@router.get("/{session_id}", response_model=schemas.SessionDetailOut)
def get_session_details(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    session = crud.get_session_by_id(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    participants_db = crud.get_participants_in_session(db, session_id=session_id)
    active_participants = [p for p in participants_db if p.leave_time is None]
    
    participants_out = []
    for p in active_participants:
        participants_out.append({
            "user_id": p.user.id,
            "full_name": p.user.full_name,
            "role": p.role,
            "join_time": p.join_time,
            "is_sharing_screen": p.is_sharing_screen
        })

    # FIX: Include recording_status, recording_url, and room_id in the response
    return {
        "session_id": session.id, 
        "status": session.status, 
        "participants": participants_out,
        "recording_status": session.recording_status,
        "recording_url": session.recording_url,
        "room_id": session.room_id
    }

@router.delete("/{session_id}/participants/me", status_code=status.HTTP_200_OK)
def leave_session(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    crud.remove_participant_from_session(db, session_id=session_id, user_id=current_user.id)
    return {"message": "You have left the meeting"}

@router.post("/{session_id}/end", response_model=schemas.Message)
def end_session_for_all(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    session = crud.get_session_by_id(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    host = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not host or host.role != 'HOST':
        raise HTTPException(status_code=403, detail="Only the host can end the session")

    crud.end_session(db, session=session)
    return {"message": "Session has been ended."}

# --- ADD THIS NEW ENDPOINT ---
@router.post("/{session_id}/cancel", response_model=schemas.Message)
def cancel_session(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    session = crud.get_session_by_id(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Authorization check: only the host can cancel
    host = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not host or host.role != 'HOST':
        raise HTTPException(status_code=403, detail="Only the host can cancel the session")
    
    if session.status != 'SCHEDULED':
        raise HTTPException(status_code=400, detail="Only scheduled sessions can be cancelled")

    crud.cancel_session(db, session=session)
    return {"message": "Session has been cancelled."}


# In app/routers/sessions.py

# ... (keep existing router and endpoints) ...

@router.post("/{session_id}/screenshare/start", status_code=status.HTTP_200_OK)
def start_screenshare(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    participant = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not participant or participant.leave_time is not None:
        raise HTTPException(status_code=403, detail="User is not an active participant in this session")

    crud.start_screen_share(db, session_id=session_id, user_id=current_user.id)

    # Broadcast to everyone in the room over WebSocket
    session = crud.get_session_by_id(db, session_id=session_id)
    if session:
        payload = json.dumps({
            "type": "screenshare-started",
            "session_id": str(session_id),
            "room_id": str(session.room_id),
            "user_id": str(current_user.id),
            "full_name": current_user.full_name
        })
        # Fire-and-forget broadcast; no await in sync route
        try:
            import anyio
            anyio.from_thread.run(manager.broadcast, payload, str(session.room_id), None)
        except Exception:
            pass

    return {"message": "Screen share started successfully"}

@router.post("/{session_id}/screenshare/stop", status_code=status.HTTP_200_OK)
def stop_screenshare(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    participant = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not participant or not participant.is_sharing_screen:
        raise HTTPException(status_code=403, detail="User is not currently sharing screen")

    crud.stop_screen_share(db, session_id=session_id, user_id=current_user.id)

    # Broadcast to everyone in the room over WebSocket
    session = crud.get_session_by_id(db, session_id=session_id)
    if session:
        payload = json.dumps({
            "type": "screenshare-stopped",
            "session_id": str(session_id),
            "room_id": str(session.room_id),
            "user_id": str(current_user.id),
            "full_name": current_user.full_name
        })
        try:
            import anyio
            anyio.from_thread.run(manager.broadcast, payload, str(session.room_id), None)
        except Exception:
            pass

    return {"message": "Screen share stopped successfully"}


# In app/routers/sessions.py
# ... (keep existing router and other endpoints) ...

@router.post("/{session_id}/recording/start", response_model=schemas.Message)
def start_session_recording(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    session = crud.get_session_by_id(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Authorization: Only the host can start a recording
    host = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not host or host.role != 'HOST':
        raise HTTPException(status_code=403, detail="Only the host can start a recording")
    
    crud.start_recording(db, session=session)
    return {"message": "Session recording started"}

@router.post("/{session_id}/recording/stop", response_model=schemas.Message)
def stop_session_recording(
    session_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    session = crud.get_session_by_id(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Authorization: Only the host can stop a recording
    host = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not host or host.role != 'HOST':
        raise HTTPException(status_code=403, detail="Only the host can stop a recording")
    
    # In a real system, you'd get the URL from the recording service (BE2)
    # For now, we'll use a placeholder.
    placeholder_url = f"https://recordings.example.com/{session.id}.mp4"
    crud.stop_recording(db, session=session, url=placeholder_url)
    return {"message": "Session recording stopped and is available"}


# In app/routers/sessions.py

@router.post("/{session_id}/participants/{user_id_to_promote}/promote", response_model=schemas.Message)
def promote_participant(
    session_id: uuid.UUID,
    user_id_to_promote: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Authorization check: Ensure the current user is the HOST of this session
    requester_participant = crud.get_participant(db, session_id=session_id, user_id=current_user.id)
    if not requester_participant or requester_participant.role != 'HOST':
        raise HTTPException(status_code=403, detail="Only the host can promote participants")

    # Get the participant to be promoted
    participant_to_promote = crud.get_participant(db, session_id=session_id, user_id=user_id_to_promote)
    if not participant_to_promote:
        raise HTTPException(status_code=404, detail="Participant to promote not found in this session")

    # Update the role
    crud.update_participant_role(db, participant=participant_to_promote, new_role='MODERATOR')
    
    return {"message": "Participant has been promoted to Moderator"}



# In app/routers/sessions.py

# ... (keep existing router and endpoints) ...

@router.post("/start", response_model=schemas.SessionOut)
def start_instant_session(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Creates an instant meeting by creating a default room and starting a session in it.
    """
    session = crud.create_instant_session(db=db, user_id=current_user.id)
    return session

