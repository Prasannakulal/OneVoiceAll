from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, security, database, models

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

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