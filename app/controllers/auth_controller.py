from fastapi import Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from jose import jwt
import bcrypt
from schemas.student_schema import StudentOut
from database import get_db
from models.user import User
from schemas.user_schema import UserOut

import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime, timedelta, timezone
from models.user import UserRole
from models.student import Student

SECRET_KEY = os.environ.get("SECRET_KEY", "RESUME@123")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS", 8)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-google-client-id")
UNIVERSITY_EMAIL_DOMAIN = os.environ.get("UNIVERSITY_EMAIL_DOMAIN", "rguktrkv.ac.in")

def login_user(email: str, password: str, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    # Create JWT (optional for your own backend tracking)
    token_data = {"userId": user.id, "email": user.email}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    user_out = UserOut.model_validate(user, from_attributes=True)

    return {"user": user_out, "token": token}



def google_login_controller(google_token: str, db):
    print("🔹 Starting Google login controller")

    # 1️⃣ Verify the Google ID token
    try:
        idinfo = id_token.verify_oauth2_token(
            google_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        print("✅ Token verified:", idinfo)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid Google token")

    email = idinfo.get("email")
    email_verified = idinfo.get("email_verified", False)
    name = idinfo.get("name")

    print(f"Email: {email}, Verified: {email_verified}, Name: {name}")

    if not email or not email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Google account email not verified")

    # 2️⃣ Look for existing User or Student
    user = db.query(User).filter(User.email == email).first()
    student = db.query(Student).filter(Student.email == email).first()

    print(f"Existing user found: {user}")
    print(f"Existing student found: {student}")

    # 3️⃣ Create Student record if not found anywhere
    if not user and not student:
        # Enforce domain restriction
        domain = UNIVERSITY_EMAIL_DOMAIN
        if not email.lower().endswith("@" + domain.lower()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Please login with university email id (@{domain})"
            )

        print("Creating new student record…")
        student = Student(
            id_number=email.split("@")[0].upper(),
            email=email,
            name=name,
        )
        db.add(student)
        db.commit()
        db.refresh(student)
    else:
        print("Skipping insert — user/student already exists")

    # 4️⃣ Build JWT token (1 day expiry)
    expire = datetime.now(timezone.utc) + timedelta(days=1)

    if user:
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "exp": expire
        }
    else:
        token_data = {
            "email": student.email,
            "id_number": student.id_number,
            "role": "student",
            "exp": expire
        }

    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    print("Generated JWT token")

    # 5️⃣ Return response
    if user:
        user_out = UserOut.model_validate(user, from_attributes=True)
        return {
            "success": True,
            "token": token,
            "user": user_out
        }

    student_out = StudentOut.model_validate(student, from_attributes=True)
    return {
        "success": True,
        "token": token,
        "user": student_out
    }
