# CI/CD Pipeline Application

Standalone CI/CD observability platform using Jenkins, Kafka, Flink, DORA metrics, Prometheus, Grafana, and Docker.

## Contents

- `Jenkinsfile` - CI pipeline that tests the sibling `incident-management-app`.
- `jenkins/` - Jenkins image, plugins, and seeded job setup.
- `kafka/` - CI/CD event generator and producer.
- `flink/` - streaming DORA metric processing jobs.
- `services/` - event schema and metric helpers used by generators and benchmarks.
- `benchmark/` - batch baseline and benchmark runner.
- `monitoring/` - Prometheus and Grafana assets.
- `database/schema.sql` - DORA metric sink schema.
- `docker-compose.yml` - pipeline platform deployment.

## Run With Docker

```bash
docker compose up -d --build
```

Services:

- Kafka UI: http://localhost:8080
- Flink UI: http://localhost:8081
- Jenkins: http://localhost:8082
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

Default Jenkins credentials can be overridden with:

```bash
JENKINS_ADMIN_USER=admin JENKINS_ADMIN_PASSWORD=change-me docker compose up -d --build jenkins
```

## Generate CI/CD Events

Install local Python utilities first:

```bash
python -m pip install -r requirements.txt
```

Write sample events:

```bash
python kafka/event_generator/generator.py --count 100000
```

Publish events to Kafka:

```bash
python kafka/event_generator/generator.py --count 100000 --to-kafka --rate 1000
```

## Kafka Topics

```bash
docker compose exec kafka kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists --topic cicd-events --partitions 6 --replication-factor 1
docker compose exec kafka kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists --topic dora-metrics --partitions 3 --replication-factor 1
docker compose exec kafka kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists --topic alerts --partitions 3 --replication-factor 1
```

The incident app can be run beside this app and receive operation logs through `http://localhost:5000/api/observability/events`.
