from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str
    source_type: str
    description: str
    timestamp: str | None = None
    observation: str | None = None
    service: str | None = None
    chunk_index: int | None = None


class RootCause(BaseModel):
    hypothesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    claim_level: str


class InvestigationReport(BaseModel):
    incident_id: str | None = None
    summary: str
    timeline: list[str]
    evidence: list[Evidence]
    root_cause: RootCause
    recommendations: list[str]
    uncertainties: list[str]