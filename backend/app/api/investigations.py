from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agents.graph import graph
from app.models.incident import Incident
from app.models.api import InvestigationResponse

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

from datetime import datetime, timezone

from app.models.database import IncidentDB, InvestigationRunDB, InvestigationEvidenceDB

import json

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


def load_incident(incident_id: str) -> Incident | None:
    with SessionLocal() as session:
        incident = session.get(IncidentDB, incident_id)

        if incident is None:
            return None

        return Incident(
            incident_id=incident.incident_id,
            service=incident.service,
            severity=incident.severity,
            title=incident.title,
            description=incident.description,
            started_at=incident.started_at,
            resolved_at=incident.resolved_at,
            symptoms=incident.symptoms,
        )


@router.get("/{incident_id}/history")
async def investigation_history(incident_id: str):
    with SessionLocal() as session:
        incident = session.get(IncidentDB, incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        investigations = (
            session.query(InvestigationRunDB)
            .filter(InvestigationRunDB.incident_id == incident_id)
            .order_by(InvestigationRunDB.started_at.desc())
            .all()
        )

        history = []

        for investigation in investigations:
            evidence = (
                session.query(InvestigationEvidenceDB)
                .filter(
                    InvestigationEvidenceDB.investigation_id
                    == investigation.id
                )
                .order_by(InvestigationEvidenceDB.id)
                .all()
            )

            history.append(
                {
                    "id": investigation.id,
                    "incident_id": investigation.incident_id,
                    "status": investigation.status,
                    "started_at": investigation.started_at,
                    "completed_at": investigation.completed_at,
                    "summary": investigation.summary,
                    "confidence": investigation.confidence,
                    "claim_level": investigation.claim_level,
                    "evidence": [
                        {
                            "id": item.id,
                            "source": item.source,
                            "source_type": item.source_type,
                            "service": item.service,
                            "timestamp": item.timestamp,
                            "observation": item.observation,
                            "description": item.description,
                            "chunk_index": item.chunk_index,
                        }
                        for item in evidence
                    ],
                }
            )

        return {
            "incident_id": incident_id,
            "investigations": history,
        }


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
            tools_data = event["tools"]
            messages = tools_data.get("messages", [])

            for message in messages:
                tool_name = getattr(message, "name", None)

                if tool_name:
                    yield json.dumps({
                        "type": "tool",
                        "tool": tool_name,
                        "status": "completed",
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

    started_at = datetime.now(timezone.utc)

    try:
        result = graph.invoke(initial_state, config={"recursion_limit": 20})
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="The AI investigation service is temporarily unavailable. Please try again shortly.",
        )

    report = result["report"]
    completed_at = datetime.now(timezone.utc)

    with SessionLocal() as session:
        investigation = InvestigationRunDB(
            incident_id=incident.incident_id,
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            summary=report.summary,
            confidence=report.root_cause.confidence,
            claim_level=report.root_cause.claim_level,
        )

        session.add(investigation)
        session.flush()

        for evidence in report.evidence:
            session.add(
                InvestigationEvidenceDB(
                    investigation_id=investigation.id,
                    source=evidence.source,
                    source_type=evidence.source_type,
                    service=evidence.service,
                    timestamp=evidence.timestamp,
                    observation=evidence.observation,
                    description=evidence.description,
                    chunk_index=evidence.chunk_index,
                )
            )

        session.commit()
    
    return {
        **report.model_dump(mode="json"),
        "status": "completed",
    }