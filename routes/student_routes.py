from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.student_schema import StudentCreate, StudentOut, StudentBase
from controllers import student_controller

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/", response_model=StudentOut)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    return student_controller.create_student(db, student)

@router.get("/", response_model=List[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return student_controller.get_students(db)

@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: str, db: Session = Depends(get_db)):
    return student_controller.get_student(db, student_id)

@router.get("/id_number/{id_number}")
def read_student(id_number: str, db: Session = Depends(get_db)):
    """
    Fetch student by id_number
    """
    return student_controller.get_student_by_id_number(db, id_number)

@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, student: StudentBase, db: Session = Depends(get_db)):
    return student_controller.update_student(db, student_id, student)

@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    return student_controller.delete_student(db, student_id)

@router.post("/upload-csv")
def upload_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload CSV file to bulk create students.
    """
    return student_controller.upload_students_csv(db, file)

@router.get("/download-csv")
def download_students(db: Session = Depends(get_db)):
    """
    Download all students as CSV.
    """
    return student_controller.download_students_csv(db)
