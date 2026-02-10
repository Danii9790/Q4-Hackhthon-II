# Prometheus Metrics Middleware
# T159-T162: Tracks HTTP requests, Kafka operations, and database queries

import time
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable

logger = logging.getLogger(__name__)


# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)


# Database Metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['operation', 'table']
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Idle database connections'
)


# Kafka Metrics
kafka_messages_published_total = Counter(
    'kafka_messages_published_total',
    'Total Kafka messages published',
    ['topic', 'status']
)

kafka_publish_duration_seconds = Histogram(
    'kafka_publish_duration_seconds',
    'Kafka publish latency',
    ['topic']
)

kafka_consumer_lag = Gauge(
    'kafka_consumer_lag',
    'Kafka consumer lag',
    ['topic', 'partition']
)


# Business Metrics
tasks_total = Gauge(
    'tasks_total',
    'Total number of tasks',
    ['user_id', 'status']
)

audit_events_total = Counter(
    'audit_events_total',
    'Total audit events',
    ['event_type']
)

reminders_sent_total = Counter(
    'reminders_sent_total',
    'Total reminders sent',
    ['status']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for Prometheus metrics collection.
    Tracks HTTP request count, latency, and in-flight requests.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get endpoint path (strip query parameters)
        path = request.url.path
        method = request.method

        # Track in-flight requests
        http_requests_in_progress.labels(
            method=method,
            endpoint=path
        ).inc()

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            status = str(response.status_code)
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status
            ).inc()

            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            return response

        except Exception as e:
            # Record error metrics
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status='500'
            ).inc()

            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            logger.error(f"Request error: {method} {path} - {str(e)}")
            raise

        finally:
            # Decrease in-flight requests
            http_requests_in_progress.labels(
                method=method,
                endpoint=path
            ).dec()


def metrics_handler():
    """
    Return Prometheus metrics in the Prometheus text format.
    """
    return generate_latest(REGISTRY)


def get_content_type():
    """
    Return the content type for Prometheus metrics.
    """
    return CONTENT_TYPE_LATEST


# Database metrics tracking
def track_db_query(operation: str, table: str, duration: float):
    """Track database query metrics."""
    db_query_duration_seconds.labels(
        operation=operation,
        table=table
    ).observe(duration)


def track_db_connections(active: int, idle: int):
    """Track database connection pool metrics."""
    db_connections_active.set(active)
    db_connections_idle.set(idle)


# Kafka metrics tracking
def track_kafka_publish(topic: str, duration: float, status: str):
    """Track Kafka publish metrics."""
    kafka_messages_published_total.labels(
        topic=topic,
        status=status
    ).inc()
    kafka_publish_duration_seconds.labels(
        topic=topic
    ).observe(duration)


def track_consumer_lag(topic: str, partition: int, lag: int):
    """Track Kafka consumer lag."""
    kafka_consumer_lag.labels(
        topic=topic,
        partition=partition
    ).set(lag)


# Business metrics tracking
def track_task_metrics(user_id: str, total: int, completed: int, pending: int):
    """Track task count metrics."""
    tasks_total.labels(user_id=user_id, status='total').set(total)
    tasks_total.labels(user_id=user_id, status='completed').set(completed)
    tasks_total.labels(user_id=user_id, status='pending').set(pending)


def track_audit_event(event_type: str):
    """Track audit event metrics."""
    audit_events_total.labels(event_type=event_type).inc()


def track_reminder_sent(status: str):
    """Track reminder sent metrics."""
    reminders_sent_total.labels(status=status).inc()
