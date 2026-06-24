# Performance Evaluation Report

The benchmark runner compares traditional ten-minute batch analytics with a
Kafka/Flink streaming path.

Measured dimensions:

- DORA metric computation latency: metric availability minus event generation time.
- Failure detection delay: alert creation time minus failure event time.
- Accuracy under out-of-order events: computed metric versus ground truth.
- Throughput: events processed per second at 100, 500, 1000, 5000, and 10000 events/sec.
- End-to-end latency: dashboard display time minus event creation time.
- Predictive alert quality: precision, recall, F1 score, and ROC-AUC.

Run:

```bash
python ../event-log-generation/kafka/event_generator/generator.py --count 100000
python benchmark/benchmark_runner.py --iterations 10
```

Results are written to `benchmark/performance_report.json`.
