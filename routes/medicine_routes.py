from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from controllers import medicine_controller as ctrl
from models.medicine import Medicine
from schemas.medicine_schema import MedicineCreate, MedicineUpdate

router = APIRouter(prefix="/medicines", tags=["Medicines"])


# 1️⃣ Download Inventory
@router.get("/download")
def download_medicine_inventory(db: Session = Depends(get_db)):
    excel_buffer = ctrl.get_medicine_inventory_excel(db)
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=medicine-inventory.xlsx"}
    )

@router.post("/upload")
def upload_medicine_inventory(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload and import medicine inventory Excel file.
    """
    result = ctrl.import_medicine_inventory_excel(file, db)
    return result

# 2️⃣ Upload Indent File (After Admin Approval)
@router.post("/approve-indent")
async def approve_indent(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    result = ctrl.approve_indent_excel(file, db)
    return {"message": "Indent approved successfully", **result}


# 3️⃣ List Medicines
@router.get("/")
def list_medicines(
    page: int = 1,
    limit: int = 20,
    search: str = "",
    brand: str = "",
    category: str = "",
    db: Session = Depends(get_db),
):
    if page < 1:
        page = 1

    skip = (page - 1) * limit

    query = db.query(Medicine)

    # Search filter
    if search.strip():
        query = query.filter(Medicine.name.ilike(f"%{search.strip()}%"))

    # Brand filter
    if brand.strip() and brand.lower().strip() != "all":
        query = query.filter(Medicine.brand.ilike(f"%{brand.strip()}%"))

    # Category filter (NEW)
    if category.strip() and category.lower().strip() != "all":
        query = query.filter(Medicine.category.ilike(f"%{category.strip()}%"))

    total = query.count()
    medicines = query.offset(skip).limit(limit).all()

    return {
        "data": medicines,
        "page": page,
        "limit": limit,
        "total": total,
        "has_more": (page * limit) < total,
    }
    

# 4️⃣ Single Medicine Operations
@router.get("/{medicine_id}")
def read_medicine(medicine_id: int, db: Session = Depends(get_db)):
    med = ctrl.get_medicine(db, medicine_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return med


@router.post("/")
def create_medicine(medicine: MedicineCreate, db: Session = Depends(get_db)):
    return ctrl.create_medicine(db, medicine)


@router.put("/{medicine_id}")
def update_medicine(medicine_id: int, medicine: MedicineUpdate, db: Session = Depends(get_db)):
    med = ctrl.update_medicine(db, medicine_id, medicine)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return med


@router.delete("/{medicine_id}")
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    med = ctrl.delete_medicine(db, medicine_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return {"ok": True}
