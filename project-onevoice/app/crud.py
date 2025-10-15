from sqlalchemy.orm import Session
from . import models, schemas, security
import uuid
import shortuuid
from datetime import datetime,timezone

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.hash_password(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_room_for_user(db: Session, room: schemas.RoomCreate, user_id: uuid.UUID):
    unique_code = shortuuid.random(length=8)
    db_room = models.Room(
        name=room.name,
        is_private=room.is_private,
        owner_id=user_id,
        unique_code=unique_code
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_room_by_id(db: Session, room_id: uuid.UUID):
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def get_rooms_for_user(db: Session, user_id: uuid.UUID):
    return db.query(models.Room).filter(models.Room.owner_id == user_id).all()

def delete_room(db: Session, room: models.Room):
    db.delete(room)
    db.commit()
    

def start_session_in_room(db: Session, room_id: uuid.UUID, user_id: uuid.UUID):
    # Create the session
    db_session = models.Session(
        room_id=room_id,
        status='LIVE',
        actual_start_time=datetime.now(timezone.utc) # <-- 2. Correctly use timezone.utc
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    # Automatically add the host as the first participant
    host_participant = models.SessionParticipant(
        session_id=db_session.id,
        user_id=user_id,
        role='HOST'
    )
    db.add(host_participant)
    db.commit()
    
    return db_session

def add_participant_to_session(db: Session, session_id: uuid.UUID, user_id: uuid.UUID):
    # Check if user is already in the session
    db_participant = db.query(models.SessionParticipant).filter(
        models.SessionParticipant.session_id == session_id,
        models.SessionParticipant.user_id == user_id
    ).first()

    if db_participant:
        return db_participant # Or handle re-joining logic

    # ✅ Check if this is the first participant (should be HOST)
    existing_participants = db.query(models.SessionParticipant).filter(
        models.SessionParticipant.session_id == session_id,
        models.SessionParticipant.leave_time.is_(None)  # Only active participants
    ).count()
    
    # ✅ First participant becomes HOST, others become PARTICIPANT
    role = 'HOST' if existing_participants == 0 else 'PARTICIPANT'

    new_participant = models.SessionParticipant(
        session_id=session_id,
        user_id=user_id,
        role=role
    )
    db.add(new_participant)
    db.commit()
    db.refresh(new_participant)
    return new_participant


def get_session_by_id(db: Session, session_id: uuid.UUID):
    return db.query(models.Session).filter(models.Session.id == session_id).first()

def get_participants_in_session(db: Session, session_id: uuid.UUID):
    return db.query(models.SessionParticipant).filter(models.SessionParticipant.session_id == session_id).all()

def get_participant(db: Session, session_id: uuid.UUID, user_id: uuid.UUID):
    return db.query(models.SessionParticipant).filter(
        models.SessionParticipant.session_id == session_id,
        models.SessionParticipant.user_id == user_id
    ).first()

def remove_participant_from_session(db: Session, session_id: uuid.UUID, user_id: uuid.UUID):
    participant = get_participant(db, session_id, user_id)
    if participant:
        participant.leave_time = datetime.now(timezone.utc)
        db.add(participant)
        db.commit()
    return participant

def end_session(db: Session, session: models.Session):
    session.status = 'ENDED'
    session.actual_end_time = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def schedule_session_in_room(db: Session, room_id: uuid.UUID, user_id: uuid.UUID, start_time: datetime):
    db_session = models.Session(
        room_id=room_id,
        status='SCHEDULED',
        scheduled_start_time=start_time
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    # Add the user who scheduled the session as the HOST
    host_participant = models.SessionParticipant(
        session_id=db_session.id,
        user_id=user_id,
        role='HOST'
    )
    db.add(host_participant)
    db.commit()

    return db_session


def cancel_session(db: Session, session: models.Session):
    session.status = 'CANCELLED'
    db.add(session)
    db.commit()
    db.refresh(session)
    return session



def get_sessions_for_room(db: Session, room_id: uuid.UUID):
    return db.query(models.Session).filter(models.Session.room_id == room_id).order_by(models.Session.created_at.desc()).all()


# In app/crud.py

def start_screen_share(db: Session, session_id: uuid.UUID, user_id: uuid.UUID):
    # First, ensure no one else is sharing in the same session
    db.query(models.SessionParticipant).\
        filter(models.SessionParticipant.session_id == session_id).\
        update({models.SessionParticipant.is_sharing_screen: False})
    
    # Now, set the current user as the sharer
    participant = get_participant(db, session_id=session_id, user_id=user_id)
    if participant:
        participant.is_sharing_screen = True
        db.add(participant)
        db.commit()
    return participant

def stop_screen_share(db: Session, session_id: uuid.UUID, user_id: uuid.UUID):
    participant = get_participant(db, session_id=session_id, user_id=user_id)
    if participant:
        participant.is_sharing_screen = False
        db.add(participant)
        db.commit()
    return participant


def create_chat_message(db: Session, session_id: uuid.UUID, user_id: uuid.UUID, content: str):
    db_message = models.ChatMessage(
        session_id=session_id,
        user_id=user_id,
        content=content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_messages_for_session(db: Session, session_id: uuid.UUID):
    # Joining with User to get the user's name
    return db.query(models.ChatMessage).join(models.User).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.created_at).all()


# In app/crud.py

def start_recording(db: Session, session: models.Session):
    session.recording_status = 'RECORDING'
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def stop_recording(db: Session, session: models.Session, url: str):
    session.recording_status = 'AVAILABLE'
    session.recording_url = url
    db.add(session)
    db.commit()
    db.refresh(session)
    return session



# In app/crud.py

def update_participant_role(db: Session, participant: models.SessionParticipant, new_role: str):
    participant.role = new_role
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant



# In app/crud.py

def get_scheduled_sessions_for_user(db: Session, user_id: uuid.UUID):
    # Find all session_participant entries where the user is the host
    host_entries = db.query(models.SessionParticipant).filter(
        models.SessionParticipant.user_id == user_id,
        models.SessionParticipant.role == 'HOST'
    ).all()
    
    # Get the session IDs from those entries
    session_ids = [entry.session_id for entry in host_entries]

    # Find all sessions that match those IDs and are also scheduled
    return db.query(models.Session).filter(
        models.Session.id.in_(session_ids),
        models.Session.status == 'SCHEDULED'
    ).order_by(models.Session.scheduled_start_time).all()
    
    
# In app/crud.py

def get_room_by_unique_code(db: Session, unique_code: str):
    return db.query(models.Room).filter(models.Room.unique_code == unique_code).first()

def get_user_by_id(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()

# In app/crud.py

def create_instant_session(db: Session, user_id: uuid.UUID):
    # 1. Create a default, non-persistent room for the user
    default_room_name = f"{get_user_by_id(db, user_id).full_name}'s Instant Meeting"
    instant_room = create_room_for_user(
        db=db,
        room=schemas.RoomCreate(name=default_room_name, is_private=True), # Instant rooms are private by default
        user_id=user_id
    )

    # 2. Immediately start a session in that new room
    instant_session = start_session_in_room(
        db=db,
        room_id=instant_room.id,
        user_id=user_id
    )
    
    return instant_session