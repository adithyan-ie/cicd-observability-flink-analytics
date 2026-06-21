# Architecture

```mermaid
flowchart LR
    G[CI/CD Event Generator] --> K[(Kafka: cicd-events)]
    K --> F[PyFlink Event-Time Job]
    F --> M[(Kafka: dora-metrics)]
    F --> A[(Kafka: alerts)]
    F --> P[(PostgreSQL)]
    P --> API[Flask Observability API]
    M --> API
    A --> API
    API --> UI[React Dashboard]
    API --> PROM[Prometheus]
    PROM --> GRAF[Grafana]
    B[Batch Baseline] --> R[Benchmark Report]
    F --> R
```

Events carry both event timestamps and processing timestamps. Flink assigns a
five-minute watermark to tolerate delayed and out-of-order pipeline events while
still producing low-latency DORA windows.

