from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agents.graph import graph
from app.models.incident import Incident
from app.models.api import InvestigationResponse

import json
from pathlib import Path


router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])

INCIDENTS_FILE = Path("data/incidents.json")


def load_incident(incident_id: str) -> Incident | None:
    if not INCIDENTS_FILE.exists():
        return None

    with INCIDENTS_FILE.open() as file:
        incidents = json.load(file)

    for incident_data in incidents:
        if incident_data["incident_id"] == incident_id:
            return Incident(**incident_data)

    return None


def investigation_event_stream(initial_state):
    for event in graph.stream(
        initial_state,
        config={"recursion_limit": 20},
        stream_mode="updates",
    ):
        if "investigator" in event:
            investigator_data = event["investigator"]
            messages = investigator_data.get("messages", [])

            if messages:
                message = messages[-1]

                if getattr(message, "tool_calls", None):
                    yield json.dumps({
                        "type": "status",
                        "status": "collecting_evidence",
                    }) + "\n"
                else:
                    yield json.dumps({
                        "type": "status",
                        "status": "analyzing_evidence",
                    }) + "\n"

        elif "tools" in event:
            yield json.dumps({
                "type": "status",
                "status": "collecting_evidence",
            }) + "\n"

        elif "report" in event:
            report = event["report"]["report"]

            yield json.dumps({
                "type": "report",
                "status": "completed",
                "report": report.model_dump(mode="json"),
            }) + "\n"


@router.post("/{incident_id}/stream")
async def stream_investigation(incident_id: str):
    incident = load_incident(incident_id)

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident_context = f"""
Incident ID: {incident.incident_id}
Service: {incident.service}
Severity: {incident.severity}
Title: {incident.title}
Description: {incident.description}
Started at: {incident.started_at}
Resolved at: {incident.resolved_at}
Symptoms: {", ".join(incident.symptoms)}
"""

    initial_state = {
        "messages": [HumanMessage(content=incident_context)],
        "report": None,
        "iterations": 0,
        "incident_id": incident.incident_id,
    }

    return StreamingResponse(
        investigation_event_stream(initial_state),
        media_type="application/x-ndjson",
    )


@router.post(
    "/{incident_id}",
    response_model=InvestigationResponse,
)
async def investigate_incident(incident_id: str):
    incident = load_incident(incident_id)

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident_context = f"""
Incident ID: {incident.incident_id}
Service: {incident.service}
Severity: {incident.severity}
Title: {incident.title}
Description: {incident.description}
Started at: {incident.started_at}
Resolved at: {incident.resolved_at}
Symptoms: {", ".join(incident.symptoms)}
"""

    initial_state = {
        "messages": [HumanMessage(content=incident_context)],
        "report": None,
        "iterations": 0,
        "incident_id": incident.incident_id,
    }

    try:
        result = graph.invoke(initial_state, config={"recursion_limit": 20})
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="The AI investigation service is temporarily unavailable. Please try again shortly.",
        )

    return {
        **result["report"].model_dump(mode="json"),
        "status": "completed",
    }