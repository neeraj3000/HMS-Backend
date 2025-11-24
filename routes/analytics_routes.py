from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from controllers.analytics_controller import get_inventory_analytics

router = APIRouter(
    prefix="/analytics",
    tags=["Pharmacist Analytics"]
)

@router.get("/medicines")
def pharmacist_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Returns inventory analytics filtered by last X days.
    """
    return get_inventory_analytics(db, days)
