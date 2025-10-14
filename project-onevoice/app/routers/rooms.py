import shortuuid
import uuid # <--- ADD THIS LINE
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import crud, schemas, security, database, models
from datetime import datetime

router = APIRouter(
    prefix="/api/v1/rooms",
    tags=["Rooms"]
)

@router.post("/", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    room: schemas.RoomCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    new_room = crud.create_room_for_user(db=db, room=room, user_id=current_user.id)
    return {"data": new_room}

@router.get("/", response_model=schemas.RoomListResponse)
def list_my_rooms(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    rooms = crud.get_rooms_for_user(db=db, user_id=current_user.id)
    return {"data": rooms}

@router.put("/{room_id}", response_model=schemas.RoomResponse)
def update_room(
    room_id: uuid.UUID,
    room_update: schemas.RoomUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    room_to_update = crud.get_room_by_id(db=db, room_id=room_id)
    if not room_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    
    # Authorization check: Ensure the user owns the room
    if room_to_update.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this room")

    # Update the model with new data
    update_data = room_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room_to_update, key, value)
    
    db.add(room_to_update)
    db.commit()
    db.refresh(room_to_update)
    return {"data": room_to_update}

@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
def delete_room(
    room_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    room_to_delete = crud.get_room_by_id(db=db, room_id=room_id)
    if not room_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # Authorization check: Ensure the user owns the room
    if room_to_delete.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this room")

    crud.delete_room(db=db, room=room_to_delete)
    return {"message": "Room deleted successfully"}



@router.post("/{room_id}/sessions/start", response_model=schemas.SessionOut)
def start_new_session(
    room_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    room = crud.get_room_by_id(db=db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the room owner can start a session")

    session = crud.start_session_in_room(db=db, room_id=room_id, user_id=current_user.id)
    return {"session_id": session.id, "room_id": session.room_id, "status": session.status, "actual_start_time": session.actual_start_time}



@router.post("/{room_id}/sessions/schedule", response_model=schemas.ScheduledSessionOut)
def schedule_session(
    room_id: uuid.UUID,
    schedule: schemas.SessionSchedule,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    room = crud.get_room_by_id(db=db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Authorization: Only the room owner can schedule a session
    if room.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the room owner can schedule a session")
    
    session = crud.schedule_session_in_room(db=db, room_id=room_id, user_id=current_user.id, start_time=schedule.scheduled_start_time)
    return session

@router.get("/{room_id}/sessions", response_model=schemas.SessionHistoryResponse)
def get_room_session_history(
    room_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    room = crud.get_room_by_id(db=db, room_id=room_id)
    if not room or room.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Room not found or not owned by user")

    sessions = crud.get_sessions_for_room(db=db, room_id=room_id)
    return {"data": sessions}


# In app/routers/rooms.py

@router.get("/join/{unique_code}", response_model=schemas.RoomJoinInfo)
def get_room_join_info(
    unique_code: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user) # Still require login to get info
):
    room = crud.get_room_by_unique_code(db=db, unique_code=unique_code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Find if there is a live session currently in this room
    live_session = db.query(models.Session).filter(
        models.Session.room_id == room.id,
        models.Session.status == 'LIVE'
    ).first()

    return {
        "room_id": room.id,
        "name": room.name,
        "is_private": room.is_private,
        "live_session_id": live_session.id if live_session else None
    }