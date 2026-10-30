"""
Request and response shapes for the API.

Both databases store the data differently (3 joined tables vs nested
documents), but the API always speaks the same flat "record", using the
column names from src/load_data.py. So predict.py doesn't care which
database a record came from.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

WindDir = Literal["NE", "NW", "SE", "cv"]


class Record(BaseModel):
    """One hour of data. pm25 can be null (sensor gap), as in the raw data."""

    datetime: datetime
    pm25: Optional[float] = Field(None, ge=0, description="PM2.5 in ug/m3")
    dew_point: float
    temperature: float
    pressure: float = Field(..., gt=800, lt=1200, description="hPa")
    wind_dir: WindDir
    wind_speed: float = Field(..., ge=0)
    hours_snow: int = Field(0, ge=0)
    hours_rain: int = Field(0, ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "datetime": "2015-01-01T00:00:00",
                "pm25": 15.0,
                "dew_point": -20,
                "temperature": -4,
                "pressure": 1034,
                "wind_dir": "NW",
                "wind_speed": 251.64,
                "hours_snow": 0,
                "hours_rain": 0,
            }
        }
    }


class RecordUpdate(BaseModel):
    """Fields to change on an existing hour. Only the fields sent are updated."""

    pm25: Optional[float] = Field(None, ge=0)
    dew_point: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = Field(None, gt=800, lt=1200)
    wind_dir: Optional[WindDir] = None
    wind_speed: Optional[float] = Field(None, ge=0)
    hours_snow: Optional[int] = Field(None, ge=0)
    hours_rain: Optional[int] = Field(None, ge=0)

    model_config = {"json_schema_extra": {"example": {"pm25": 18.0}}}
