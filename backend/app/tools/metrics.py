import json
from pathlib import Path

from langchain_core.tools import tool


METRICS_DIR = Path("data/metrics")


@tool
def query_metrics(service: str) -> list[dict]:
    """Query metrics for the incident's affected service.

    Use the exact service name from the incident. If no metrics are
    returned, treat that as missing telemetry rather than querying an
    unrelated service.
    """

    metrics_file = METRICS_DIR / f"{service}.json"

    if not metrics_file.exists():
        return []

    with metrics_file.open() as file:
        metrics = json.load(file)

    return [
        metric
        for metric in metrics
        if metric["service"] == service
    ]