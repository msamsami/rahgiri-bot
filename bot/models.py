from typing import Optional

from pydantic import BaseModel


class TrackingRecord(BaseModel):
    id: int
    date: Optional[str] = None
    time: str
    description: str
    location: Optional[str] = None
