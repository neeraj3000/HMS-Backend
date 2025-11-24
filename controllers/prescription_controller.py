import cloudinary
from fastapi import HTTPException, UploadFile
from sqlalchemy import asc, desc, cast, String, func, case, or_, and_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from models.student import Student
from models.lab_report import LabReport
from models.prescription import Prescription
from models.prescription_medicine import PrescriptionMedicine
from models.medicine import Medicine

from schemas.prescription_schema import PrescriptionCreate, PrescriptionUpdate


# ===================================================================
# HELPER: SAFE STUDENT SERIALIZER (handles student=None)
# ===================================================================

def serialize_student(student):
    if not student:
        return None
    return {
        "id_number": student.id_number,
        "name": student.name,
        "branch": student.branch,
        "section": student.section,
        "email": student.email,
    }


# ===================================================================
# GET PRESCRIPTIONS (LIST)
# ===================================================================

def get_prescriptions(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str = None,
    status: str = None,
    date: str = None,
):
    skip = (page - 1) * limit

    query = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.student),
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports),
        )
        .order_by(desc(Prescription.created_at))
    )

    filters = []

    # --- Search ---
    if search and search.strip():
        search = search.strip()
        term = f"%{search}%"

        filters.append(
            or_(
                cast(Prescription.id, String).ilike(term),
                Prescription.other_name.ilike(term),
                Student.name.ilike(term),
                Student.id_number.ilike(term),
            )
        )

        query = query.outerjoin(Student)

    # --- Status ---
    if status and status.lower() != "all":
        filters.append(Prescription.status.ilike(f"%{status}%"))

    # --- Date ---
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
            filters.append(
                and_(
                    Prescription.created_at >= datetime.combine(d, datetime.min.time()),
                    Prescription.created_at <= datetime.combine(d, datetime.max.time()),
                )
            )
        except:
            pass

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    has_more = (page * limit) < total

    result = []
    for pres in rows:
        result.append({
            "id": pres.id,
            "status": pres.status,
            "patient_type": pres.patient_type,
            "visit_type": pres.visit_type,
            "other_name": pres.other_name,

            "nurse_notes": pres.nurse_notes,
            "doctor_notes": pres.doctor_notes,
            "nurse_image_url": pres.nurse_image_url,
            "doctor_image_url": pres.doctor_image_url,
            "audio_url": pres.audio_url,

            "created_at": pres.created_at,
            "updated_at": pres.updated_at,

            # student may be None
            "student": serialize_student(pres.student),

            "medicines": [
                {
                    "medicine_name": med.medicine.name if med.medicine else None,
                    "quantity_prescribed": med.quantity_prescribed,
                    "quantity_issued": med.quantity_issued,
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


# ===================================================================
# GET SINGLE PRESCRIPTION
# ===================================================================

def get_prescription(db: Session, prescription_id: int):
    pres = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.student),
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports),
        )
        .filter(Prescription.id == prescription_id)
        .first()
    )

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return {
        "id": pres.id,
        "status": pres.status,
        "patient_type": pres.patient_type,
        "visit_type": pres.visit_type,
        "other_name": pres.other_name,

        "nurse_notes": pres.nurse_notes,
        "doctor_notes": pres.doctor_notes,
        "ai_summary": pres.ai_summary,
        "nurse_image_url": pres.nurse_image_url,
        "doctor_image_url": pres.doctor_image_url,
        "audio_url": pres.audio_url,

        "created_at": pres.created_at,
        "updated_at": pres.updated_at,

        "student_id": pres.student_id,
        "student": serialize_student(pres.student),

        "temperature": pres.temperature,
        "bp": pres.bp,
        "age": pres.age,
        "weight": pres.weight,

        "medicines": [
            {
                "id": med.id,
                "medicine": {
                    "id": med.medicine.id if med.medicine else None,
                    "name": med.medicine.name if med.medicine else None,
                    "quantity": med.medicine.quantity if med.medicine else None,
                },
                "quantity_prescribed": med.quantity_prescribed,
                "quantity_issued": med.quantity_issued,
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
    }


# ===================================================================
# GET PRESCRIPTIONS BY STUDENT ID
# ===================================================================

from sqlalchemy.orm import joinedload
from sqlalchemy import desc, or_, and_, cast, String, func
from datetime import datetime

def get_prescriptions_by_studentid(
    db: Session,
    student_id: int,
    page: int = 1,
    limit: int = 10,
    search: str = "",
    status: str = "all",
    date: str = None
):
    if page < 1:
        page = 1

    skip = (page - 1) * limit

    q = (
        db.query(Prescription)
        .filter(Prescription.student_id == student_id)
        .options(
            joinedload(Prescription.student),
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports),
        )
    )

    filters = []

    # --- Search ---
    if search.strip():
        s = search.strip()
        search_term = f"%{s}%"

        filters.append(
            or_(
                cast(Prescription.id, String).ilike(search_term),
                Prescription.nurse_notes.ilike(search_term),
                Prescription.doctor_notes.ilike(search_term),
                Prescription.other_name.ilike(search_term),
                Prescription.patient_type.ilike(search_term),
                Prescription.visit_type.ilike(search_term),
            )
        )

    # --- Status ---
    if status and status.lower() != "all":
        filters.append(Prescription.status.ilike(f"%{status}%"))

    # --- Date Filter ---
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
            filters.append(
                and_(
                    Prescription.created_at >= datetime.combine(d, datetime.min.time()),
                    Prescription.created_at < datetime.combine(d, datetime.max.time()),
                )
            )
        except:
            pass

    # Apply filters
    if filters:
        q = q.filter(and_(*filters))

    # Total count
    total = q.count()

    # Sorting + pagination
    rows = (
        q.order_by(desc(Prescription.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    has_more = (page * limit) < total

    # ---- Serialize ----
    result = []

    for pres in rows:
        result.append({
            "id": pres.id,
            "status": pres.status,

            "patient_type": pres.patient_type,
            "visit_type": pres.visit_type,
            "other_name": pres.other_name,

            "nurse_notes": pres.nurse_notes,
            "doctor_notes": pres.doctor_notes,

            "age": pres.age,
            "temperature": pres.temperature,
            "bp": pres.bp,
            "weight": pres.weight,

            "created_at": pres.created_at,
            "updated_at": pres.updated_at,

            "student": serialize_student(pres.student),

            "medicines": [
                {
                    "id": med.id,
                    "medicine_name": med.medicine.name if med.medicine else None,
                    "quantity_prescribed": med.quantity_prescribed,
                    "quantity_issued": med.quantity_issued,
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
                    "updated_at": lab.updated_at
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


# ===================================================================
# CREATE PRESCRIPTION
# ===================================================================

def create_prescription(db: Session, data: PrescriptionCreate):

    db_prescription = Prescription(
        student_id=data.student_id,       # may be None
        other_name=data.other_name,       # string or None

        nurse_id=data.nurse_id,
        nurse_notes=data.nurse_notes,

        weight=data.weight,
        bp=data.bp,
        age=data.age,
        temperature=data.temperature,

        patient_type=data.patient_type,
        visit_type=data.visit_type,

        nurse_image_url=data.nurse_image_url,
        status=data.status or "Initiated by Nurse",
    )

    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)

    # --- Save Medicines ---
    if data.medicines:
        for med in data.medicines:
            db.add(
                PrescriptionMedicine(
                    prescription_id=db_prescription.id,
                    medicine_id=med.medicine_id,
                    quantity_prescribed=med.quantity,
                )
            )

    # --- Save Lab Tests ---
    if data.lab_tests:
        for test in data.lab_tests:
            db.add(
                LabReport(
                    prescription_id=db_prescription.id,
                    test_name=test,
                    status="Lab Test Requested",
                )
            )

    db.commit()
    return db_prescription


# ===================================================================
# UPDATE PRESCRIPTION (doctor)
# ===================================================================

def update_prescription(db: Session, prescription_id: int, prescription: PrescriptionUpdate):
    db_pres = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not db_pres:
        return None

    for field, value in prescription.dict(exclude_unset=True).items():
        setattr(db_pres, field, value)

    db.commit()
    db.refresh(db_pres)
    return db_pres


# ===================================================================
# UPDATE WITH AUDIO (doctor)
# ===================================================================

def update_prescription_with_audio(
    db: Session,
    prescription_id: int,
    doctor_id: int,
    doctor_notes: str,
    ai_summary: str,
    status: str,
    doctor_image_url: str = None,
    file: UploadFile = None,
):
    pres = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        return None, "Prescription not found"

    try:
        audio_url = None
        if file:
            upload_result = cloudinary.uploader.upload(
                file.file,
                resource_type="video",
                folder="hms/doctor-audio",
            )
            audio_url = upload_result.get("secure_url")

        pres.doctor_id = doctor_id
        pres.doctor_notes = doctor_notes
        pres.ai_summary = ai_summary
        pres.status = status

        if doctor_image_url:
            pres.doctor_image_url = doctor_image_url
        if audio_url:
            pres.audio_url = audio_url

        db.commit()
        db.refresh(pres)
        return pres, None

    except Exception as e:
        db.rollback()
        return None, str(e)


# ===================================================================
# DELETE PRESCRIPTION
# ===================================================================

def delete_prescription(db: Session, prescription_id: int):
    pres = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        return None

    db.delete(pres)
    db.commit()
    return pres


# ===================================================================
# PENDING PRESCRIPTIONS
# ===================================================================

def get_pending_prescriptions(db: Session):
    records = (
        db.query(Prescription)
        .options(joinedload(Prescription.student))
        .filter(Prescription.status == "Initiated by Nurse")
        .all()
    )

    result = []
    for pres in records:
        result.append({
            "id": pres.id,
            "student_id": pres.student_id,
            "other_name": pres.other_name,
            "patient_type": pres.patient_type,
            "visit_type": pres.visit_type,

            "nurse_notes": pres.nurse_notes,
            "doctor_notes": pres.doctor_notes,
            "weight": pres.weight,
            "bp": pres.bp,
            "age": pres.age,
            "temperature": pres.temperature,

            "status": pres.status,
            "created_at": pres.created_at,

            # student may be None
            "student": serialize_student(pres.student),
        })

    return result

# ===================== PRESCRIBED QUEUE CONTROLLER =====================

from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_, cast, String, desc
from datetime import datetime
from models.student import Student
from models.prescription import Prescription
from models.prescription_medicine import PrescriptionMedicine
from models.lab_report import LabReport


def get_prescribed_queue(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str = None,
    date: str = None,
    status: str = None,          # <-- important (avoid 422)
):
    """
    Fetch prescriptions where status is:
      - Medication Prescribed by Doctor
      - Medication Prescribed and Lab Test Requested
      - Medication Prescribed by Nurse (Emergency)
    Supports pagination, search, date filter.
    """

    skip = (page - 1) * limit

    VALID_STATUSES = [
        "Medication Prescribed by Doctor",
        "Medication Prescribed and Lab Test Requested",
        "Medication Prescribed by Nurse (Emergency)",
    ]

    q = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.student),
            joinedload(Prescription.medicines).joinedload(PrescriptionMedicine.medicine),
            joinedload(Prescription.lab_reports),
        )
        .filter(Prescription.status.in_(VALID_STATUSES))
    )

    # --- SEARCH ---
    if search and search.strip():
        s = f"%{search.lower().strip()}%"
        q = (
            q.outerjoin(Student)
             .filter(
                 or_(
                     cast(Prescription.id, String).ilike(s),
                     Prescription.other_name.ilike(s),
                     Student.name.ilike(s),
                     Student.id_number.ilike(s),
                 )
             )
        )

    # --- DATE FILTER ---
    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
            q = q.filter(
                and_(
                    Prescription.created_at >= datetime.combine(d, datetime.min.time()),
                    Prescription.created_at <= datetime.combine(d, datetime.max.time()),
                )
            )
        except:
            pass

    total = q.count()

    rows = (
        q.order_by(desc(Prescription.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    has_more = (page * limit) < total

    # --- SERIALIZE ---
    data = []
    for pres in rows:
        data.append({
            "id": pres.id,
            "status": pres.status,
            "patient_type": pres.patient_type,
            "visit_type": pres.visit_type,
            "other_name": pres.other_name,

            # Student object (nullable)
            "student": {
                "id_number": pres.student.id_number,
                "name": pres.student.name,
                "branch": pres.student.branch,
                "section": pres.student.section,
                "email": pres.student.email,
            } if pres.student else None,

            # Notes
            "nurse_notes": pres.nurse_notes,
            "doctor_notes": pres.doctor_notes,

            # Vitals
            "age": pres.age,
            "bp": pres.bp,
            "temperature": pres.temperature,
            "weight": pres.weight,

            # Medicines
            "medicines": [
                {
                    "medicine_name": pm.medicine.name if pm.medicine else None,
                    "quantity_prescribed": pm.quantity_prescribed,
                    "quantity_issued": pm.quantity_issued,
                }
                for pm in pres.medicines
            ],

            # Lab reports
            "lab_reports": [
                {
                    "id": lr.id,
                    "test_name": lr.test_name,
                    "status": lr.status,
                    "result": lr.result,
                    "created_at": lr.created_at,
                }
                for lr in pres.lab_reports
            ],

            "created_at": pres.created_at,
            "updated_at": pres.updated_at,
        })

    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "has_more": has_more,
    }
