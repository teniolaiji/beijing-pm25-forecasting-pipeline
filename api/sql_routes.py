"""MySQL endpoints, mounted at /sql."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from api import sql_db
from api.config import MAX_RANGE_ROWS
from api.schemas import Record, RecordUpdate

router = APIRouter(prefix="/sql", tags=["MySQL"])


def _not_found(ts):
    return HTTPException(status.HTTP_404_NOT_FOUND, f"No record for {ts.isoformat()}")


@router.post("/records", response_model=Record, status_code=status.HTTP_201_CREATED)
def create(record: Record):
    try:
        sql_db.create_record(record.model_dump())
    except sql_db.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"A record for {record.datetime.isoformat()} already exists")
    return sql_db.get_record(record.datetime)


# Time-series queries. Declared before /records/{ts} so "latest" isn't read as a date.
@router.get("/records/latest", response_model=Record)
def latest():
    row = sql_db.get_latest()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The database is empty")
    return row


@router.get("/records", response_model=list[Record])
def date_range(
    start: datetime = Query(..., description="e.g. 2014-12-30T00:00:00"),
    end: datetime = Query(..., description="e.g. 2014-12-31T23:00:00"),
    limit: int = Query(1000, ge=1, le=MAX_RANGE_ROWS),
):
    if start > end:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "start must be before end")
    return sql_db.get_range(start, end, limit)


@router.get("/records/{ts}", response_model=Record)
def read(ts: datetime):
    row = sql_db.get_record(ts)
    if row is None:
        raise _not_found(ts)
    return row


@router.put("/records/{ts}", response_model=Record)
def update(ts: datetime, changes: RecordUpdate):
    fields = changes.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Send at least one field to update")
    if not sql_db.update_record(ts, fields):
        raise _not_found(ts)
    return sql_db.get_record(ts)


@router.delete("/records/{ts}", status_code=status.HTTP_204_NO_CONTENT)
def delete(ts: datetime):
    if not sql_db.delete_record(ts):
        raise _not_found(ts)
