from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from controllers import staff_profile_controller as controller
from schemas.staff_profile_schema import StaffProfileCreate, StaffProfileResponse, StaffProfileUpdate
from typing import List

router = APIRouter(prefix="/staff-profiles", tags=["Staff Profiles"])

@router.post("/", response_model=StaffProfileResponse)
def create_profile(profile: StaffProfileCreate, db: Session = Depends(get_db)):
    return controller.create_staff_profile(db, profile)

@router.get("/", response_model=List[StaffProfileResponse])
def get_all_profiles(db: Session = Depends(get_db)):
    return controller.get_all_profiles(db)

@router.get("/{user_id}", response_model=StaffProfileResponse)
def get_profile_by_user(user_id: int, db: Session = Depends(get_db)):
    return controller.get_profile(db, user_id=user_id)

@router.get("/by-employee/{employeeId}", response_model=StaffProfileResponse)
def get_profile_by_employee(employeeId: str, db: Session = Depends(get_db)):
    return controller.get_profile(db, employeeId=employeeId)

@router.put("/{user_id}", response_model=StaffProfileResponse)
def update_profile(user_id: int, profile: StaffProfileUpdate, db: Session = Depends(get_db)):
    return controller.update_profile(db, user_id, profile)

@router.delete("/{user_id}")
def delete_profile(user_id: int, db: Session = Depends(get_db)):
    return controller.delete_profile(db, user_id)
