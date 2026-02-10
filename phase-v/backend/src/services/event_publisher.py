# Event Publishing Service
# Publishes events to Kafka after successful database operations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .kafka_producer import get_kafka_producer

logger = logging.getLogger(__name__)


class EventPublisher:
    """Service for publishing events to Kafka after DB operations"""

    @staticmethod
    def publish_task_created(
        task_id: int,
        user_id: str,
        task_data: Dict[str, Any],
    ):
        """Publish task-created event"""
        producer = get_kafka_producer()

        # Publish to task-events topic (audit trail)
        producer.publish_task_event(
            event_type="created",
            task_id=str(task_id),
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": None,
                "after": task_data,
                "changes": ["created"],
            },
        )

        # Publish to task-updates topic (real-time sync)
        producer.publish_task_update(
            event_type="created",
            task_id=str(task_id),
            user_id=user_id,
            task_data={
                **task_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(f"Published task-created event for task {task_id}")

    @staticmethod
    def publish_task_updated(
        task_id: int,
        user_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        changes: list,
    ):
        """Publish task-updated event"""
        producer = get_kafka_producer()

        producer.publish_task_event(
            event_type="updated",
            task_id=str(task_id),
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": old_data,
                "after": new_data,
                "changes": changes,
            },
        )

        producer.publish_task_update(
            event_type="updated",
            task_id=str(task_id),
            user_id=user_id,
            task_data={
                **new_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(f"Published task-updated event for task {task_id}")

    @staticmethod
    def publish_task_completed(
        task_id: int,
        user_id: str,
        task_data: Dict[str, Any],
    ):
        """Publish task-completed event"""
        producer = get_kafka_producer()

        producer.publish_task_event(
            event_type="completed",
            task_id=str(task_id),
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": {"completed": False},
                "after": {"completed": True, "completed_at": task_data.get("completed_at")},
                "changes": ["completed", "completed_at"],
            },
        )

        producer.publish_task_update(
            event_type="completed",
            task_id=str(task_id),
            user_id=user_id,
            task_data={
                **task_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(f"Published task-completed event for task {task_id}")

    @staticmethod
    def publish_task_deleted(
        task_id: int,
        user_id: str,
        deleted_data: Dict[str, Any],
    ):
        """Publish task-deleted event"""
        producer = get_kafka_producer()

        producer.publish_task_event(
            event_type="deleted",
            task_id=str(task_id),
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": deleted_data,
                "after": None,
                "changes": ["deleted"],
            },
        )

        producer.publish_task_update(
            event_type="deleted",
            task_id=str(task_id),
            user_id=user_id,
            task_data={
                **deleted_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(f"Published task-deleted event for task {task_id}")
