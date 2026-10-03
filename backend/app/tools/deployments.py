import json
from pathlib import Path

from langchain_core.tools import tool


DEPLOYMENTS_FILE = Path("data/deployments.json")


@tool
def search_deployments(
    service: str,
    version: str | None = None,
) -> list[dict]:
    """Search deployment history for the incident's affected service.

    Use the exact service name from the incident. If no deployments are
    returned, treat that as missing deployment evidence rather than
    searching an unrelated service.
    """

    if not DEPLOYMENTS_FILE.exists():
        return []

    with DEPLOYMENTS_FILE.open() as file:
        deployments = json.load(file)

    results = [
        deployment
        for deployment in deployments
        if deployment["service"] == service
    ]

    if version:
        results = [
            deployment
            for deployment in results
            if deployment["version"] == version
        ]

    return results