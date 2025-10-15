from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, security, database, models

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

# ✅ NEW ENDPOINT - Add this BEFORE the scheduled sessions endpoint
@router.get("/me")
def get_current_user_info(
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get current authenticated user's information including their UUID.
    This is used by the frontend to identify which participant tile belongs to the current user.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "profile_picture_url": current_user.profile_picture_url,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }


# Your existing endpoint
@router.get("/me/sessions/scheduled", response_model=schemas.ScheduledSessionListResponse)
def get_my_scheduled_sessions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Retrieves a list of all sessions scheduled by the currently authenticated user.
    """
    sessions = crud.get_scheduled_sessions_for_user(db=db, user_id=current_user.id)
    return {"data": sessions}
