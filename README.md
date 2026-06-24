# Real-Time CI/CD Observability and Predictive Analytics Framework

Observability platform for CI/CD pipelines using Kafka, Flink, DORA metrics,
predictive deployment risk scoring, PostgreSQL, React, Prometheus, and Grafana.

The synthetic event log generator has been extracted into the sibling project:

```text
../event-log-generation
```

## Start The Stack

```bash
docker-compose up -d
```

Services:

- Backend API: http://localhost:5000
- React dashboard: http://localhost:3000
- Kafka UI: http://localhost:8080
- Flink UI: http://localhost:8081
- Jenkins: http://localhost:8082
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

## Event Source

Use the separate `event-log-generation` project to generate JSONL samples or
publish synthetic CI/CD events to the `cicd-events` Kafka topic.

## API Endpoints

- `GET /api/observability/health`
- `GET /api/observability/metrics/live`
- `POST /api/observability/events`
- `GET /api/observability/alerts`
- `GET /api/observability/prediction`

## Tests

```bash
python -m pytest
```

## Project Map

- `flink/jobs/` PyFlink SQL streaming job.
- `services/` shared metric, schema, alert, and prediction logic.
- `backend/api/` Flask JSON API for observability views.
- `frontend/` React dashboard.
- `database/schema.sql` PostgreSQL tables.
- `benchmark/` batch baseline and benchmark runner.
- `monitoring/` Prometheus and Grafana assets.
- `docs/architecture.md` architecture diagram.
- `docs/performance_evaluation_report.md` evaluation template.

