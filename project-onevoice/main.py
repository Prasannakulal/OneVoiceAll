import asyncio
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
# from app.routers import authentication, rooms # <-- Import rooms
# from app.routers import authentication, rooms, sessions 
# from app.routers import authentication, rooms, sessions, chat # Import the new chat router# Import the new sessions router
from app.routers import authentication, rooms, sessions, chat, users  ,signaling, webrtc # Import the new users router
from fastapi.middleware.cors import CORSMiddleware
from app.signaling import manager # <-- Import the manager

app = FastAPI()

# --- Heartbeat Task ---
async def heartbeat():
    while True:
        await asyncio.sleep(20) # Send a ping every 20 seconds
        for connection in list(manager.all_connections):
            try:
                # The ping message can be anything, even empty.
                await connection.send_text('{"type": "ping"}')
            except Exception:
                # If sending fails, the connection is likely dead.
                # The disconnect logic in the websocket endpoint will handle the cleanup.
                pass

# --- Lifespan Event Handler ---
@app.on_event("startup")
async def startup_event():
    # Start the heartbeat task when the application starts
    asyncio.create_task(heartbeat())


origins = [
    "http://localhost:5173", # <-- Your Vite frontend
    "http://localhost:3000", # <-- In case you use React/Next.js
    "http://localhost:3001", # <-- Original frontend
    "http://localhost:3002", # <-- Zynthora AI frontend
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)



@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred."},
    )
# ------------------------------------

app.include_router(authentication.router)
app.include_router(rooms.router) # <-- Include the rooms router
app.include_router(sessions.router) # Include the sessions router
app.include_router(chat.router) 
app.include_router(users.router)
app.include_router(signaling.router)
app.include_router(webrtc.router)
@app.get("/")
def read_root():
    return {"message": "Welcome to the OneVoice API"}