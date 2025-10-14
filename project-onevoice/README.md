# OneVoice API Documentation

## Overview

The **OneVoice Real-Time Translation Platform** provides a scalable backend for managing users, rooms, sessions, participants, and real-time interactions such as chat, screen sharing, and recording.  
This documentation describes the database schema, API endpoints, architectural principles, and testing procedures that power the OneVoice platform.

---

## 1. System Overview

### Purpose
The OneVoice backend enables secure, real-time multilingual meetings with persistent rooms, scheduled sessions, chat functionality, and advanced participant controls. It supports full lifecycle management — from user authentication to meeting recording.

### Core Technologies
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT (Access + Refresh Tokens)
- **Password Hashing:** Argon2
- **Architecture:** MVC-inspired, modular design (Models, Schemas, CRUD, Routers)

---

## 2. Database Schema

### Schema Overview
The database supports the OneVoice platform’s user and meeting lifecycle.  
It uses UUIDs for distributed scalability and timestamps with timezone awareness (`TIMESTAMPTZ`).

---

### Entity-Relationship Diagram (ERD)

```
[users] 1--* [rooms] 1--* [sessions] 1--* [session_participants] *--1 [users]
```

- A user can own many rooms.  
- A room can have many sessions.  
- A session can have many participants.  
- A user can participate in multiple sessions.

---

### Tables

#### **users**
Stores account information for each registered user.

| Column | Type | Constraints | Description |
|--------|------|-------------|--------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique user ID |
| full_name | VARCHAR(255) | NOT NULL | User's display name |
| email | VARCHAR(255) | NOT NULL, UNIQUE | Login email |
| password_hash | TEXT | NOT NULL | Argon2 hashed password |
| profile_picture_url | TEXT | NULLABLE | Profile picture URL |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

---

#### **rooms**
Stores data about persistent meeting rooms.

| Column | Type | Constraints | Description |
|--------|------|-------------|--------------|
| id | UUID | PRIMARY KEY | Room ID |
| name | VARCHAR(255) | NOT NULL | Room title |
| unique_code | VARCHAR(50) | NOT NULL, UNIQUE | Human-readable join code |
| owner_id | UUID | FOREIGN KEY → users(id) | Room owner |
| is_private | BOOLEAN | DEFAULT FALSE | If passcode is required |
| passcode_hash | TEXT | NULLABLE | Hashed passcode |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

---

#### **sessions**
Represents each individual meeting instance within a room.

| Column | Type | Constraints | Description |
|--------|------|-------------|--------------|
| id | UUID | PRIMARY KEY | Session ID |
| room_id | UUID | FOREIGN KEY → rooms(id) | Linked room |
| status | ENUM | NOT NULL | `SCHEDULED`, `LIVE`, `ENDED`, `CANCELLED` |
| scheduled_start_time | TIMESTAMPTZ | NULLABLE | Planned start time |
| actual_start_time | TIMESTAMPTZ | NULLABLE | Actual start time |
| actual_end_time | TIMESTAMPTZ | NULLABLE | Actual end time |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

---

#### **session_participants**
Join table linking users to sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|--------------|
| session_id | UUID | COMPOSITE PK, FK → sessions(id) | Session reference |
| user_id | UUID | COMPOSITE PK, FK → users(id) | Participant reference |
| role | ENUM | NOT NULL | `HOST`, `PARTICIPANT`, `MODERATOR` |
| join_time | TIMESTAMPTZ | DEFAULT NOW() | When user joined |
| leave_time | TIMESTAMPTZ | NULLABLE | When user left |
| is_sharing_screen | BOOLEAN | DEFAULT FALSE | Screen sharing flag |

---

## 3. API Endpoints

### Authentication

#### `POST /api/v1/auth/register`
Creates a new user account.

**Request**
```json
{
  "fullName": "Sid S",
  "email": "sid.s@example.com",
  "password": "strong-password-123"
}
```

**Response**
```json
{
  "data": {
    "id": "a1b2c3d4-...",
    "fullName": "Sid S",
    "email": "sid.s@example.com",
    "createdAt": "2025-09-16T12:40:00Z"
  }
}
```

---

#### `POST /api/v1/auth/login`
Authenticates a user and returns tokens.

**Response**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

---

#### `POST /api/v1/auth/refresh`
Generates a new access and refresh token pair.

---

### Room Management

| Method | Endpoint | Description |
|--------|-----------|--------------|
| POST | `/api/v1/rooms` | Create a new room |
| GET | `/api/v1/rooms` | List rooms owned by user |
| PUT | `/api/v1/rooms/{roomId}` | Update a room |
| DELETE | `/api/v1/rooms/{roomId}` | Delete a room |

All endpoints require authentication.

---

## 4. Session & Participant Management

| Method | Endpoint | Description |
|--------|-----------|--------------|
| POST | `/api/v1/rooms/{roomId}/sessions/start` | Start a live session |
| POST | `/api/v1/rooms/{roomId}/sessions/schedule` | Schedule a future session |
| POST | `/api/v1/sessions/{sessionId}/cancel` | Cancel a scheduled session |
| POST | `/api/v1/sessions/{sessionId}/participants` | Join a session (LIVE only) |
| DELETE | `/api/v1/sessions/{sessionId}/participants/me` | Leave a session |
| POST | `/api/v1/sessions/{sessionId}/end` | End session (host only) |
| GET | `/api/v1/rooms/{roomId}/sessions` | Retrieve session history |

---

## 5. Screen Sharing API

| Method | Endpoint | Description |
|--------|-----------|--------------|
| POST | `/api/v1/sessions/{sessionId}/screenshare/start` | Start screen share |
| POST | `/api/v1/sessions/{sessionId}/screenshare/stop` | Stop screen share |

---

## 6. Chat Messaging API

| Method | Endpoint | Description |
|--------|-----------|--------------|
| POST | `/api/v1/sessions/{sessionId}/chat` | Send message |
| GET | `/api/v1/sessions/{sessionId}/chat` | Retrieve chat history |

---

## 7. Meeting Recording API

| Method | Endpoint | Description |
|--------|-----------|--------------|
| POST | `/api/v1/sessions/{sessionId}/recording/start` | Start recording (host only) |
| POST | `/api/v1/sessions/{sessionId}/recording/stop` | Stop recording (host only) |

---

## 8. Testing & Stabilization

### Testing Methodology
All endpoints were tested using **Postman** and **FastAPI’s interactive docs**, covering both happy-path and error cases.

### Database Optimization
Indexes added for performance:
```sql
CREATE INDEX idx_rooms_owner_id ON rooms(owner_id);
CREATE INDEX idx_sessions_room_id ON sessions(room_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

### Error Handling
A global exception handler ensures clean JSON error responses.

---

## 9. Conclusion

The OneVoice backend provides a complete, production-ready foundation for a secure and scalable real-time communication platform.
