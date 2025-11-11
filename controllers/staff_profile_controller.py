from sqlalchemy.orm import Session
from models.staff_profile import StaffProfile
from schemas.staff_profile_schema import StaffProfileCreate, StaffProfileUpdate
from fastapi import HTTPException, status

#  Create a new profile
def create_staff_profile(db: Session, profile_data: StaffProfileCreate):
    existing = db.query(StaffProfile).filter(
        (StaffProfile.user_id == profile_data.user_id) | 
        (StaffProfile.employeeId == profile_data.employeeId)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")

    new_profile = StaffProfile(**profile_data.dict())
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile

#  Get all profiles
def get_all_profiles(db: Session):
    return db.query(StaffProfile).all()

#  Get profile by user_id or employeeId
def get_profile(db: Session, user_id: int = None, employeeId: str = None):
    query = db.query(StaffProfile)
    if user_id:
        profile = query.filter(StaffProfile.user_id == user_id).first()
    elif employeeId:
        profile = query.filter(StaffProfile.employeeId == employeeId).first()
    else:
        raise HTTPException(status_code=400, detail="user_id or employeeId required")

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

#  Update staff profile
def update_profile(db: Session, user_id: int, update_data: StaffProfileUpdate):
    profile = db.query(StaffProfile).filter(StaffProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile

#  Delete staff profile
def delete_profile(db: Session, user_id: int):
    profile = db.query(StaffProfile).filter(StaffProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted successfully"}
