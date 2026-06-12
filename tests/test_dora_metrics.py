"""
Tests for DORA metrics computation (services/dora_metrics.py).
Uses an in-memory SQLite database; no running server needed.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
import pytest

from app import app, db
from models.pipeline_event import PipelineEvent
from services import dora_metrics as dm


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        # Dispose existing engine so Flask-SQLAlchemy picks up the new URI
        db.engine.dispose()
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _add_event(pipeline_id, run_id, event_type, event_time):
    e = PipelineEvent(
        pipeline_id=pipeline_id,
        run_id=run_id,
        event_type=event_type,
        event_time=event_time,
    )
    db.session.add(e)
    db.session.commit()
    return e


# ---------------------------------------------------------------------------
# Deployment Frequency
# ---------------------------------------------------------------------------

def test_deployment_frequency_empty(client):
    with app.app_context():
        result = dm.deployment_frequency()
    assert result['total_deployments'] == 0
    assert result['per_day'] == 0.0
    assert result['rating'] == 'Low'


def test_deployment_frequency_counts(client):
    now = datetime.utcnow()
    with app.app_context():
        for i in range(5):
            _add_event('pipe-a', f'run-{i}', 'deploy_success',
                       now - timedelta(days=i))
        result = dm.deployment_frequency(now - timedelta(days=30), now)
    assert result['total_deployments'] == 5


# ---------------------------------------------------------------------------
# Lead Time for Change
# ---------------------------------------------------------------------------

def test_lead_time_no_data(client):
    with app.app_context():
        result = dm.lead_time_for_change()
    assert result['samples'] == 0
    assert result['avg_minutes'] is None


def test_lead_time_calculation(client):
    now = datetime.utcnow()
    with app.app_context():
        _add_event('pipe-b', 'run-1', 'build_start',    now - timedelta(minutes=30))
        _add_event('pipe-b', 'run-1', 'deploy_success', now)
        result = dm.lead_time_for_change(now - timedelta(days=1), now)
    assert result['samples'] == 1
    assert abs(result['avg_minutes'] - 30.0) < 0.1


def test_lead_time_out_of_order_event(client):
    """Event-time semantics: even if ingested late, event_time is used."""
    now = datetime.utcnow()
    with app.app_context():
        # Ingest deploy first, then build_start (simulating out-of-order ingestion)
        _add_event('pipe-c', 'run-2', 'deploy_success', now)
        _add_event('pipe-c', 'run-2', 'build_start',    now - timedelta(minutes=45))
        result = dm.lead_time_for_change(now - timedelta(days=1), now)
    assert result['samples'] == 1
    assert abs(result['avg_minutes'] - 45.0) < 0.1


# ---------------------------------------------------------------------------
# Change Failure Rate
# ---------------------------------------------------------------------------

def test_cfr_zero_when_empty(client):
    with app.app_context():
        result = dm.change_failure_rate()
    assert result['rate_pct'] == 0.0


def test_cfr_calculation(client):
    now = datetime.utcnow()
    with app.app_context():
        for i in range(8):
            _add_event('pipe-d', f'run-{i}', 'deploy_success', now - timedelta(hours=i))
        for i in range(2):
            _add_event('pipe-d', f'run-fail-{i}', 'deploy_failure', now - timedelta(hours=i+10))
        result = dm.change_failure_rate(now - timedelta(days=1), now)
    # 2 failures / 10 total = 20 %
    assert result['rate_pct'] == 20.0
    assert result['rating'] == 'Low'


# ---------------------------------------------------------------------------
# Mean Time to Restore
# ---------------------------------------------------------------------------

def test_mttr_no_failures(client):
    with app.app_context():
        result = dm.mean_time_to_restore()
    assert result['samples'] == 0
    assert result['avg_minutes'] is None


def test_mttr_calculation(client):
    now = datetime.utcnow()
    with app.app_context():
        _add_event('pipe-e', 'run-fail', 'deploy_failure', now - timedelta(minutes=60))
        _add_event('pipe-e', 'run-fix',  'deploy_success', now - timedelta(minutes=20))
        result = dm.mean_time_to_restore(now - timedelta(days=1), now)
    assert result['samples'] == 1
    assert abs(result['avg_minutes'] - 40.0) < 0.1
    assert result['rating'] == 'Elite'
