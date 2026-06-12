"""
DORA Metrics Service
====================
Computes the four core DORA (DevOps Research and Assessment) metrics from
PipelineEvent records stored in the database.

Metrics
-------
1. Deployment Frequency    – how often successful deployments reach production
2. Lead Time for Change    – elapsed time from build_start → deploy_success
                             for the same run_id (event-time semantics)
3. Change Failure Rate     – % of deployments that caused a failure or rollback
4. Mean Time to Restore    – average time between deploy_failure/rollback and
                             the next deploy_success on the same pipeline

All time windows default to the last 30 days but callers can supply any
start/end datetime pair.
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from extensions import db
from models.pipeline_event import PipelineEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _default_window():
    end   = datetime.utcnow()
    start = end - timedelta(days=30)
    return start, end


def _events_in_window(event_type, start, end):
    """Return a query for events of a given type within [start, end]."""
    return (
        PipelineEvent.query
        .filter(
            PipelineEvent.event_type == event_type,
            PipelineEvent.event_time >= start,
            PipelineEvent.event_time <= end,
        )
    )


# ---------------------------------------------------------------------------
# 1. Deployment Frequency
# ---------------------------------------------------------------------------

def deployment_frequency(start=None, end=None):
    """
    Returns:
        {
            'total_deployments': int,
            'period_days':       int,
            'per_day':           float,
            'rating':            str   # Elite / High / Medium / Low
        }
    """
    if start is None or end is None:
        start, end = _default_window()

    total = _events_in_window('deploy_success', start, end).count()
    period_days = max((end - start).days, 1)
    per_day     = round(total / period_days, 4)

    # DORA band thresholds (simplified)
    if per_day >= 1:
        rating = 'Elite'      # multiple times per day / day
    elif per_day >= 1 / 7:
        rating = 'High'       # once per week
    elif per_day >= 1 / 30:
        rating = 'Medium'     # once per month
    else:
        rating = 'Low'

    return {
        'total_deployments': total,
        'period_days':       period_days,
        'per_day':           per_day,
        'rating':            rating,
    }


# ---------------------------------------------------------------------------
# 2. Lead Time for Change
# ---------------------------------------------------------------------------

def lead_time_for_change(start=None, end=None):
    """
    Measures the elapsed time from build_start to deploy_success for each run_id.
    Uses event-time (PipelineEvent.event_time) so out-of-order ingestion does not
    distort the result.

    Returns:
        {
            'samples':        int,
            'avg_minutes':    float,
            'median_minutes': float,
            'rating':         str
        }
    """
    if start is None or end is None:
        start, end = _default_window()

    # Collect deploy_success events in window
    deploys = (
        PipelineEvent.query
        .filter(
            PipelineEvent.event_type == 'deploy_success',
            PipelineEvent.event_time >= start,
            PipelineEvent.event_time <= end,
        )
        .all()
    )

    durations = []
    for deploy in deploys:
        # Find the earliest build_start for the same run_id
        build_start = (
            PipelineEvent.query
            .filter(
                PipelineEvent.run_id     == deploy.run_id,
                PipelineEvent.event_type == 'build_start',
            )
            .order_by(PipelineEvent.event_time.asc())
            .first()
        )
        if build_start and build_start.event_time < deploy.event_time:
            delta_minutes = (
                (deploy.event_time - build_start.event_time).total_seconds() / 60
            )
            durations.append(delta_minutes)

    if not durations:
        return {'samples': 0, 'avg_minutes': None,
                'median_minutes': None, 'rating': 'N/A'}

    avg    = round(sum(durations) / len(durations), 2)
    sorted_d = sorted(durations)
    mid    = len(sorted_d) // 2
    median = (
        round(sorted_d[mid], 2)
        if len(sorted_d) % 2 != 0
        else round((sorted_d[mid - 1] + sorted_d[mid]) / 2, 2)
    )

    # DORA bands (in minutes)
    if avg < 60:          # < 1 hour
        rating = 'Elite'
    elif avg < 24 * 60:   # < 1 day
        rating = 'High'
    elif avg < 7 * 24 * 60:  # < 1 week
        rating = 'Medium'
    else:
        rating = 'Low'

    return {
        'samples':        len(durations),
        'avg_minutes':    avg,
        'median_minutes': median,
        'rating':         rating,
    }


# ---------------------------------------------------------------------------
# 3. Change Failure Rate
# ---------------------------------------------------------------------------

def change_failure_rate(start=None, end=None):
    """
    CFR = (deploy_failure + rollback) / (deploy_success + deploy_failure + rollback) * 100

    Returns:
        {
            'successes':  int,
            'failures':   int,
            'rollbacks':  int,
            'rate_pct':   float,
            'rating':     str
        }
    """
    if start is None or end is None:
        start, end = _default_window()

    successes = _events_in_window('deploy_success', start, end).count()
    failures  = _events_in_window('deploy_failure', start, end).count()
    rollbacks = _events_in_window('rollback',        start, end).count()

    total = successes + failures + rollbacks
    rate  = round((failures + rollbacks) / total * 100, 2) if total > 0 else 0.0

    if rate <= 5:
        rating = 'Elite'
    elif rate <= 10:
        rating = 'High'
    elif rate <= 15:
        rating = 'Medium'
    else:
        rating = 'Low'

    return {
        'successes': successes,
        'failures':  failures,
        'rollbacks': rollbacks,
        'rate_pct':  rate,
        'rating':    rating,
    }


# ---------------------------------------------------------------------------
# 4. Mean Time to Restore (MTTR)
# ---------------------------------------------------------------------------

def mean_time_to_restore(start=None, end=None):
    """
    For each deploy_failure (or rollback) event, find the next deploy_success
    on the same pipeline_id.  MTTR is the average of those recovery durations.

    Returns:
        {
            'samples':     int,
            'avg_minutes': float,
            'rating':      str
        }
    """
    if start is None or end is None:
        start, end = _default_window()

    failure_events = (
        PipelineEvent.query
        .filter(
            PipelineEvent.event_type.in_(['deploy_failure', 'rollback']),
            PipelineEvent.event_time >= start,
            PipelineEvent.event_time <= end,
        )
        .order_by(PipelineEvent.event_time.asc())
        .all()
    )

    recovery_times = []
    for failure in failure_events:
        # Next deploy_success on the same pipeline after the failure event_time
        recovery = (
            PipelineEvent.query
            .filter(
                PipelineEvent.pipeline_id == failure.pipeline_id,
                PipelineEvent.event_type  == 'deploy_success',
                PipelineEvent.event_time  >  failure.event_time,
            )
            .order_by(PipelineEvent.event_time.asc())
            .first()
        )
        if recovery:
            delta_minutes = (
                (recovery.event_time - failure.event_time).total_seconds() / 60
            )
            recovery_times.append(delta_minutes)

    if not recovery_times:
        return {'samples': 0, 'avg_minutes': None, 'rating': 'N/A'}

    avg = round(sum(recovery_times) / len(recovery_times), 2)

    # DORA bands (in minutes)
    if avg < 60:               # < 1 hour
        rating = 'Elite'
    elif avg < 24 * 60:        # < 1 day
        rating = 'High'
    elif avg < 7 * 24 * 60:   # < 1 week
        rating = 'Medium'
    else:
        rating = 'Low'

    return {
        'samples':     len(recovery_times),
        'avg_minutes': avg,
        'rating':      rating,
    }


# ---------------------------------------------------------------------------
# Aggregate helper – all four metrics in one call
# ---------------------------------------------------------------------------

def all_dora_metrics(start=None, end=None):
    """Return a dict containing all four DORA metrics."""
    if start is None or end is None:
        start, end = _default_window()
    return {
        'window': {
            'start': start.isoformat(),
            'end':   end.isoformat(),
        },
        'deployment_frequency':  deployment_frequency(start, end),
        'lead_time_for_change':  lead_time_for_change(start, end),
        'change_failure_rate':   change_failure_rate(start, end),
        'mean_time_to_restore':  mean_time_to_restore(start, end),
    }
