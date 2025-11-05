from sqlalchemy.orm import Session
from models.prescription_medicine import PrescriptionMedicine
from schemas.prescription_medicine_schema import PrescriptionMedicineCreate, PrescriptionMedicineUpdate

def get_prescription_medicines(db: Session, prescription_id: int):
    return db.query(PrescriptionMedicine).filter(PrescriptionMedicine.prescription_id == prescription_id).all()

def add_prescription_medicine(db: Session, prescription_medicine: PrescriptionMedicineCreate):
    db_prescription_medicine = PrescriptionMedicine(**prescription_medicine.dict())
    db.add(db_prescription_medicine)
    db.commit()
    db.refresh(db_prescription_medicine)
    return db_prescription_medicine

def update_prescription_medicine(db: Session, id: int, prescription_medicine: PrescriptionMedicineUpdate):
    db_pm = db.query(PrescriptionMedicine).filter(PrescriptionMedicine.id == id).first()
    if not db_pm:
        return None
    for field, value in prescription_medicine.dict(exclude_unset=True).items():
        setattr(db_pm, field, value)
    db.commit()
    db.refresh(db_pm)
    return db_pm

def delete_prescription_medicine(db: Session, id: int):
    db_pm = db.query(PrescriptionMedicine).filter(PrescriptionMedicine.id == id).first()
    if not db_pm:
        return None
    db.delete(db_pm)
    db.commit()
    return db_pm
