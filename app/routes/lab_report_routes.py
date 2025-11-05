from os import stat
from reportlab.pdfgen import canvas
from io import BytesIO
from fastapi.responses import FileResponse, StreamingResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.lab_report import LabReport
from database import get_db
from controllers import lab_report_controller as ctrl
from schemas.lab_report_schema import LabReportCreate, LabReportUpdate

router = APIRouter(prefix="/lab-reports", tags=["Lab Reports"])

@router.get("/")
def read_lab_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ctrl.get_lab_reports(db, skip, limit)

@router.get("/{report_id}")
def read_lab_report(report_id: int, db: Session = Depends(get_db)):
    report = ctrl.get_lab_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Lab Report not found")
    return report

@router.post("/")
def create_lab_report(lab_report: LabReportCreate, db: Session = Depends(get_db)):
    return ctrl.create_lab_report(db, lab_report)

@router.put("/{report_id}")
def update_lab_report(report_id: int, lab_report: LabReportUpdate, db: Session = Depends(get_db)):
    report = ctrl.update_lab_report(db, report_id, lab_report)
    if not report:
        raise HTTPException(status_code=404, detail="Lab Report not found")
    return report

@router.delete("/{report_id}")
def delete_lab_report(report_id: int, db: Session = Depends(get_db)):
    report = ctrl.delete_lab_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Lab Report not found")
    return {"ok": True}

@router.get("/{lab_report_id}/download")
def download_lab_report(
    lab_report_id: int,
    db: Session = Depends(get_db),
):
    # Fetch lab report
    lab_report = db.query(LabReport).filter(LabReport.id == lab_report_id).first()
    if not lab_report:
        raise HTTPException(status_code=stat.HTTP_404_NOT_FOUND, detail="Lab report not found")

    # Generate PDF dynamically
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setTitle(f"LabReport_{lab_report_id}")

    # Add lab report details
    pdf.drawString(50, 820, f"Lab Report ID: {lab_report.id}")
    pdf.drawString(50, 800, f"Student ID: {lab_report.prescription.student.id_number if lab_report.prescription and lab_report.prescription.student else 'N/A'}")
    pdf.drawString(50, 780, f"Student Name: {lab_report.prescription.student.name if lab_report.prescription and lab_report.prescription.student else 'N/A'}")
    pdf.drawString(50, 760, f"Test Name: {lab_report.test_name}")
    pdf.drawString(50, 740, f"Status: {lab_report.status}")
    pdf.drawString(50, 720, f"Result: {lab_report.result or 'N/A'}")
    pdf.drawString(50, 680, f"Created At: {lab_report.created_at}")
    pdf.drawString(50, 660, f"Updated At: {lab_report.updated_at}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    # Return as downloadable PDF
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=LabReport_{lab_report_id}.pdf"}
    )
