from __future__ import annotations

import json
import os

from kafka import KafkaProducer


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda value: value.encode("utf-8") if value else None,
        linger_ms=20,
        acks="all",
    )


def publish_event(event: dict, topic: str = "cicd-events") -> None:
    producer = build_producer()
    producer.send(topic, key=event.get("pipeline_id"), value=event)
    producer.flush()

