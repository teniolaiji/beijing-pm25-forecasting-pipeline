"""MongoDB endpoints, mounted at /mongo. Same contract as /sql."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import DuplicateKeyError

from api import mongo_db
from api.schemas import Record, RecordUpdate

router = APIRouter(prefix="/mongo", tags=["MongoDB"])


def _not_found(ts):
    return HTTPException(status.HTTP_404_NOT_FOUND, f"No record for {ts.isoformat()}")


@router.post("/records", response_model=Record, status_code=status.HTTP_201_CREATED)
def create(record: Record):
    try:
        mongo_db.create_record(record.model_dump())
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"A record for {record.datetime.isoformat()} already exists")
    return mongo_db.get_record(record.datetime)


@router.get("/records/{ts}", response_model=Record)
def read(ts: datetime):
    rec = mongo_db.get_record(ts)
    if rec is None:
        raise _not_found(ts)
    return rec


@router.put("/records/{ts}", response_model=Record)
def update(ts: datetime, changes: RecordUpdate):
    fields = changes.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Send at least one field to update")
    if not mongo_db.update_record(ts, fields):
        raise _not_found(ts)
    return mongo_db.get_record(ts)


@router.delete("/records/{ts}", status_code=status.HTTP_204_NO_CONTENT)
def delete(ts: datetime):
    if not mongo_db.delete_record(ts):
        raise _not_found(ts)
