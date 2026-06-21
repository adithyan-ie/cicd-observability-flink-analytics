from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.event_schema import CICDEvent

EVENT_SEQUENCE = [
    ("BUILD_STARTED", "SUCCESS", 0),
    ("BUILD_COMPLETED", "SUCCESS", 5),
    ("TEST_STARTED", "SUCCESS", 6),
    ("TEST_COMPLETED", "SUCCESS", 12),
    ("DEPLOYMENT_STARTED", "SUCCESS", 15),
]


def generate_events(count: int = 100_000, repositories: int = 20, pipelines: int = 250) -> list[dict]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    events: list[dict] = []
    while len(events) < count:
        repo = f"repo_{random.randint(1, repositories):03d}"
        pipeline = f"pipeline_{random.randint(1, pipelines):03d}"
        run_id = f"{pipeline}-{uuid4().hex[:10]}"
        start = now - timedelta(minutes=random.randint(0, 60 * 24 * 30))
        failure = random.random() < 0.14
        for event_type, status, offset in EVENT_SEQUENCE:
            events.append(_event(repo, pipeline, run_id, event_type, status, start + timedelta(minutes=offset)))
        if failure:
            events.append(_event(repo, pipeline, run_id, "DEPLOYMENT_FAILED", "FAILED", start + timedelta(minutes=18)))
            if random.random() < 0.55:
                events.append(_event(repo, pipeline, run_id, "ROLLBACK_TRIGGERED", "FAILED", start + timedelta(minutes=35)))
            if random.random() < 0.45:
                incident_id = f"incident-{uuid4().hex[:8]}"
                opened = start + timedelta(minutes=22)
                events.append(_event(repo, pipeline, incident_id, "INCIDENT_OPENED", "FAILED", opened))
                events.append(_event(repo, pipeline, incident_id, "INCIDENT_RESOLVED", "SUCCESS", opened + timedelta(minutes=random.randint(10, 180))))
        else:
            events.append(_event(repo, pipeline, run_id, "DEPLOYMENT_COMPLETED", "SUCCESS", start + timedelta(minutes=20)))
    events = events[:count]
    for event in random.sample(events, k=max(1, len(events) // 12)):
        event["processing_timestamp"] = (
            datetime.fromisoformat(event["event_timestamp"].replace("Z", ""))
            + timedelta(minutes=random.randint(1, 15))
        ).isoformat() + "Z"
    random.shuffle(events)
    return events


def _event(repo: str, pipeline: str, run_id: str, event_type: str, status: str, event_time: datetime) -> dict:
    processing_delay = random.choice([1, 2, 3, 5, 30, 120])
    return CICDEvent(
        event_id=str(uuid4()),
        repository_id=repo,
        pipeline_id=pipeline,
        run_id=run_id,
        event_type=event_type,
        event_timestamp=event_time,
        processing_timestamp=event_time + timedelta(seconds=processing_delay),
        status=status,
        commit_hash=uuid4().hex[:12],
    ).to_dict()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--output", default="database/sample_cicd_events.jsonl")
    parser.add_argument("--to-kafka", action="store_true")
    parser.add_argument("--rate", type=int, default=1000)
    args = parser.parse_args()
    events = generate_events(args.count)
    if args.to_kafka:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from producer.producer import build_producer

        producer = build_producer()
        for idx, event in enumerate(events, 1):
            producer.send("cicd-events", key=event["pipeline_id"], value=event)
            if idx % args.rate == 0:
                producer.flush()
                time.sleep(1)
        producer.flush()
    else:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")
        print(f"Wrote {len(events)} events to {path}")


if __name__ == "__main__":
    main()
