from sqlalchemy.inspection import inspect
from datetime import datetime

def orm_to_dict(obj):
    data = {}
    for c in inspect(obj).mapper.column_attrs:
        value = getattr(obj, c.key)

        # Convert datetime to ISO string
        if isinstance(value, datetime):
            value = value.isoformat()

        data[c.key] = value

    return data
