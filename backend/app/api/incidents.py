import json
from pathlib import Path

from fastapi import APIRouter

from app.models.incident import Incident


router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

INCIDENTS_FILE = Path("data/incidents.json")


@router.get("", response_model=list[Incident])
async def list_incidents():
    with INCIDENTS_FILE.open() as file:
        incidents = json.load(file)

    return [Incident(**incident) for incident in incidents]