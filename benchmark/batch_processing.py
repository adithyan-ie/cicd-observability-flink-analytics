from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.event_schema import CICDEvent
from services.streaming_metrics import compute_dora_from_events


def load_events(path: str) -> list[dict]:
    events = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        event = CICDEvent.from_dict(json.loads(line))
        events.append(
            {
                "pipeline_id": event.pipeline_id,
                "run_id": event.run_id,
                "event_type": event.event_type,
                "event_time": event.event_timestamp,
            }
        )
    return events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="database/sample_cicd_events.jsonl")
    parser.add_argument("--output", default="benchmark/batch_metrics.json")
    args = parser.parse_args()
    metrics = compute_dora_from_events(load_events(args.input))
    Path(args.output).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
