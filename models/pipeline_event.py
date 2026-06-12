from datetime import datetime
from extensions import db


class PipelineEvent(db.Model):
    """
    Represents a single CI/CD pipeline event.

    Event-type vocabulary
    ---------------------
    build_start      - pipeline build kicked off
    build_success    - build completed successfully
    build_failure    - build failed
    test_start       - test suite started
    test_pass        - all tests passed
    test_fail        - one or more tests failed
    deploy_start     - deployment kicked off
    deploy_success   - deployment completed successfully
    deploy_failure   - deployment failed
    rollback         - a rollback was executed
    """

    EVENT_TYPES = [
        'build_start', 'build_success', 'build_failure',
        'test_start', 'test_pass', 'test_fail',
        'deploy_start', 'deploy_success', 'deploy_failure',
        'rollback',
    ]

    id          = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.String(100), nullable=False, index=True)
    run_id      = db.Column(db.String(100), nullable=False, index=True)
    event_type  = db.Column(db.String(30), nullable=False)
    commit_hash = db.Column(db.String(40))
    # event_time: the time the event actually occurred in the pipeline (event-time semantics)
    event_time  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # ingested_at: the time the event was received by this system (processing-time)
    ingested_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          self.id,
            'pipeline_id': self.pipeline_id,
            'run_id':      self.run_id,
            'event_type':  self.event_type,
            'commit_hash': self.commit_hash,
            'event_time':  self.event_time.isoformat() if self.event_time else None,
            'ingested_at': self.ingested_at.isoformat() if self.ingested_at else None,
        }

    def __repr__(self):
        return f'<PipelineEvent {self.pipeline_id}/{self.run_id} [{self.event_type}]>'
