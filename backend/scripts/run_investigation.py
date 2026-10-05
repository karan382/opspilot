import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from app.agents.graph import graph


INCIDENT_ID = "INC-004"
INCIDENTS_FILE = Path("data/incidents.json")


def load_incident(incident_id: str) -> dict:
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
Symptoms:
{chr(10).join(f"- {symptom}" for symptom in incident["symptoms"])}
"""


initial_state = {
    "messages": [HumanMessage(content=incident_context)],
    "report": None,
    "iterations": 0,
    "incident_id": incident["incident_id"],
}


result = graph.invoke(
    initial_state,
    config={"recursion_limit": 20},
)


print("\n=== INVESTIGATION TRACE ===\n")

for message in result["messages"]:
    message_type = getattr(message, "type", "unknown")
    tool_name = getattr(message, "name", None)

    if message_type == "tool":
        print(f"[TOOL: {tool_name}]")
        print(message.content)
        print()

print("\n=== OPSPILOT INVESTIGATION REPORT ===\n")
print(result["report"].model_dump_json(indent=2))