from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


EVENT_TYPE_MAP = {
    "BUILD_STARTED": "build_start",
    "BUILD_COMPLETED": "build_success",
    "TEST_STARTED": "test_start",
    "TEST_COMPLETED": "test_pass",
    "DEPLOYMENT_STARTED": "deploy_start",
    "DEPLOYMENT_COMPLETED": "deploy_success",
    "DEPLOYMENT_FAILED": "deploy_failure",
    "ROLLBACK_TRIGGERED": "rollback",
    "INCIDENT_OPENED": "incident_opened",
    "INCIDENT_RESOLVED": "incident_resolved",
    "build_start": "build_start",
    "build_success": "build_success",
    "build_failure": "build_failure",
    "test_start": "test_start",
    "test_pass": "test_pass",
    "test_fail": "test_fail",
    "deploy_start": "deploy_start",
    "deploy_success": "deploy_success",
    "deploy_failure": "deploy_failure",
    "rollback": "rollback",
    "incident_opened": "incident_opened",
    "incident_resolved": "incident_resolved",
}


def parse_datetime(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


@dataclass(slots=True)
class CICDEvent:
    pipeline_id: str
    repository_id: str
    event_type: str
    event_timestamp: datetime
    processing_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    status: str = "SUCCESS"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str | None = None
    commit_hash: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CICDEvent":
        event_type = EVENT_TYPE_MAP.get(payload.get("event_type", ""), payload.get("event_type", ""))
        return cls(
            event_id=payload.get("event_id") or str(uuid4()),
            pipeline_id=payload["pipeline_id"],
            repository_id=payload.get("repository_id") or payload.get("pipeline_id", "repo_000"),
            run_id=payload.get("run_id") or payload.get("pipeline_run_id") or payload.get("event_id"),
            event_type=event_type,
            event_timestamp=parse_datetime(payload.get("event_timestamp") or payload.get("event_time")),
            processing_timestamp=parse_datetime(payload.get("processing_timestamp") or payload.get("ingested_at")),
            status=payload.get("status", "SUCCESS"),
            commit_hash=payload.get("commit_hash"),
        )

    def to_dict(self) -> dict[str, Any]:
        external_type = next((k for k, v in EVENT_TYPE_MAP.items() if v == self.event_type and k.isupper()), self.event_type)
        return {
            "event_id": self.event_id,
            "pipeline_id": self.pipeline_id,
            "repository_id": self.repository_id,
            "run_id": self.run_id,
            "event_type": external_type,
            "event_timestamp": self.event_timestamp.isoformat() + "Z",
            "processing_timestamp": self.processing_timestamp.isoformat() + "Z",
            "status": self.status,
            "commit_hash": self.commit_hash,
        }

