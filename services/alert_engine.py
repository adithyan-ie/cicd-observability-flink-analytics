from __future__ import annotations

from datetime import datetime
from uuid import uuid4


def generate_alerts(metrics: dict, previous_metrics: dict | None = None) -> list[dict]:
    alerts: list[dict] = []
    failure_rate = metrics.get("change_failure_rate", {}).get("rate_pct") or 0
    mttr = metrics.get("mean_time_to_recovery", {}).get("avg_minutes")
    deploy_frequency = metrics.get("deployment_frequency", {}).get("per_day") or 0
    previous_frequency = (previous_metrics or {}).get("deployment_frequency", {}).get("per_day") or 0

    if failure_rate > 20:
        alerts.append(_alert("High Deployment Risk", "CRITICAL", f"Change failure rate is {failure_rate}%"))
    if mttr is not None and mttr > 30:
        alerts.append(_alert("Recovery SLA Breach", "HIGH", f"MTTR is {mttr} minutes"))
    if previous_frequency > 0 and deploy_frequency <= previous_frequency * 0.5:
        alerts.append(_alert("Pipeline Slowdown", "MEDIUM", "Deployment frequency dropped by at least 50%"))
    return alerts


def _alert(name: str, severity: str, description: str) -> dict:
    return {
        "alert_id": str(uuid4()),
        "name": name,
        "severity": severity,
        "description": description,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "ACTIVE",
    }

