"""
Reminder Consumer

Processes due reminders and sends notifications.
Triggered by Dapr cron binding on a schedule (e.g., every 5 minutes).
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.reminder_service import get_due_reminders, send_reminder


logger = logging.getLogger(__name__)


class ReminderConsumer:
    """
    T082: Consumer that processes due reminders.

    Triggered by Dapr cron binding to poll for due reminders
    and send notifications.
    """

    def __init__(self):
        """Initialize the reminder consumer."""
        self.running = False

    def process_due_reminders(self) -> dict:
        """
        T082: Process all due reminders.

        Called by Dapr cron binding on schedule (every 5 minutes).
        Queries for due reminders and sends notifications.

        Returns:
            Dict with processing results:
            {
                "processed": int,
                "succeeded": int,
                "failed": int,
                "errors": List[str]
            }
        """
        logger.info("Processing due reminders...")

        processed = 0
        succeeded = 0
        failed = 0
        errors = []

        # Get database session
        session = next(get_session())

        try:
            # Get all due reminders
            due_reminders = get_due_reminders(session=session, limit=100)

            if not due_reminders:
                logger.info("No due reminders found")
                return {
                    "processed": 0,
                    "succeeded": 0,
                    "failed": 0,
                    "errors": []
                }

            logger.info(f"Found {len(due_reminders)} due reminders")

            # Process each reminder
            for reminder in due_reminders:
                processed += 1

                try:
                    # Send reminder (T083)
                    send_reminder(
                        reminder_id=reminder.id,
                        session=session
                    )
                    succeeded += 1
                    logger.info(f"Successfully sent reminder {reminder.id}")

                except Exception as e:
                    failed += 1
                    error_msg = f"Failed to send reminder {reminder.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg, exc_info=True)

            logger.info(
                f"Processed {processed} reminders: "
                f"{succeeded} succeeded, {failed} failed"
            )

        except Exception as e:
            logger.error(f"Error processing due reminders: {e}", exc_info=True)
            errors.append(f"Processing error: {str(e)}")

        finally:
            session.close()

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors
        }


# Global consumer instance
_reminder_consumer: Optional[ReminderConsumer] = None


def get_reminder_consumer() -> ReminderConsumer:
    """Get or create the global reminder consumer instance."""
    global _reminder_consumer
    if _reminder_consumer is None:
        _reminder_consumer = ReminderConsumer()
    return _reminder_consumer


def process_reminders_cron() -> dict:
    """
    T082: Entry point for Dapr cron binding.

    This function is called by Dapr cron binding on a schedule
    to process due reminders.

    Returns:
        Dict with processing results
    """
    consumer = get_reminder_consumer()
    return consumer.process_due_reminders()
