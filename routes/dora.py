from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, abort
from flask_login import login_required

from extensions import db
from models.pipeline_event import PipelineEvent
from services.dora_metrics import all_dora_metrics

dora_bp = Blueprint('dora', __name__, url_prefix='/dora')


# ---------------------------------------------------------------------------
# Dashboard (HTML)
# ---------------------------------------------------------------------------

@dora_bp.route('/')
@login_required
def dashboard():
    metrics = all_dora_metrics()
    recent_events = (
        PipelineEvent.query
        .order_by(PipelineEvent.event_time.desc())
        .limit(20)
        .all()
    )
    return render_template('dora_dashboard.html',
                           metrics=metrics,
                           recent_events=recent_events)


# ---------------------------------------------------------------------------
# JSON API – all metrics
# ---------------------------------------------------------------------------

@dora_bp.route('/api/metrics')
@login_required
def api_metrics():
    """
    GET /dora/api/metrics
    Optional query params: start=<ISO datetime>, end=<ISO datetime>
    """
    start = end = None
    try:
        if request.args.get('start'):
            start = datetime.fromisoformat(request.args['start'])
        if request.args.get('end'):
            end = datetime.fromisoformat(request.args['end'])
    except ValueError:
        abort(400, description='Invalid datetime format. Use ISO 8601.')

    return jsonify(all_dora_metrics(start, end))


# ---------------------------------------------------------------------------
# Event ingestion endpoint
# ---------------------------------------------------------------------------

@dora_bp.route('/api/events', methods=['POST'])
@login_required
def ingest_event():
    """
    POST /dora/api/events
    Body (JSON):
        {
            "pipeline_id": "my-service",
            "run_id":      "run-1234",
            "event_type":  "deploy_success",
            "commit_hash": "abc123",       (optional)
            "event_time":  "2024-01-01T12:00:00"  (optional, defaults to now)
        }
    """
    data = request.get_json(silent=True)
    if not data:
        abort(400, description='JSON body required.')

    required = ('pipeline_id', 'run_id', 'event_type')
    missing  = [f for f in required if not data.get(f)]
    if missing:
        abort(400, description=f'Missing required fields: {", ".join(missing)}')

    if data['event_type'] not in PipelineEvent.EVENT_TYPES:
        abort(400, description=(
            f'Unknown event_type "{data["event_type"]}". '
            f'Valid types: {PipelineEvent.EVENT_TYPES}'
        ))

    event_time = datetime.utcnow()
    if data.get('event_time'):
        try:
            event_time = datetime.fromisoformat(data['event_time'])
        except ValueError:
            abort(400, description='event_time must be ISO 8601.')

    event = PipelineEvent(
        pipeline_id = data['pipeline_id'],
        run_id      = data['run_id'],
        event_type  = data['event_type'],
        commit_hash = data.get('commit_hash'),
        event_time  = event_time,
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({'status': 'created', 'event': event.to_dict()}), 201


# ---------------------------------------------------------------------------
# Bulk event ingestion (simulate a pipeline run)
# ---------------------------------------------------------------------------

@dora_bp.route('/api/events/bulk', methods=['POST'])
@login_required
def ingest_bulk_events():
    """
    POST /dora/api/events/bulk
    Body (JSON): list of event objects (same schema as single ingest)
    """
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        abort(400, description='JSON array of event objects required.')

    created = []
    for idx, item in enumerate(data):
        if item.get('event_type') not in PipelineEvent.EVENT_TYPES:
            abort(400, description=f'Item {idx}: unknown event_type "{item.get("event_type")}"')

        event_time = datetime.utcnow()
        if item.get('event_time'):
            try:
                event_time = datetime.fromisoformat(item['event_time'])
            except ValueError:
                abort(400, description=f'Item {idx}: invalid event_time format.')

        event = PipelineEvent(
            pipeline_id = item.get('pipeline_id', ''),
            run_id      = item.get('run_id', ''),
            event_type  = item['event_type'],
            commit_hash = item.get('commit_hash'),
            event_time  = event_time,
        )
        db.session.add(event)
        created.append(event)

    db.session.commit()
    return jsonify({'status': 'created', 'count': len(created)}), 201
