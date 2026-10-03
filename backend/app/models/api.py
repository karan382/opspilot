from pydantic import Field

from app.models.investigation import InvestigationReport


class InvestigationResponse(InvestigationReport):
    """API response for an incident investigation."""

    status: str = Field(default="completed")