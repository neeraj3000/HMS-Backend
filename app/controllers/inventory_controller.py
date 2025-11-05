from sqlalchemy.orm import Session
from models.inventory import InventoryItem
from schemas.inventory_schema import InventoryItemCreate, InventoryItemUpdate
import pandas as pd
import io
from openpyxl import Workbook


def get_inventory_excel(db: Session):
    items = db.query(InventoryItem).all()
    data = [
        {"ID": i.id, "Name": i.name, "Category": i.category, "Quantity": i.quantity}
        for i in items
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventory")
    output.seek(0)
    return output

def bulk_upload_inventory(db: Session, file):
    df = pd.read_excel(file)
    count = 0

    for _, row in df.iterrows():
        item = InventoryItem(
            name=row["Name"],
            category=row["Category"],
            quantity=int(row["Quantity"]),
        )
        db.add(item)
        count += 1

    db.commit()
    return {"count": count}

def create_item(db: Session, item: InventoryItemCreate):
    db_item = InventoryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_all_items(db: Session):
    return db.query(InventoryItem).all()

def get_item_by_id(db: Session, item_id: int):
    return db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

def update_item(db: Session, item_id: int, item_update: InventoryItemUpdate):
    db_item = get_item_by_id(db, item_id)
    if not db_item:
        return None
    for field, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    db_item = get_item_by_id(db, item_id)
    if not db_item:
        return None
    db.delete(db_item)
    db.commit()
    return db_item
