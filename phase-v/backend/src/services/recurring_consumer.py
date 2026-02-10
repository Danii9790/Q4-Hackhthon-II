"""
Recurring Task Consumer

Consumes task completion events from Kafka and automatically creates
the next occurrence for recurring tasks.
"""
import json
import logging
import threading
import time
from typing import Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.recurring_service import create_next_occurrence


logger = logging.getLogger(__name__)


class RecurringTaskConsumer:
    """
    T062: Kafka consumer for automatic recurring task generation.

    Listens for task-completed events and creates the next occurrence
    for tasks with a recurring_task_id.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "recurring-task-consumer",
        topic: str = "task-events",
    ):
        """
        Initialize the recurring task consumer.

        Args:
            bootstrap_servers: Kafka broker addresses
            group_id: Consumer group ID for offset management
            topic: Kafka topic to consume from
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """
        T063: Start the consumer in a background thread.

        The consumer runs in a separate thread to avoid blocking
        the main application.
        """
        if self.running:
            logger.warning("Recurring task consumer is already running")
            return

        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',  # Start from latest message
                enable_auto_commit=True,  # Auto-commit offsets
                session_timeout_ms=30000,  # 30 seconds
                heartbeat_interval_ms=3000,  # 3 seconds
            )

            self.running = True
            self.thread = threading.Thread(target=self._consume_loop, daemon=True)
            self.thread.start()

            logger.info(
                f"Recurring task consumer started: "
                f"topic={self.topic}, group={self.group_id}"
            )
        except KafkaError as e:
            logger.error(f"Failed to start recurring task consumer: {e}")
            raise

    def stop(self):
        """
        T064: Stop the consumer and cleanup resources.

        Gracefully shuts down the consumer thread and closes
        the Kafka connection.
        """
        self.running = False

        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None

        if self.consumer:
            self.consumer.close(timeout=5)
            self.consumer = None

        logger.info("Recurring task consumer stopped")

    def _consume_loop(self):
        """
        Main consumer loop.

        Continuously polls for messages and processes task completion events.
        Runs in a background thread.
        """
        logger.info("Recurring task consumer loop started")

        try:
            while self.running:
                # Poll for messages with 1 second timeout
                messages = self.consumer.poll(timeout_ms=1000)

                if not messages:
                    continue

                for topic_partition, records in messages.items():
                    for message in records:
                        try:
                            self._process_message(message.value)
                        except Exception as e:
                            logger.error(
                                f"Error processing message: {e}",
                                exc_info=True
                            )

        except Exception as e:
            logger.error(f"Consumer loop error: {e}", exc_info=True)
        finally:
            logger.info("Recurring task consumer loop stopped")

    def _process_message(self, event: dict):
        """
        Process a single Kafka message.

        Args:
            event: Event data from Kafka
        """
        event_type = event.get("event_type")
        task_id = event.get("task_id")
        user_id = event.get("user_id")

        # Only process task completion events
        if event_type != "completed":
            return

        logger.info(f"Processing task completion event: task_id={task_id}")

        # Get database session
        session = next(get_session())

        try:
            # Get the task to check if it's recurring
            from src.models.task import Task

            task = session.query(Task).filter(
                Task.id == task_id
            ).first()

            if not task:
                logger.warning(f"Task {task_id} not found, skipping")
                return

            # Check if this is a recurring task
            if not task.recurring_task_id:
                logger.debug(f"Task {task_id} is not recurring, skipping")
                return

            logger.info(
                f"Task {task_id} is recurring (template: {task.recurring_task_id}), "
                f"creating next occurrence"
            )

            # Create next occurrence
            next_task = create_next_occurrence(
                recurring_task_id=task.recurring_task_id,
                session=session
            )

            if next_task:
                logger.info(
                    f"Created next occurrence {next_task.id} for "
                    f"recurring task {task.recurring_task_id}"
                )
            else:
                logger.info(
                    f"Recurring task {task.recurring_task_id} reached end_date, "
                    f"no next occurrence created"
                )

        except Exception as e:
            logger.error(
                f"Error processing recurring task for task {task_id}: {e}",
                exc_info=True
            )
        finally:
            session.close()


# Global consumer instance
_recurring_consumer: Optional[RecurringTaskConsumer] = None


def get_recurring_consumer() -> RecurringTaskConsumer:
    """Get or create the global recurring task consumer instance"""
    global _recurring_consumer
    if _recurring_consumer is None:
        _recurring_consumer = RecurringTaskConsumer()
    return _recurring_consumer


def start_recurring_consumer():
    """Start the global recurring task consumer"""
    consumer = get_recurring_consumer()
    consumer.start()


def stop_recurring_consumer():
    """Stop the global recurring task consumer"""
    global _recurring_consumer
    if _recurring_consumer:
        _recurring_consumer.stop()
        _recurring_consumer = None
