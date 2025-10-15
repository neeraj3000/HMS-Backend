import io
import csv
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from models.student import Student
from schemas.student_schema import StudentCreate, StudentBase
from fastapi.responses import StreamingResponse

# CREATE
def create_student(db: Session, student: StudentCreate):
    if db.query(Student).filter(Student.id_number == student.id_number).first():
        raise HTTPException(status_code=400, detail="Student already exists")
    new_student = Student(**student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

# READ - all
def get_students(db: Session):
    return db.query(Student).all()

# READ - one
def get_student(db: Session, student_id: str):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

def get_student_by_id_number(db: Session, id_number: str):
    student = db.query(Student).filter(Student.id_number == id_number).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# UPDATE
def update_student(db: Session, student_id: int, student_data: StudentBase):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.id_number = student_data.id_number
    student.email = student_data.email
    student.name = student_data.name
    student.branch = student_data.branch
    student.section = student_data.section
    db.commit()
    db.refresh(student)
    return student

# DELETE
def delete_student(db: Session, id_number: int):
    student = db.query(Student).filter(Student.id == id_number).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"detail": "Student deleted"}

# BULK UPLOAD
def upload_students_csv(db: Session, file: UploadFile):
    """
    Accepts a CSV file with columns:
    id_number, name, email, branch, section
    Validates each row with StudentCreate schema before insert.
    """
    try:
        content = file.file.read().decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file")

    reader = csv.DictReader(io.StringIO(content))
    inserted = []

    for i, row in enumerate(reader, start=1):
        try:
            student_in = StudentCreate(**row)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Row {i} invalid: {str(e)}"
            )

        # Skip if already exists
        if db.query(Student).filter(Student.id_number == student_in.id_number).first():
            continue  

        new_student = Student(**student_in.dict())
        db.add(new_student)
        inserted.append(new_student)

    db.commit()
    return {"inserted": len(inserted)}

# DOWNLOAD CSV
def download_students_csv(db: Session):
    """
    Returns CSV of all students.
    """
    students = db.query(Student).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "id_number", "name", "email", "branch", "section"])
    for s in students:
        writer.writerow([s.id, s.id_number, s.name, s.email, s.branch, s.section])

    output.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename=students.csv'
    }
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)