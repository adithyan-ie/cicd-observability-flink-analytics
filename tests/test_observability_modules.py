from datetime import datetime, timedelta

from services.alert_engine import generate_alerts
from services.event_schema import CICDEvent
from services.prediction import DeploymentRiskFeatures, DeploymentRiskPredictor
from services.streaming_metrics import compute_dora_from_events


def test_cicd_event_normalizes_prompt_schema():
    event = CICDEvent.from_dict(
        {
            "event_id": "evt-1",
            "pipeline_id": "pipeline_001",
            "repository_id": "repo_001",
            "event_type": "DEPLOYMENT_COMPLETED",
            "event_timestamp": "2026-01-01T12:00:00Z",
            "processing_timestamp": "2026-01-01T12:00:02Z",
            "status": "SUCCESS",
        }
    )

    assert event.event_type == "deploy_success"
    assert event.pipeline_id == "pipeline_001"


def test_streaming_metrics_handle_out_of_order_events():
    now = datetime.utcnow()
    events = [
        {"pipeline_id": "p1", "run_id": "r1", "event_type": "deploy_success", "event_time": now},
        {"pipeline_id": "p1", "run_id": "r1", "event_type": "build_start", "event_time": now - timedelta(minutes=20)},
        {"pipeline_id": "p1", "run_id": "r2", "event_type": "deploy_failure", "event_time": now - timedelta(minutes=10)},
    ]

    metrics = compute_dora_from_events(events)

    assert metrics["lead_time_for_changes"]["avg_minutes"] == 20
    assert metrics["change_failure_rate"]["rate_pct"] == 50


def test_alert_rules_and_prediction_fallback():
    metrics = {
        "deployment_frequency": {"per_day": 1},
        "change_failure_rate": {"rate_pct": 35},
        "mean_time_to_recovery": {"avg_minutes": 45},
    }
    previous = {"deployment_frequency": {"per_day": 3}}

    alerts = generate_alerts(metrics, previous)
    prediction = DeploymentRiskPredictor().predict(
        DeploymentRiskFeatures(
            deployment_frequency=1,
            lead_time=180,
            mttr=45,
            failure_rate=35,
            recent_incidents=4,
        )
    )

    assert {alert["name"] for alert in alerts} == {
        "High Deployment Risk",
        "Recovery SLA Breach",
        "Pipeline Slowdown",
    }
    assert 0 <= prediction["risk_score"] <= 1

