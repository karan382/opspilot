from datetime import datetime

from pydantic import BaseModel, Field


class Incident(BaseModel):
    incident_id: str
    service: str
    severity: str = Field(pattern=r"^(P1|P2|P3|P4)$")
    title: str
    description: str
    started_at: datetime
    resolved_at: datetime | None = None
    symptoms: list[str] = []