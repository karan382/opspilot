import json
from pathlib import Path

from app.models.incident import Incident


DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "incidents.json"


with DATA_FILE.open() as file:
    incidents = json.load(file)


for data in incidents:
    incident = Incident(**data)
    print(f"✓ {incident.incident_id}: {incident.title}")