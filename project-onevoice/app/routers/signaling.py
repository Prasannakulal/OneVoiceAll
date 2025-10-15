import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.orm import Session
from .. import crud, security, database
from ..signaling import manager

router = APIRouter(
    tags=["Signaling"]
)

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...),
    db: Session = Depends(database.get_db)
):
    # Authenticate the user and validate the room
    user = security.get_current_user(token=token, db=db)
    if not user or not crud.get_room_by_id(db, room_id=room_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")

            # Handle chat messages
            if message_type == "chat-message":
                chat_payload = json.dumps({
                    "type": "chat-message",
                    "sender_id": str(user.id),
                    "full_name": user.full_name,
                    "text": message.get("text")
                })
                await manager.broadcast(chat_payload, room_id, websocket)
            
            # Handle screenshare start
            elif message_type == "screenshare-started":
                await manager.broadcast(data, room_id, websocket)
            
            # Handle screenshare stop
            elif message_type == "screenshare-stopped":
                await manager.broadcast(data, room_id, websocket)
            
            # Handle WebRTC signaling (offer, answer, ICE candidates)
            elif message_type in ["offer", "answer", "ice-candidate"]:
                await manager.broadcast(data, room_id, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        # Inform others that a user has left
        await manager.broadcast(
            json.dumps({
                "type": "user_left", 
                "user_id": str(user.id)
            }), 
            room_id, 
            websocket
        )