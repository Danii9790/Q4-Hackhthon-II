# Kafka Producer Service
# Publishes events to Kafka topics for event-driven architecture

import json
import logging
import time
from typing import Any, Dict, Optional
from kafka import KafkaProducer as SyncKafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Kafka producer for publishing events to Kafka topics"""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        client_id: str = "todo-backend-producer",
    ):
        """
        Initialize Kafka producer

        Args:
            bootstrap_servers: Kafka broker addresses (comma-separated)
            client_id: Client ID for this producer
        """
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[SyncKafkaProducer] = None
        self.client_id = client_id

    def start(self):
        """Initialize the Kafka producer"""
        try:
            self.producer = SyncKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,  # Retry failed sends 3 times
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                compression_type='snappy',  # Compress messages
            )
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    def stop(self):
        """Flush and close the Kafka producer"""
        if self.producer:
            self.producer.flush(timeout=10)
            self.producer.close()
            logger.info("Kafka producer stopped")

    def publish_event(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
        max_retries: int = 3,
    ) -> bool:
        """
        T173: Publish an event to a Kafka topic with exponential backoff retry

        Args:
            topic: Kafka topic name
            event: Event data (will be JSON serialized)
            key: Optional partition key (used for ordering)
            max_retries: Maximum number of retry attempts

        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized. Call start() first.")
            return False

        # T173: Retry with exponential backoff
        for attempt in range(max_retries):
            try:
                future = self.producer.send(
                    topic=topic,
                    value=event,
                    key=key,
                )
                record_metadata = future.get(timeout=10)
                logger.debug(
                    f"Event published to {topic}: partition={record_metadata.partition}, "
                    f"offset={record_metadata.offset}"
                )
                return True
            except KafkaError as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Failed to publish event to {topic} (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to publish event to {topic} after {max_retries} attempts: {e}")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error publishing to {topic}: {e}")
                return False

    def publish_task_event(
        self,
        event_type: str,
        task_id: str,
        user_id: str,
        event_data: Dict[str, Any],
    ) -> bool:
        """
        Publish a task event to the task-events topic

        Args:
            event_type: Type of event (created, updated, completed, deleted)
            task_id: Task ID
            user_id: User ID who performed the action
            event_data: Additional event data (before/after state, changes, etc.)

        Returns:
            True if published successfully
        """
        event = {
            "event_type": event_type,
            "task_id": task_id,
            "user_id": user_id,
            "timestamp": event_data.get("timestamp"),
            "event_data": event_data,
        }

        # Use user_id as key to ensure all events for a user go to same partition
        return self.publish_event(
            topic="task-events",
            event=event,
            key=user_id,
        )

    def publish_task_update(
        self,
        event_type: str,
        task_id: str,
        user_id: str,
        task_data: Dict[str, Any],
    ) -> bool:
        """
        Publish a task update for real-time synchronization

        Args:
            event_type: Type of event (created, updated, completed, deleted)
            task_id: Task ID
            user_id: User ID who performed the action
            task_data: Task data (title, description, completed, etc.)

        Returns:
            True if published successfully
        """
        event = {
            "event_type": event_type,
            "task_id": task_id,
            "user_id": user_id,
            "timestamp": task_data.get("timestamp"),
            "task_data": task_data,
        }

        # Use user_id as key
        return self.publish_event(
            topic="task-updates",
            event=event,
            key=user_id,
        )

    def publish_reminder(
        self,
        reminder_id: str,
        task_id: str,
        user_id: str,
        remind_at: str,
        task_data: Dict[str, Any],
    ) -> bool:
        """
        Publish a reminder event

        Args:
            reminder_id: Reminder ID
            task_id: Task ID
            user_id: User ID to notify
            remind_at: When to send reminder (ISO 8601)
            task_data: Task data (title, due_date, etc.)

        Returns:
            True if published successfully
        """
        event = {
            "reminder_id": reminder_id,
            "task_id": task_id,
            "user_id": user_id,
            "remind_at": remind_at,
            "task_data": task_data,
        }

        return self.publish_event(
            topic="reminders",
            event=event,
            key=user_id,
        )


# Global producer instance
_kafka_producer: Optional[KafkaProducer] = None


def get_kafka_producer() -> KafkaProducer:
    """Get or create the global Kafka producer instance"""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducer()
        _kafka_producer.start()
    return _kafka_producer


def shutdown_kafka_producer():
    """Shutdown the global Kafka producer"""
    global _kafka_producer
    if _kafka_producer:
        _kafka_producer.stop()
        _kafka_producer = None
