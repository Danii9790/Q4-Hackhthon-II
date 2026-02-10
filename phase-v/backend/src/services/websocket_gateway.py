"""
WebSocket Gateway Service

Consumes task updates from Kafka and broadcasts to connected WebSocket clients.
Enables real-time task synchronization across multiple devices.
"""
import logging
import asyncio
import json
from typing import Dict, Set, Any, Optional
from datetime import datetime, timezone

from kafka import KafkaConsumer
from kafka.errors import KafkaError


logger = logging.getLogger(__name__)


class WebSocketGateway:
    """
    T094: WebSocket gateway for real-time task updates.

    This service:
    - Subscribes to task-updates Kafka topic
    - Tracks connected clients by user_id
    - Broadcasts task updates to relevant users
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "task-updates",
    ):
        """
        Initialize WebSocket gateway.

        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Kafka topic to consume from
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        # Structure: {user_id: {connection_id: websocket}}

    def add_client(self, user_id: str, connection_id: str, websocket: Any = None):
        """
        T095: Add a WebSocket client connection.

        Args:
            user_id: User ID
            connection_id: Unique connection identifier
            websocket: WebSocket connection object (optional, for tracking)
        """
        if user_id not in self.connected_clients:
            self.connected_clients[user_id] = {}

        self.connected_clients[user_id][connection_id] = {
            "websocket": websocket,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Added WebSocket connection {connection_id} for user {user_id}")

    def remove_client(self, user_id: str, connection_id: str):
        """
        T095: Remove a WebSocket client connection.

        Args:
            user_id: User ID
            connection_id: Connection identifier to remove
        """
        if user_id in self.connected_clients:
            if connection_id in self.connected_clients[user_id]:
                del self.connected_clients[user_id][connection_id]
                logger.info(f"Removed WebSocket connection {connection_id} for user {user_id}")

            # Clean up empty user entries
            if not self.connected_clients[user_id]:
                del self.connected_clients[user_id]

    def get_user_connections(self, user_id: str) -> Set[str]:
        """
        Get all connection IDs for a user.

        Args:
            user_id: User ID

        Returns:
            Set of connection IDs
        """
        if user_id not in self.connected_clients:
            return set()
        return set(self.connected_clients[user_id].keys())

    async def broadcast_to_user(self, user_id: str, message: dict):
        """
        T094: Broadcast a message to all connected clients for a user.

        Args:
            user_id: User ID to broadcast to
            message: Message dict to broadcast
        """
        connections = self.get_user_connections(user_id)

        if not connections:
            logger.debug(f"No connected clients for user {user_id}")
            return

        logger.info(f"Broadcasting to {len(connections)} connections for user {user_id}")

        # Send message to each connection
        for connection_id in connections:
            try:
                connection_data = self.connected_clients[user_id][connection_id]
                websocket = connection_data.get("websocket")

                if websocket:
                    # Send message via WebSocket
                    try:
                        await websocket.send_json(message)
                        logger.debug(f"Sent message to connection {connection_id}")
                    except Exception as e:
                        logger.error(f"Failed to send to connection {connection_id}: {e}")
                        # Remove dead connection
                        self.remove_client(user_id, connection_id)

            except Exception as e:
                logger.error(f"Error broadcasting to connection {connection_id}: {e}")

    def start_consumer(self):
        """
        T094: Start Kafka consumer for task updates.

        Runs in background thread to avoid blocking.
        """
        if self.running:
            logger.warning("WebSocket gateway consumer is already running")
            return

        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id="websocket-gateway",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
            )

            self.running = True
            logger.info(f"WebSocket gateway consumer started: topic={self.topic}")

        except KafkaError as e:
            logger.error(f"Failed to start WebSocket gateway consumer: {e}")
            raise

    def stop_consumer(self):
        """
        Stop the Kafka consumer.
        """
        self.running = False

        if self.consumer:
            self.consumer.close(timeout=5)
            self.consumer = None

        logger.info("WebSocket gateway consumer stopped")

    def process_messages(self):
        """
        Process Kafka messages and broadcast to clients.

        This should be called in a background task/thread.
        """
        if not self.consumer:
            logger.error("Kafka consumer not initialized. Call start_consumer() first.")
            return

        logger.info("WebSocket gateway message processing loop started")

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
                                f"Error processing WebSocket message: {e}",
                                exc_info=True
                            )

        except Exception as e:
            logger.error(f"WebSocket gateway processing error: {e}", exc_info=True)
        finally:
            logger.info("WebSocket gateway message processing loop stopped")

    def _process_message(self, event: dict):
        """
        Process a single Kafka message and broadcast to user.

        Args:
            event: Event data from Kafka
        """
        event_type = event.get("event_type")
        task_id = event.get("task_id")
        user_id = event.get("user_id")
        task_data = event.get("task_data", {})

        if not user_id:
            logger.warning(f"Message missing user_id: {event}")
            return

        logger.info(
            f"Processing {event_type} event for task {task_id}, user {user_id}"
        )

        # Broadcast to user's connected clients
        message = {
            "type": f"task_{event_type}",
            "task_id": task_id,
            "data": task_data,
            "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat())
        }

        # Use asyncio to broadcast asynchronously
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.broadcast_to_user(user_id, message))
        except RuntimeError:
            # No event loop running, use asyncio.run
            asyncio.run(self.broadcast_to_user(user_id, message))


# Global gateway instance
_websocket_gateway: Optional[WebSocketGateway] = None


def get_websocket_gateway() -> WebSocketGateway:
    """Get or create the global WebSocket gateway instance."""
    global _websocket_gateway
    if _websocket_gateway is None:
        _websocket_gateway = WebSocketGateway()
    return _websocket_gateway


def start_websocket_gateway():
    """Start the global WebSocket gateway consumer."""
    gateway = get_websocket_gateway()
    gateway.start_consumer()
    return gateway


def stop_websocket_gateway():
    """Stop the global WebSocket gateway consumer."""
    global _websocket_gateway
    if _websocket_gateway:
        _websocket_gateway.stop_consumer()
        _websocket_gateway = None
