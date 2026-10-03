import json
from pathlib import Path

from langchain_core.tools import tool

from app.models.log import LogEntry


LOGS_DIR = Path("data/logs")


@tool
def search_logs(service: str, keyword: str | None = None) -> list[dict]:
    """Search application logs for the incident's affected service.

    Use the exact service name from the incident when calling this tool.
    If no logs are returned, treat that as missing evidence rather than
    searching an unrelated service.
    """

    log_file = LOGS_DIR / f"{service}.jsonl"

    if not log_file.exists():
        return []

    results = []

    with log_file.open() as file:
        for line in file:
            data = json.loads(line)

            log = LogEntry(
                timestamp=data["timestamp"],
                level=data["level"],
                service=data["service"],
                message=data["message"],
                metadata={
                    key: value
                    for key, value in data.items()
                    if key not in {"timestamp", "level", "service", "message"}
                },
            )

            if keyword:
                normalized_message = log.message.lower().replace(
                    "timed out", "timeout"
                )

                if keyword.lower() not in normalized_message:
                    continue

            results.append(log.model_dump(mode="json"))

    return results