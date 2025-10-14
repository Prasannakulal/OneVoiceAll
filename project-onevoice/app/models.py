import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Text, TIMESTAMP, func, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Enum

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)
    profile_picture_url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    
class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    unique_code = Column(String(50), unique=True, nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_private = Column(Boolean, default=False, nullable=False)
    passcode_hash = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    owner = relationship("User")
    
    
# class Session(Base):
#     __tablename__ = "sessions"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
#     status = Column(Enum('SCHEDULED', 'LIVE', 'ENDED', 'CANCELLED', name='session_status'), nullable=False)
#     scheduled_start_time = Column(TIMESTAMP(timezone=True), nullable=True)
#     actual_start_time = Column(TIMESTAMP(timezone=True), nullable=True)
#     actual_end_time = Column(TIMESTAMP(timezone=True), nullable=True)
#     created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
#     updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
#     recording_status = Column(Enum('RECORDING', 'STOPPED', 'AVAILABLE', name='recording_status'), nullable=True)
#     recording_url = Column(Text, nullable=True)

#     room = relationship("Room")
#     participants = relationship("SessionParticipant")
    
class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    status = Column(Enum('SCHEDULED', 'LIVE', 'ENDED', 'CANCELLED', name='session_status'), nullable=False)
    scheduled_start_time = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_start_time = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_end_time = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # --- THESE TWO COLUMNS WERE MISSING ---
    recording_status = Column(Enum('RECORDING', 'STOPPED', 'AVAILABLE', name='recording_status'), nullable=True)
    recording_url = Column(Text, nullable=True)
    # ------------------------------------

    room = relationship("Room")
    participants = relationship("SessionParticipant", back_populates="session")
    
    
class SessionParticipant(Base):
    __tablename__ = "session_participants"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role = Column(Enum('HOST', 'PARTICIPANT', 'MODERATOR', name='participant_role'), nullable=False)
    join_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    leave_time = Column(TIMESTAMP(timezone=True), nullable=True)
    is_sharing_screen = Column(Boolean, default=False, nullable=False)

    user = relationship("User")
    session = relationship("Session")
    

# In app/models.py


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    session = relationship("Session")
    user = relationship("User")