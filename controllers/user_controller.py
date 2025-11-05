from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.hash import bcrypt
from models.user import User
from schemas.user_schema import UserCreate, UserBase

# CREATE
def create_user(db: Session, user: UserCreate):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed_pw = bcrypt.hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        role=user.role,
        hashed_password=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# READ - all
def get_users(db: Session):
    return db.query(User).all()

# READ - one
def get_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# UPDATE
def update_user(db: Session, user_id: int, user_data: UserBase):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.username = user_data.username
    user.email = user_data.email
    user.role = user_data.role
    db.commit()
    db.refresh(user)
    return user

# DELETE
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}
