from fastapi import WebSocket
import logging

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.all_connections: set[WebSocket] = set() # <-- ADD THIS LINE

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        self.all_connections.add(websocket) # <-- ADD THIS LINE
        logging.info(f"WebSocket {websocket.client.host} connected to room {room_id}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            # Use a loop to safely remove the websocket
            self.active_connections[room_id] = [conn for conn in self.active_connections[room_id] if conn != websocket]
        if websocket in self.all_connections:
            self.all_connections.remove(websocket) # <-- ADD THIS LINE
        logging.info(f"WebSocket {websocket.client.host} disconnected from room {room_id}")

    async def broadcast(self, message: str, room_id: str, sender: WebSocket):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection is not sender:
                    await connection.send_text(message)

manager = ConnectionManager()