from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, abort

from extensions import db
from models.pipeline_event import PipelineEvent
from services.alert_engine import generate_alerts
from services.dora_metrics import all_dora_metrics
from services.event_schema import CICDEvent
from services.prediction import DeploymentRiskFeatures, DeploymentRiskPredictor


observability_bp = Blueprint("observability", __name__, url_prefix="/api/observability")
predictor = DeploymentRiskPredictor()


@observability_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "cicd-observability"})


@observability_bp.get("/metrics/live")
def live_metrics():
    return jsonify(all_dora_metrics())


@observability_bp.post("/events")
def ingest_stream_event():
    payload = request.get_json(silent=True)
    if not payload:
        abort(400, description="JSON body required.")
    event = CICDEvent.from_dict(payload)
    row = PipelineEvent(
        event_id=event.event_id,
        pipeline_id=event.pipeline_id,
        repository_id=event.repository_id,
        run_id=event.run_id or event.event_id,
        event_type=event.event_type,
        status=event.status,
        commit_hash=event.commit_hash,
        event_time=event.event_timestamp,
        ingested_at=event.processing_timestamp,
    )
    db.session.add(row)
    db.session.commit()
    return jsonify({"status": "created", "event": row.to_dict()}), 201


@observability_bp.get("/alerts")
def alerts():
    metrics = _current_stream_metrics()
    previous = _previous_stream_metrics()
    return jsonify({"alerts": generate_alerts(metrics, previous)})


@observability_bp.get("/prediction")
def prediction():
    metrics = _current_stream_metrics()
    failure_rate = metrics["change_failure_rate"]["rate_pct"]
    lead_time = metrics["lead_time_for_changes"]["avg_minutes"] or 0
    mttr = metrics["mean_time_to_recovery"]["avg_minutes"] or 0
    deploy_frequency = metrics["deployment_frequency"]["per_day"]
    recent_incidents = PipelineEvent.query.filter(
        PipelineEvent.event_type == "incident_opened",
        PipelineEvent.event_time >= datetime.utcnow() - timedelta(days=7),
    ).count()
    return jsonify(
        predictor.predict(
            DeploymentRiskFeatures(
                deployment_frequency=deploy_frequency,
                lead_time=lead_time,
                mttr=mttr,
                failure_rate=failure_rate,
                recent_incidents=recent_incidents,
            )
        )
    )


def _current_stream_metrics() -> dict:
    metrics = all_dora_metrics()
    return {
        "deployment_frequency": {"per_day": metrics["deployment_frequency"]["per_day"]},
        "lead_time_for_changes": {"avg_minutes": metrics["lead_time_for_change"]["avg_minutes"]},
        "change_failure_rate": {"rate_pct": metrics["change_failure_rate"]["rate_pct"]},
        "mean_time_to_recovery": {"avg_minutes": metrics["mean_time_to_restore"]["avg_minutes"]},
    }


def _previous_stream_metrics() -> dict:
    end = datetime.utcnow() - timedelta(days=30)
    start = end - timedelta(days=30)
    metrics = all_dora_metrics(start, end)
    return {"deployment_frequency": {"per_day": metrics["deployment_frequency"]["per_day"]}}

