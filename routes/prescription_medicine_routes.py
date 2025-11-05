from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from controllers import prescription_medicine_controller as ctrl
from schemas.prescription_medicine_schema import PrescriptionMedicineCreate, PrescriptionMedicineUpdate

router = APIRouter(prefix="/prescription-medicines", tags=["Prescription Medicines"])

@router.get("/{prescription_id}")
def read_prescription_medicines(prescription_id: int, db: Session = Depends(get_db)):
    return ctrl.get_prescription_medicines(db, prescription_id)

@router.post("/")
def add_prescription_medicine(prescription_medicine: PrescriptionMedicineCreate, db: Session = Depends(get_db)):
    return ctrl.add_prescription_medicine(db, prescription_medicine)

@router.put("/{id}")
def update_prescription_medicine(id: int, prescription_medicine: PrescriptionMedicineUpdate, db: Session = Depends(get_db)):
    pm = ctrl.update_prescription_medicine(db, id, prescription_medicine)
    if not pm:
        raise HTTPException(status_code=404, detail="Prescription Medicine not found")
    return pm

@router.delete("/{id}")
def delete_prescription_medicine(id: int, db: Session = Depends(get_db)):
    pm = ctrl.delete_prescription_medicine(db, id)
    if not pm:
        raise HTTPException(status_code=404, detail="Prescription Medicine not found")
    return {"ok": True}
