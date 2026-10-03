from datetime import datetime

from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str
    metadata: dict = {}