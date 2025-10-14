import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from typing import List

class UserCreate(BaseModel):
    full_name: str = Field(..., alias='fullName')
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    created_at: datetime

    # Pydantic v2 configuration for ORM mode
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    data: UserOut

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str
    
class RoomCreate(BaseModel):
    name: str
    is_private: bool = False

class RoomOut(BaseModel):
    id: uuid.UUID
    name: str
    unique_code: str
    owner_id: uuid.UUID
    is_private: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RoomResponse(BaseModel):
    data: RoomOut
    
    
class RoomUpdate(BaseModel):
    name: Optional[str] = None
    is_private: Optional[bool] = None

class RoomListResponse(BaseModel):
    data: List[RoomOut]
    
class SessionOut(BaseModel):
    session_id: uuid.UUID = Field(..., alias='id') # <-- Add the alias here
    room_id: uuid.UUID
    status: str
    actual_start_time: datetime

    class Config:
        from_attributes = True

class JoinResponse(BaseModel):
    message: str
    role: str
    
    
class ParticipantOut(BaseModel):
    user_id: uuid.UUID
    full_name: str
    role: str
    join_time: datetime
    is_sharing_screen: bool

    class Config:
        from_attributes = True

class SessionDetailOut(BaseModel):
    session_id: uuid.UUID
    status: str
    participants: List[ParticipantOut]
    recording_status: Optional[str] = None # <-- Add this
    recording_url: Optional[str] = None    # <-- And this

    class Config:
        from_attributes = True
        
        
class SessionSchedule(BaseModel):
    scheduled_start_time: datetime

class ScheduledSessionOut(BaseModel):
    session_id: uuid.UUID = Field(..., alias='id') # <-- Add alias here
    room_id: uuid.UUID
    status: str
    scheduled_start_time: datetime

    class Config:
        from_attributes = True
        
        
class Message(BaseModel):
    message: str
    
    
    

class SessionHistoryOut(BaseModel):
    id: uuid.UUID
    status: str
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    scheduled_start_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SessionHistoryResponse(BaseModel):
    data: List[SessionHistoryOut]
    

# In app/schemas.py
# ... keep existing schemas ...

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    user_full_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class MessageListResponse(BaseModel):
    data: List[MessageOut]
    

# In app/schemas.py


class ScheduledSessionListResponse(BaseModel):
    data: List[ScheduledSessionOut]



# In app/schemas.py

class RoomJoinInfo(BaseModel):
    room_id: uuid.UUID
    name: str
    is_private: bool
    live_session_id: Optional[uuid.UUID] = None