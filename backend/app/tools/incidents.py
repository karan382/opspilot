import json
from pathlib import Path

from langchain_core.tools import tool

from app.models.incident import Incident


INCIDENTS_FILE = Path("data/incidents.json")


@tool
def get_incident(incident_id: str) -> dict:
    """Retrieve a production incident by its incident ID."""

    if not INCIDENTS_FILE.exists():
        return {}

    with INCIDENTS_FILE.open() as file:
        incidents = json.load(file)

    for incident_data in incidents:
        if incident_data["incident_id"] == incident_id:
            incident = Incident(**incident_data)
            return incident.model_dump(mode="json")

    return {}