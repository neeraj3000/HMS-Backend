from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controllers.stats_controller import get_hospital_stats, get_lab_tech_stats
from database import get_db

router = APIRouter()

@router.get("/doctor-stats")
def fetch_stats(db: Session = Depends(get_db)):
    return get_hospital_stats(db)

@router.get("/lab-tech-stats")
def fetch_stats(db: Session = Depends(get_db)):
    return get_lab_tech_stats(db)
