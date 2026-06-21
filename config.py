import os
class Config:
    SECRET_KEY=os.getenv('SECRET_KEY','dev-secret-key')
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///incident.db')
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    KAFKA_BOOTSTRAP_SERVERS=os.getenv('KAFKA_BOOTSTRAP_SERVERS','localhost:9092')
    DORA_EVENTS_TOPIC=os.getenv('DORA_EVENTS_TOPIC','cicd-events')
    DORA_METRICS_TOPIC=os.getenv('DORA_METRICS_TOPIC','dora-metrics')
    DORA_ALERTS_TOPIC=os.getenv('DORA_ALERTS_TOPIC','alerts')
