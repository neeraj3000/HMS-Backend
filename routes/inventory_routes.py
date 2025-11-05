from curses.ascii import ctrl
from click import File
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from schemas.inventory_schema import InventoryItemCreate, InventoryItemUpdate, InventoryItemOut
from controllers import inventory_controller

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post("/bulk-upload")
async def bulk_upload_inventory(file: UploadFile = File(...), db: Session = Depends(get_db)):
    result = inventory_controller.bulk_upload_inventory(db, file.file)
    return result

@router.get("/download")
def download_inventory(db: Session = Depends(get_db)):
    excel_buffer = inventory_controller.get_inventory_excel(db)
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory-items.xlsx"},
    )

@router.post("/", response_model=InventoryItemOut)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    return inventory_controller.create_item(db, item)

@router.get("/", response_model=list[InventoryItemOut])
def list_inventory_items(db: Session = Depends(get_db)):
    return inventory_controller.get_all_items(db)

@router.get("/{item_id}", response_model=InventoryItemOut)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = inventory_controller.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=InventoryItemOut)
def update_inventory_item(item_id: int, item_update: InventoryItemUpdate, db: Session = Depends(get_db)):
    item = inventory_controller.update_item(db, item_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{item_id}", response_model=InventoryItemOut)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = inventory_controller.delete_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
