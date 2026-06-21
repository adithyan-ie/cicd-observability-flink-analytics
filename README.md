# Real-Time CI/CD Observability and Predictive Analytics Framework

Production-oriented demo platform for CI/CD observability using Kafka, Flink,
DORA metrics, predictive deployment risk scoring, PostgreSQL, React, Prometheus,
and Grafana.

## What Is Included

- Synthetic CI/CD event generator with delayed and out-of-order events.
- Kafka topics for `cicd-events`, `dora-metrics`, and `alerts`.
- PyFlink streaming job with event-time processing, sliding windows, tumbling-ready SQL, and five-minute watermark lateness.
- DORA metric calculators for deployment frequency, lead time, change failure rate, and MTTR.
- Alert rules for high deployment risk, recovery SLA breaches, and pipeline slowdown.
- RandomForest-compatible predictive analytics module with deterministic fallback.
- Flask observability API plus the existing incident/DORA dashboard.
- React + Material UI + Recharts dashboard.
- PostgreSQL schema, Dockerfile, Docker Compose, Prometheus, and Grafana dashboard stub.
- Batch baseline and benchmark runner with latency, throughput, accuracy, and predictive effectiveness reporting.

## Start The Stack

```bash
docker-compose up -d
```

Services:

- Backend API: http://localhost:5000
- React dashboard: http://localhost:3000
- Kafka UI: http://localhost:8080
- Flink UI: http://localhost:8081
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Kafka Topic Commands

```bash
docker-compose exec kafka kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists --topic cicd-events --partitions 6 --replication-factor 1
docker-compose exec kafka kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists --topic dora-metrics --partitions 3 --replication-factor 1
docker-compose exec kafka kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists --topic alerts --partitions 3 --replication-factor 1
docker-compose exec kafka kafka-topics --bootstrap-server kafka:29092 --list
docker-compose exec kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic cicd-events --from-beginning
```

## Generate Events

Write 100,000 events to a JSONL sample file:

```bash
python kafka/event_generator/generator.py --count 100000
```

Produce directly to Kafka:

```bash
python kafka/event_generator/generator.py --count 100000 --to-kafka --rate 1000
```

## Run Benchmarks

```bash
python benchmark/batch_processing.py --input database/sample_cicd_events.jsonl
python benchmark/benchmark_runner.py --input database/sample_cicd_events.jsonl --iterations 10
```

Reports are written under `benchmark/`.

## API Endpoints

- `GET /api/observability/health`
- `GET /api/observability/metrics/live`
- `POST /api/observability/events`
- `GET /api/observability/alerts`
- `GET /api/observability/prediction`

Example event:

```json
{
  "event_id": "evt-001",
  "pipeline_id": "pipeline_001",
  "repository_id": "repo_001",
  "event_type": "BUILD_STARTED",
  "event_timestamp": "2026-01-01T12:00:00Z",
  "processing_timestamp": "2026-01-01T12:00:02Z",
  "status": "SUCCESS"
}
```

## Tests

```bash
python -m pytest
```

Current suite covers DORA metric calculations, out-of-order event handling,
alert rules, event-schema normalization, and prediction output bounds.

## Project Map

- `kafka/event_generator/` synthetic event generation and Kafka publishing.
- `flink/jobs/` PyFlink SQL streaming job.
- `services/` shared metric, schema, alert, and prediction logic.
- `backend/api/` Flask JSON API for observability views.
- `frontend/` React dashboard.
- `database/schema.sql` PostgreSQL tables.
- `benchmark/` batch baseline and benchmark runner.
- `monitoring/` Prometheus and Grafana assets.
- `docs/architecture.md` architecture diagram.
- `docs/performance_evaluation_report.md` evaluation template.

