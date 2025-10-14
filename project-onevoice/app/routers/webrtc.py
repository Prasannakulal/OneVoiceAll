from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/api/v1/webrtc",
    tags=["WebRTC"]
)

class IceServer(BaseModel):
    urls: str
    username: str = None
    credential: str = None

class WebRTCConfig(BaseModel):
    iceServers: List[IceServer]

@router.get("/config", response_model=WebRTCConfig)
def get_webrtc_config():
    """
    Provides the client with the necessary STUN and TURN server configurations.
    """
    # These values would come from environment variables in a real production app.
    ice_servers = [
        # Public STUN server for general use
        {"urls": "stun:stun.l.google.com:19302"},
        
        # This is the address of the TURN server you set up as BE2
        {
            "urls": "turn:localhost:3478",
            "username": "testuser",
            "credential": "testpassword"
        }
    ]
    return {"iceServers": ice_servers}