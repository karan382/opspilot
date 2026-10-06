import json
from pathlib import Path

from app.core.database import SessionLocal
from app.models.database import IncidentDB


INCIDENTS_FILE = Path("data/incidents.json")


def migrate_incidents() -> None:
    with INCIDENTS_FILE.open() as file:
        incidents = json.load(file)

    with SessionLocal() as session:
        inserted = 0

        for incident in incidents:
            existing = session.get(IncidentDB, incident["incident_id"])

            if existing:
                existing.service = incident["service"]
                existing.severity = incident["severity"]
                existing.title = incident["title"]
                existing.description = incident["description"]
                existing.started_at = incident["started_at"]
                existing.resolved_at = incident.get("resolved_at")
                existing.symptoms = incident.get("symptoms", [])
                continue

            session.add(
                IncidentDB(
                    incident_id=incident["incident_id"],
                    service=incident["service"],
                    severity=incident["severity"],
                    title=incident["title"],
                    description=incident["description"],
                    started_at=incident["started_at"],
                    resolved_at=incident.get("resolved_at"),
                    symptoms=incident.get("symptoms", []),
                )
            )
            inserted += 1

        session.commit()

    print(f"Migrated {inserted} incidents")


if __name__ == "__main__":
    migrate_incidents()