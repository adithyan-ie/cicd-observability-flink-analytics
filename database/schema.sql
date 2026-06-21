CREATE TABLE IF NOT EXISTS pipeline_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE,
    pipeline_id VARCHAR(100) NOT NULL,
    repository_id VARCHAR(100),
    run_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    processing_timestamp TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(30) DEFAULT 'SUCCESS',
    commit_hash VARCHAR(40)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_event_time ON pipeline_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_repository_time ON pipeline_events(repository_id, event_timestamp);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_run ON pipeline_events(run_id);

CREATE TABLE IF NOT EXISTS dora_metrics (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    repository_id VARCHAR(100),
    deployment_frequency BIGINT NOT NULL DEFAULT 0,
    failed_deployments BIGINT NOT NULL DEFAULT 0,
    total_deployments BIGINT NOT NULL DEFAULT 0,
    change_failure_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
    lead_time_minutes DOUBLE PRECISION,
    mttr_minutes DOUBLE PRECISION,
    metric_available_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    repository_id VARCHAR(100),
    deployment_frequency DOUBLE PRECISION,
    lead_time DOUBLE PRECISION,
    mttr DOUBLE PRECISION,
    failure_rate DOUBLE PRECISION,
    recent_incidents INTEGER,
    risk_score DOUBLE PRECISION NOT NULL,
    prediction VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

