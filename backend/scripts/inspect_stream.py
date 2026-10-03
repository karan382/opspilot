from pathlib import Path
import json

from langchain_core.messages import HumanMessage

from app.agents.graph import graph


INCIDENT_ID = "INC-001"
INCIDENTS_FILE = Path("data/incidents.json")


def load_incident(incident_id: str):
    with INCIDENTS_FILE.open() as file:
        incidents = json.load(file)

    for incident in incidents:
        if incident["incident_id"] == incident_id:
            return incident

    raise ValueError(f"Incident not found: {incident_id}")


incident = load_incident(INCIDENT_ID)

incident_context = f"""
Incident ID: {incident["incident_id"]}
Service: {incident["service"]}
Severity: {incident["severity"]}
Title: {incident["title"]}
Description: {incident["description"]}
Started at: {incident["started_at"]}
Resolved at: {incident["resolved_at"]}
Symptoms: {", ".join(incident["symptoms"])}
"""

initial_state = {
    "messages": [HumanMessage(content=incident_context)],
    "report": None,
    "iterations": 0,
    "incident_id": INCIDENT_ID,
}

for event in graph.stream(
    initial_state,
    config={"recursion_limit": 20},
    stream_mode="updates",
):
    print("\n=== EVENT ===")
    print(event)