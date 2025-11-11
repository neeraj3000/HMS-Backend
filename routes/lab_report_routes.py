from os import stat
import cloudinary
from reportlab.pdfgen import canvas
from io import BytesIO
from fastapi.responses import FileResponse, StreamingResponse
from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from models.lab_report import LabReport
from database import get_db
from controllers import lab_report_controller as ctrl
from schemas.lab_report_schema import LabReportCreate, LabReportDetailedResponse, LabReportUpdate

router = APIRouter(prefix="/lab-reports", tags=["Lab Reports"])

@router.get("/")
def read_lab_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=200),
    search: str = Query(None),
    status: str = Query("all"),
    date: str = Query(None),
    db: Session = Depends(get_db)
):
    return ctrl.get_lab_reports(db, page=page, limit=limit, search=search, status=status, date=date)

@router.get("/{report_id}", response_model=LabReportDetailedResponse)
def read_lab_report(report_id: int, db: Session = Depends(get_db)):
    report = ctrl.get_lab_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Lab Report not found")
    return report

@router.post("/")
def create_lab_report(lab_report: LabReportCreate, db: Session = Depends(get_db)):
    return ctrl.create_lab_report(db, lab_report)

@router.put("/{report_id}")
async def update_lab_report(
    report_id: int,
    status: str = Form(None),
    result: str = Form(None),
    file: UploadFile = None,
    db: Session = Depends(get_db),
):
    """
    Update a lab report with optional file upload (uploaded to Cloudinary).
    Stores result_url, status, and result.
    """
    # Fetch existing report
    db_report = ctrl.get_lab_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Lab report not found")

    # Upload file to Cloudinary if provided
    result_url = None
    if file:
        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder="hospital_management/lab_reports",
                resource_type="auto"
            )
            result_url = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # Build the update payload
    update_data = LabReportUpdate(
        status=status,
        result=result,
        result_url=result_url
    )

    #  Reuse controller logic for dynamic update & prescription sync
    updated_report = ctrl.update_lab_report(db, report_id, update_data)
    return {"message": "Lab report updated successfully", "data": updated_report}

@router.delete("/{report_id}")
def delete_lab_report(report_id: int, db: Session = Depends(get_db)):
    report = ctrl.delete_lab_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Lab Report not found")
    return {"ok": True}

@router.get("/{lab_report_id}/download")
def download_lab_report(lab_report_id: int, db: Session = Depends(get_db)):
    # Fetch lab report
    lab_report = db.query(LabReport).filter(LabReport.id == lab_report_id).first()
    if not lab_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab report not found")

    # generate_lab_report_pdf returns (BytesIO, filename)
    pdf_buffer, filename = ctrl.generate_lab_report_pdf(db, lab_report)

    pdf_buffer.seek(0)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
