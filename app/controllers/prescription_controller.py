from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import outerjoin
from models.student import Student
from models.lab_report import LabReport
from models.prescription import Prescription
from models.prescription_medicine import PrescriptionMedicine
from models.medicine import Medicine
from schemas.prescription_schema import PrescriptionCreate, PrescriptionUpdate
from schemas.prescription_medicine_schema import PrescriptionMedicineCreate

def get_prescriptions(db: Session, skip: int = 0, limit: int = 100):
    """
    Fetch all prescriptions with related student details, medicines, and lab reports.
    Uses joinedload for efficient eager loading.
    """
    prescriptions = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.student),  # student relationship
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Transform the result for easier serialization
    result = []
    for pres in prescriptions:
        result.append({
            "id": pres.id,
            "status": pres.status,
            "notes": pres.notes,
            "created_at": pres.created_at,
            "updated_at": pres.updated_at,

            # student details
            "student": {
                "id_number": pres.student.id_number,
                "name": pres.student.name,
                "branch": pres.student.branch,
                "section": pres.student.section,
                "email": pres.student.email
            } if pres.student else None,

            # medicines list
            "medicines": [
                {
                    "medicine_name": med.medicine.name if med.medicine else "Unknown",
                    "quantity_prescribed": med.quantity_prescribed,
                    "quantity_issued": getattr(med, "quantity_issued", None)
                }
                for med in pres.medicines
            ],

            # lab reports list
            "lab_reports": [
                {"test_name": lab.test_name, "status": lab.status}
                for lab in pres.lab_reports
            ]
        })
    return result


def get_prescription(db: Session, prescription_id: int):
    """
    Fetch a single prescription with related student, medicines, and lab reports.
    """
    pres = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.student),
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports)
        )
        .filter(Prescription.id == prescription_id)
        .first()
    )

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Return structured data
    return {
        "id": pres.id,
        "status": pres.status,
        "notes": pres.notes,
        "created_at": pres.created_at,
        "updated_at": pres.updated_at,
        "student_id": pres.student_id,
        "temperature": pres.temperature,
        "bp": pres.bp,
        "weight": pres.weight,
        # student details
        "student": {
            "id_number": pres.student.id_number,
            "name": pres.student.name,
            "branch": pres.student.branch,
            "section": pres.student.section
        } if pres.student else None,

        # medicines list
        "medicines": [
            {
                "medicine_name": med.medicine.name if med.medicine else "Unknown",
                "quantity_prescribed": med.quantity_prescribed,
                "quantity_issued": getattr(med, "quantity_issued", None)
            }
            for med in pres.medicines
        ],

        # lab reports list
        "lab_reports": [
            {"test_name": lab.test_name, "status": lab.status}
            for lab in pres.lab_reports
        ]
    }


def create_prescription(db: Session, prescription: PrescriptionCreate):
    db_prescription = Prescription(**prescription.dict(exclude={"medicines"}))
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    # handle medicines if passed
    # if prescription.medicines:
    #     for med in prescription.medicines:
    #         # check medicine availability
    #         medicine = db.query(Medicine).filter(Medicine.id == med.medicine_id).first()
    #         if medicine and medicine.quantity >= med.quantity_prescribed:
    #             # reduce stock
    #             medicine.quantity -= med.quantity_prescribed
    #             db_med = PrescriptionMedicine(
    #                 prescription_id=db_prescription.id,
    #                 medicine_id=med.medicine_id,
    #                 quantity_prescribed=med.quantity_prescribed
    #             )
    #             db.add(db_med)
    #     db.commit()
    # db.refresh(db_prescription)
    return db_prescription

def update_prescription(db: Session, prescription_id: int, prescription: PrescriptionUpdate):
    db_prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not db_prescription:
        return None
    for field, value in prescription.dict(exclude_unset=True, exclude={"medicines"}).items():
        setattr(db_prescription, field, value)
    db.commit()
    db.refresh(db_prescription)
    return db_prescription

def delete_prescription(db: Session, prescription_id: int):
    db_prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not db_prescription:
        return None
    db.delete(db_prescription)
    db.commit()
    return db_prescription

def list_prescriptions(db: Session, page: int = 1, limit: int = 10, sortBy: str = "date", status: str = "all"):
    query = db.query(Prescription)

    if status != "all":
        query = query.filter(Prescription.status == status)

    if sortBy == "date":
        query = query.order_by(desc(Prescription.created_at))
    elif sortBy == "name":  # if you want sort by id_number/name
        query = query.order_by(asc(Prescription.student_id))

    total = query.count()

    prescriptions = query.offset((page - 1) * limit).limit(limit).all()

    return prescriptions, total


def get_pending_prescriptions(db: Session):
    """
    Fetch all prescriptions with status 'Initiated by Nurse'
    and include student details in the response.
    """
    # Query prescriptions with eager loading of student relationship
    prescriptions = (
        db.query(Prescription)
        .join(Prescription.student)  # use relationship
        .filter(Prescription.status == "Initiated by Nurse")
        .all()
    )

    # Prepare response with student info
    result = []
    for pres in prescriptions:
        result.append({
            "id": pres.id,
            "student_id": pres.student_id,
            "id_number": pres.student.id_number if pres.student else None,
            "nurse_id": pres.nurse_id,
            "doctor_id": pres.doctor_id,
            "notes": pres.notes,
            "weight": pres.weight,
            "bp": pres.bp,
            "temperature": pres.temperature,
            "status": pres.status,
            "created_at": pres.created_at,
            "updated_at": pres.updated_at,
            "student_name": pres.student.name if pres.student else None,
            "branch": pres.student.branch if pres.student else None,
            "section": pres.student.section if pres.student else None
        })

    return result
