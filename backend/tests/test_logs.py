import json
from pathlib import Path

from app.models.log import LogEntry


LOG_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "logs"
    / "recommendation-service.jsonl"
)


with LOG_FILE.open() as file:
    for line in file:
        log = LogEntry(
            timestamp=json.loads(line)["timestamp"],
            level=json.loads(line)["level"],
            service=json.loads(line)["service"],
            message=json.loads(line)["message"],
            metadata={
                key: value
                for key, value in json.loads(line).items()
                if key not in {"timestamp", "level", "service", "message"}
            },
        )

        print(f"✓ {log.timestamp} [{log.level}] {log.message}")