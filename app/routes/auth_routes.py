from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from controllers.auth_controller import login_user
from database import get_db
from schemas.user_schema import LoginRequest, GoogleLogin
import os
from controllers.auth_controller import google_login_controller

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.environ.get("SECRET_KEY", "RESUME@123")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS", 8)

@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    return login_user(payload.email, payload.password, response, db)


@router.post("/google-login")
def google_login(req: GoogleLogin, db: Session = Depends(get_db)):
    print(req.token)
    result = google_login_controller(req.token, db)
    return result
