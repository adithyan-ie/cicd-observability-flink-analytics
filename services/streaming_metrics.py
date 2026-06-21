from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean, median


def compute_dora_from_events(events: list[dict]) -> dict:
    """Pure DORA calculator used by tests, benchmarks, and stream snapshots."""
    ordered = sorted(events, key=lambda e: e["event_time"])
    deploy_success = [e for e in ordered if e["event_type"] == "deploy_success"]
    deploy_failed = [e for e in ordered if e["event_type"] == "deploy_failure"]
    rollbacks = [e for e in ordered if e["event_type"] == "rollback"]
    incident_opened = [e for e in ordered if e["event_type"] == "incident_opened"]
    incident_resolved = [e for e in ordered if e["event_type"] == "incident_resolved"]

    by_run = defaultdict(list)
    for event in ordered:
        by_run[event.get("run_id")].append(event)

    lead_times = []
    for run_events in by_run.values():
        starts = [e for e in run_events if e["event_type"] == "build_start"]
        deploys = [e for e in run_events if e["event_type"] == "deploy_success"]
        if starts and deploys:
            delta = (min(d["event_time"] for d in deploys) - min(s["event_time"] for s in starts)).total_seconds() / 60
            if delta >= 0:
                lead_times.append(delta)

    by_pipeline = defaultdict(list)
    for event in ordered:
        by_pipeline[event.get("pipeline_id")].append(event)

    mttr = []
    for pipeline_events in by_pipeline.values():
        for failure in [e for e in pipeline_events if e["event_type"] in {"deploy_failure", "rollback", "incident_opened"}]:
            recovery_type = "incident_resolved" if failure["event_type"] == "incident_opened" else "deploy_success"
            recoveries = [
                e for e in pipeline_events
                if e["event_type"] == recovery_type and e["event_time"] > failure["event_time"]
            ]
            if recoveries:
                mttr.append((min(e["event_time"] for e in recoveries) - failure["event_time"]).total_seconds() / 60)

    if ordered:
        days = max((ordered[-1]["event_time"] - ordered[0]["event_time"]).total_seconds() / 86400, 1 / 24)
    else:
        days = 1
    total_deployments = len(deploy_success) + len(deploy_failed) + len(rollbacks)

    return {
        "computed_at": datetime.utcnow().isoformat() + "Z",
        "deployment_frequency": {
            "successful_deployments": len(deploy_success),
            "per_day": round(len(deploy_success) / days, 4),
        },
        "lead_time_for_changes": {
            "samples": len(lead_times),
            "avg_minutes": round(mean(lead_times), 2) if lead_times else None,
            "median_minutes": round(median(lead_times), 2) if lead_times else None,
        },
        "change_failure_rate": {
            "failed_deployments": len(deploy_failed) + len(rollbacks),
            "total_deployments": total_deployments,
            "rate_pct": round(((len(deploy_failed) + len(rollbacks)) / total_deployments) * 100, 2)
            if total_deployments else 0.0,
        },
        "mean_time_to_recovery": {
            "samples": len(mttr),
            "avg_minutes": round(mean(mttr), 2) if mttr else None,
        },
    }
