from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


def main() -> None:
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(int(os.getenv("FLINK_PARALLELISM", "2")))
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    table_env = StreamTableEnvironment.create(env, environment_settings=settings)

    kafka = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    postgres = os.getenv("POSTGRES_JDBC_URL", "jdbc:postgresql://postgres:5432/observability")

    table_env.execute_sql(
        f"""
        CREATE TABLE cicd_events (
            event_id STRING,
            pipeline_id STRING,
            repository_id STRING,
            run_id STRING,
            event_type STRING,
            event_timestamp TIMESTAMP(3),
            processing_timestamp TIMESTAMP(3),
            status STRING,
            WATERMARK FOR event_timestamp AS event_timestamp - INTERVAL '5' MINUTE
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'cicd-events',
            'properties.bootstrap.servers' = '{kafka}',
            'properties.group.id' = 'dora-flink',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
        """
    )

    table_env.execute_sql(
        f"""
        CREATE TABLE dora_metrics (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            repository_id STRING,
            deployment_frequency BIGINT,
            failed_deployments BIGINT,
            total_deployments BIGINT,
            change_failure_rate DOUBLE,
            metric_available_at TIMESTAMP(3)
        ) WITH (
            'connector' = 'jdbc',
            'url' = '{postgres}',
            'table-name' = 'dora_metrics',
            'username' = '{os.getenv("POSTGRES_USER", "observability")}',
            'password' = '{os.getenv("POSTGRES_PASSWORD", "observability")}'
        )
        """
    )

    table_env.execute_sql(
        f"""
        CREATE TABLE metrics_topic (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            repository_id STRING,
            deployment_frequency BIGINT,
            failed_deployments BIGINT,
            total_deployments BIGINT,
            change_failure_rate DOUBLE,
            metric_available_at TIMESTAMP(3)
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'dora-metrics',
            'properties.bootstrap.servers' = '{kafka}',
            'format' = 'json'
        )
        """
    )

    query = """
        SELECT
            window_start,
            window_end,
            repository_id,
            SUM(CASE WHEN event_type = 'DEPLOYMENT_COMPLETED' THEN 1 ELSE 0 END) AS deployment_frequency,
            SUM(CASE WHEN event_type IN ('DEPLOYMENT_FAILED', 'ROLLBACK_TRIGGERED') THEN 1 ELSE 0 END) AS failed_deployments,
            SUM(CASE WHEN event_type IN ('DEPLOYMENT_COMPLETED', 'DEPLOYMENT_FAILED', 'ROLLBACK_TRIGGERED') THEN 1 ELSE 0 END) AS total_deployments,
            CASE
                WHEN SUM(CASE WHEN event_type IN ('DEPLOYMENT_COMPLETED', 'DEPLOYMENT_FAILED', 'ROLLBACK_TRIGGERED') THEN 1 ELSE 0 END) = 0
                THEN 0.0
                ELSE
                    SUM(CASE WHEN event_type IN ('DEPLOYMENT_FAILED', 'ROLLBACK_TRIGGERED') THEN 1 ELSE 0 END) * 100.0 /
                    SUM(CASE WHEN event_type IN ('DEPLOYMENT_COMPLETED', 'DEPLOYMENT_FAILED', 'ROLLBACK_TRIGGERED') THEN 1 ELSE 0 END)
            END AS change_failure_rate,
            CURRENT_TIMESTAMP AS metric_available_at
        FROM TABLE(
            HOP(TABLE cicd_events, DESCRIPTOR(event_timestamp), INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)
        )
        GROUP BY window_start, window_end, repository_id
    """
    table_env.execute_sql(f"INSERT INTO dora_metrics {query}")
    table_env.execute_sql(f"INSERT INTO metrics_topic {query}").wait()


if __name__ == "__main__":
    main()
