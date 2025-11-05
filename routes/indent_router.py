from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from controllers import indent_controller as ctrl

router = APIRouter(prefix="/indents", tags=["Indents"])


@router.post("/upload")
async def upload_indent(
    file: UploadFile = File(...),
    uploaded_by: str = Form(...),
    db: Session = Depends(get_db)
):
    """Storekeeper uploads an indent file."""
    try:
        result = ctrl.upload_indent(file, uploaded_by, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve/{indent_id}")
async def approve_indent(indent_id: int, approved_by: str = Form(...), db: Session = Depends(get_db)):
    """Admin approves an indent and updates stock."""
    result = ctrl.approve_indent(indent_id, approved_by, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/")
def list_indents(db: Session = Depends(get_db)):
    """View all uploaded indents with status."""
    return ctrl.get_all_indents(db)
