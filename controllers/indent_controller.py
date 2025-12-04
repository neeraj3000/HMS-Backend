import os
import cloudinary.uploader
from datetime import datetime
import openpyxl
from io import BytesIO
from models.indent import Indent
from models.medicine import Medicine
from sqlalchemy.orm import Session
import requests
from cloudinary.utils import cloudinary_url


def upload_indent(file, uploaded_by: str, db: Session):
    """Upload indent file to Cloudinary as a raw Excel file with a proper filename."""
    original_name = file.filename or "indent.xlsx"
    name, ext = os.path.splitext(original_name)
    if not ext:
        ext = ".xlsx"
    final_name = name + ext

    #  Upload with proper public_id (so it doesn't become 'stream')
    upload_result = cloudinary.uploader.upload(
        file.file,
        folder="indents",
        public_id=name,              # explicitly sets filename
        resource_type="raw",         # handle Excel properly
        type="upload",               # make it public
        use_filename=True,           
        unique_filename=False,
        filename_override=final_name
    )

    file_url = upload_result.get("secure_url")
    public_id = upload_result.get("public_id")

    #  Create a clean downloadable link (with Content-Disposition: attachment)
    download_url, _ = cloudinary_url(
        public_id,
        resource_type="raw",
        type="upload",
        flags="attachment",
        attachment=final_name
    )

    new_indent = Indent(
        file_name=final_name,
        file_url=file_url,
        uploaded_by=uploaded_by,
        status="pending",
        uploaded_at=datetime.utcnow()
    )
    db.add(new_indent)
    db.commit()
    db.refresh(new_indent)

    return {
        "message": "Indent uploaded successfully",
        "indent_id": new_indent.id,
        "file_url": file_url,        # for viewing in iframe
        "download_url": download_url, # for direct .xlsx download
        "status": new_indent.status
    }

def approve_indent(indent_id: int, approved_by: str, db: Session):
    """Approve indent: update medicine stock and mark indent as approved."""
    indent = db.query(Indent).filter(Indent.id == indent_id).first()
    if not indent:
        return {"error": "Indent not found"}
    if indent.status != "pending":
        return {"error": "Indent already processed"}

    response = requests.get(indent.file_url)
    workbook = openpyxl.load_workbook(BytesIO(response.content))
    sheet = workbook.active

    inserted, updated = 0, 0

    for index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):
        try:
            s_no, drug_name, brand, category, present_qty, required_qty, cost, tax, total_cost = row[:8]
            if not drug_name:
                continue

            name = str(drug_name).strip()
            existing = db.query(Medicine).filter(Medicine.name == name).first()

            if existing:
                existing.quantity = (existing.quantity or 0) + int(required_qty or 0)
                existing.brand = brand or existing.brand
                existing.cost = cost or existing.cost
                existing.tax = tax or existing.tax
                existing.total_cost = total_cost or existing.total_cost
                existing.category = category or existing.category
                existing.expiry_date = None
                updated += 1
            else:
                new_medicine = Medicine(
                    name=name,
                    brand=brand,
                    quantity=int(present_qty or 0) + int(required_qty or 0),
                    cost=cost,
                    tax=tax,
                    total_cost=total_cost,
                    category=category or None,
                    expiry_date=None
                )
                db.add(new_medicine)
                inserted += 1
        except Exception:
            continue

    indent.status = "approved"
    indent.approved_by = approved_by
    indent.approved_at = datetime.now()

    db.commit()

    return {
        "message": "Indent approved successfully",
        "inserted": inserted,
        "updated": updated,
        "approved_by": approved_by
    }


def get_all_indents(db: Session):
    """List all indents with their details."""
    return db.query(Indent).order_by(Indent.uploaded_at.desc()).all()

def get_sample_indent():
    return {"url": "https://res.cloudinary.com/dfdpmmrdd/raw/upload/v1764833833/sample_indent.xlsx"}

