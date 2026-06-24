#!/usr/bin/env bash
set -euo pipefail

echo "Starting CI/CD pipeline platform"
docker compose up -d --build

echo ""
echo "Services:"
echo "  Kafka UI:   http://localhost:8080"
echo "  Flink UI:   http://localhost:8081"
echo "  Jenkins:    http://localhost:8082"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3001"
echo ""
echo "Generate events:"
echo "  python kafka/event_generator/generator.py --count 100000 --to-kafka --rate 1000"
