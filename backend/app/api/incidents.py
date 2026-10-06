from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.database import IncidentDB
from app.models.incident import Incident


router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["incidents"],
)


def get_db():
    with SessionLocal() as session:
        yield session


@router.get("", response_model=list[Incident])
async def list_incidents(
    db: Session = Depends(get_db),
):
    incidents = (
        db.query(IncidentDB)
        .order_by(IncidentDB.incident_id)
        .all()
    )

    return [
        Incident(
            incident_id=incident.incident_id,
            service=incident.service,
            severity=incident.severity,
            title=incident.title,
            description=incident.description,
            started_at=incident.started_at,
            resolved_at=incident.resolved_at,
            symptoms=incident.symptoms,
        )
        for incident in incidents
    ]