import cloudinary
from fastapi import HTTPException, UploadFile
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import outerjoin
from models.student import Student
from models.lab_report import LabReport
from models.prescription import Prescription
from models.prescription_medicine import PrescriptionMedicine
from models.medicine import Medicine
from schemas.prescription_schema import PrescriptionCreate, PrescriptionUpdate
from sqlalchemy import or_, and_,cast, String, func, case
from datetime import datetime


def get_prescriptions(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str = None,
    status: str = None,
    date: str = None
):
    skip = (page - 1) * limit

    base_query = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.student),
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports)
        )
        .join(Student)
    )

    filters = []

    # --- Search ---
    if search and search.strip():
        search = search.strip()
        search_term = f"%{search}%"

        id_condition = cast(Prescription.id, String).ilike(search_term)
        name_condition = Student.name.ilike(search_term)
        idnum_condition = Student.id_number.ilike(search_term)

        filters.append(or_(id_condition, name_condition, idnum_condition))

        relevance_score = case(
            (func.lower(Student.id_number) == func.lower(search), 3),
            (func.lower(Student.name).startswith(func.lower(search)), 2),
            (func.lower(Student.name).ilike(search_term), 1),
            else_=0
        ).label("score")

        query = (
            db.query(Prescription, relevance_score)
            .join(Student)
            .filter(or_(id_condition, name_condition, idnum_condition))
            .order_by(desc("score"), desc(Prescription.created_at))
        )
    else:
        query = base_query.order_by(desc(Prescription.created_at))

    # --- Status Filter ---
    if status and status.lower() != "all":
        filters.append(Prescription.status.ilike(f"%{status}%"))

    # --- Date Filter ---
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            filters.append(
                and_(
                    Prescription.created_at >= datetime.combine(date_obj, datetime.min.time()),
                    Prescription.created_at < datetime.combine(date_obj, datetime.max.time())
                )
            )
        except ValueError:
            pass

    # Apply filters
    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    has_more = (page * limit) < total

    result = []

    for row in rows:
        # Handle all possible return shapes safely
        if hasattr(row, "_mapping"):
            # SQLAlchemy Row object
            pres = row._mapping.get("Prescription", None)
            score = row._mapping.get("score", None)
        elif isinstance(row, tuple):
            pres, score = row
        else:
            pres = row
            score = None

        if pres is None:
            continue  # Skip invalid entries just in case

        result.append({
            "id": pres.id,
            "status": pres.status,
            "nurse_notes": pres.nurse_notes,
            "doctor_notes": pres.doctor_notes,
            "nurse_image_url": pres.nurse_image_url,
            "doctor_image_url": pres.doctor_image_url,
            "audio_url": pres.audio_url,
            "created_at": pres.created_at,
            "updated_at": pres.updated_at,
            "student": {
                "id_number": pres.student.id_number,
                "name": pres.student.name,
                "branch": pres.student.branch,
                "section": pres.student.section,
                "email": pres.student.email,
            } if pres.student else None,
            "medicines": [
                {
                    "medicine_name": med.medicine.name if med.medicine else "Unknown",
                    "quantity_prescribed": med.quantity_prescribed,
                    "quantity_issued": getattr(med, "quantity_issued", None),
                }
                for med in pres.medicines
            ],
            "lab_reports": [
                {
                    "id": lab.id,
                    "test_name": lab.test_name,
                    "status": lab.status,
                    "result": lab.result,
                    "created_at": lab.created_at,
                    "updated_at": lab.updated_at,
                }
                for lab in pres.lab_reports
            ],
        })

    return {
        "data": result,
        "page": page,
        "limit": limit,
        "total": total,
        "has_more": has_more,
    }



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
        "nurse_notes": pres.nurse_notes,
        "doctor_notes": pres.doctor_notes,
        "ai_summary": pres.ai_summary,
        "nurse_image_url": pres.nurse_image_url,
        "doctor_image_url": pres.doctor_image_url,
        "audio_url": pres.audio_url,
        "created_at": pres.created_at,
        "updated_at": pres.updated_at,
        "student_id": pres.student_id,
        "temperature": pres.temperature,
        "bp": pres.bp,
        "age": pres.age,
        "weight": pres.weight,
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
                "id": med.id,
                "medicine": {
                    "id": med.medicine.id if med.medicine else None,
                    "name": med.medicine.name if med.medicine else "Unknown",
                    "quantity": med.medicine.quantity if med.medicine else None
                },
                "quantity_prescribed": med.quantity_prescribed,
                "quantity_issued": getattr(med, "quantity_issued", None)
            }
            for med in pres.medicines
        ],

        # lab reports list
        "lab_reports": [
            {"id": lab.id, "test_name": lab.test_name, "status": lab.status, "result": lab.result, "created_at": lab.created_at, "updated_at": lab.updated_at}
            for lab in pres.lab_reports
        ]
    }

def get_prescriptions_by_studentid( db: Session, student_id: int, skip: int = 0, limit: int = 100):
    """
    Fetch all prescriptions for a given student (by student.id)
    including related student info, medicines, and lab reports.
    """
    prescriptions = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.student),
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports)
        )
        .filter(Prescription.student_id == student_id)
        .order_by(Prescription.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not prescriptions:
        raise HTTPException(status_code=404, detail="No prescriptions found for this student")

    return [
        {
            "id": pres.id,
            "status": pres.status,
            "nurse_notes": pres.nurse_notes,
            "doctor_notes": pres.doctor_notes,
            "nurse_image_url": pres.nurse_image_url,
            "doctor_image_url": pres.doctor_image_url,
            "audio_url": pres.audio_url,
            "created_at": pres.created_at,
            "updated_at": pres.updated_at,
            "student_id": pres.student_id,
            "temperature": pres.temperature,
            "bp": pres.bp,
            "age": pres.age,
            "weight": pres.weight,

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
                    "id": med.id,
                    "medicine": {
                        "id": med.medicine.id if med.medicine else None,
                        "name": med.medicine.name if med.medicine else "Unknown",
                        "quantity": med.medicine.quantity if med.medicine else None
                    },
                    "quantity_prescribed": med.quantity_prescribed,
                    "quantity_issued": getattr(med, "quantity_issued", None)
                }
                for med in pres.medicines
            ],

            # lab reports list
            "lab_reports": [
                {
                    "id": lab.id,
                    "test_name": lab.test_name,
                    "status": lab.status,
                    "result": lab.result,
                    "created_at": lab.created_at,
                    "updated_at": lab.updated_at
                }
                for lab in pres.lab_reports
            ]
        }
        for pres in prescriptions
    ]


def create_prescription(db: Session, prescription: PrescriptionCreate):
    db_prescription = Prescription(**prescription.model_dump(exclude={"medicines"}))
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

def update_prescription_with_audio(
    db: Session,
    prescription_id: int,
    doctor_id: int,
    doctor_notes: str,
    ai_summary: str,
    status: str,
    doctor_image_url: str = None,
    file: UploadFile = None
):
    """
    Uploads audio (if provided) to Cloudinary and updates prescription record.
    """
    db_prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not db_prescription:
        return None, "Prescription not found"

    try:
        # Upload audio to Cloudinary (if available)
        audio_url = None
        if file:
            upload_result = cloudinary.uploader.upload(
                file.file,
                resource_type="video",
                folder="hms/doctor-audio"
            )
            audio_url = upload_result.get("secure_url")

        # Update DB record
        db_prescription.doctor_id = doctor_id
        db_prescription.doctor_notes = doctor_notes
        db_prescription.ai_summary = ai_summary
        db_prescription.status = status
        if audio_url:
            db_prescription.audio_url = audio_url
        if doctor_image_url:
            db_prescription.doctor_image_url = doctor_image_url

        db.commit()
        db.refresh(db_prescription)

        return db_prescription, None

    except Exception as e:
        db.rollback()
        return None, str(e)

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
            "nurse_notes": pres.nurse_notes,
            "doctor_notes": pres.doctor_notes,
            "nurse_image_url": pres.nurse_image_url,
            "doctor_image_url": pres.doctor_image_url,
            "audio_url": pres.audio_url,
            "weight": pres.weight,
            "bp": pres.bp,
            "age": pres.age,
            "temperature": pres.temperature,
            "status": pres.status,
            "created_at": pres.created_at,
            "updated_at": pres.updated_at,
            "student_name": pres.student.name if pres.student else None,
            "branch": pres.student.branch if pres.student else None,
            "section": pres.student.section if pres.student else None
        })

    return result
