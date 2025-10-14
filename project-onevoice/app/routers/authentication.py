from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import logging
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import crud, schemas, security, database

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        # Password Strength Check
        password = user.password
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long."
            )
        if not any(char.isdigit() for char in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number."
            )
        if not any(char.isupper() for char in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter."
            )

        # Check for existing email
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        new_user = crud.create_user(db=db, user=user)
        content = {
            "data": {
                "id": str(new_user.id),
                "email": new_user.email,
                "full_name": new_user.full_name,
                "created_at": new_user.created_at.isoformat() if getattr(new_user, "created_at", None) else None,
            }
        }
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=content)
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Registration failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/login", response_model=schemas.TokenPair)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=schemas.TokenPair)
def refresh_tokens(payload: schemas.RefreshRequest):
    try:
        data = security.verify_refresh_token(payload.refresh_token)
        subject = data.get("sub")
        access_token = security.create_access_token(data={"sub": subject})
        refresh_token = security.create_refresh_token(data={"sub": subject})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")