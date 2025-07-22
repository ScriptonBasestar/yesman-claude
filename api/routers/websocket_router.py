# Copyright notice.

import asyncio
import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.routers.logs import get_logs
from api.utils import BatchConfig, WebSocketBatchProcessor

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""WebSocket router for real-time updates."""


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self) -> None:
        # All active connections
        self.active_connections: list[WebSocket] = []

        # Channel-based connections
        self.channel_connections: dict[str, set[WebSocket]] = defaultdict(set)

        # Connection metadata
        self.connection_metadata: dict[WebSocket, dict] = {}

        # Ping interval in seconds
        self.ping_interval = 30

        # Batch processor configuration
        batch_config = BatchConfig(
            max_batch_size=10,  # Batch up to 10 messages
            max_batch_time=0.1,  # Wait max 100ms
            compression_threshold=5,  # Start optimizing after 5 messages
        )
        self.batch_processor = WebSocketBatchProcessor(batch_config)

        # Register message handlers for each channel
        self._register_batch_handlers()

        # Start background tasks
        self.start_background_tasks()

    def _register_batch_handlers(self) -> None:
        """Register message handlers for batch processing."""
        self.batch_processor.register_message_handler("dashboard", self._send_to_dashboard)
        self.batch_processor.register_message_handler("sessions", self._send_to_sessions)
        self.batch_processor.register_message_handler("health", self._send_to_health)
        self.batch_processor.register_message_handler("activity", self._send_to_activity)
        self.batch_processor.register_message_handler("logs", self._send_to_logs)

    async def _send_to_dashboard(self, messages: list[dict]) -> None:
        """Send batched messages to dashboard channel."""
        await self._broadcast_messages_to_channel("dashboard", messages)

    async def _send_to_sessions(self, messages: list[dict]) -> None:
        """Send batched messages to sessions channel."""
        await self._broadcast_messages_to_channel("sessions", messages)

    async def _send_to_health(self, messages: list[dict]) -> None:
        """Send batched messages to health channel."""
        await self._broadcast_messages_to_channel("health", messages)

    async def _send_to_activity(self, messages: list[dict]) -> None:
        """Send batched messages to activity channel."""
        await self._broadcast_messages_to_channel("activity", messages)

    async def _send_to_logs(self, messages: list[dict]) -> None:
        """Send batched messages to logs channel."""
        await self._broadcast_messages_to_channel("logs", messages)

    async def _broadcast_messages_to_channel(self, channel: str, messages: list[dict]) -> None:
        """Broadcast multiple messages to a specific channel."""
        connections = self.channel_connections.get(channel, set())
        disconnected = []

        for connection in connections:
            try:
                # Send batch as a single WebSocket message or multiple messages
                if len(messages) == 1:
                    await connection.send_json(messages[0])
                else:
                    # Send as message batch
                    batch_message = {
                        "type": "message_batch",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "channel": channel,
                        "messages": messages,
                        "count": len(messages),
                    }
                    await connection.send_json(batch_message)
            except Exception:
                logger.exception(f"Error broadcasting batch to {channel}:")  # noqa: G004
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    def start_background_tasks(self) -> None:
        """Start background tasks for connection management."""
        asyncio.create_task(self.ping_connections())
        asyncio.create_task(self.batch_processor.start())

    async def connect(self, websocket: WebSocket, channel: str = "dashboard") -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.channel_connections[channel].add(websocket)

        # Store metadata
        self.connection_metadata[websocket] = {
            "channel": channel,
            "connected_at": datetime.now(UTC),
            "last_ping": datetime.now(UTC),
        }

        logger.info(f"WebSocket connected to channel: {channel}")  # noqa: G004

        # Send initial data
        await self.send_initial_data(websocket, channel)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all channels
        for connections in self.channel_connections.values():
            if websocket in connections:
                connections.remove(websocket)

        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info("WebSocket disconnected")

    @staticmethod
    async def send_initial_data(websocket: WebSocket, channel: str) -> None:
        """Send initial data when a client connects."""
        try:
            from api.routers.dashboard import (
                get_activity_data,
                get_dashboard_stats,
                get_project_health,
                get_sessions,
            )

            initial_data: dict[str, Any] = {}

            if channel in {"dashboard", "sessions"}:
                sessions = await get_sessions()
                initial_data["sessions"] = sessions

            if channel in {"dashboard", "health"}:
                health = await get_project_health()
                initial_data["health"] = health

            if channel in {"dashboard", "activity"}:
                activity = await get_activity_data()
                initial_data["activity"] = activity

            if channel == "dashboard":
                stats = await get_dashboard_stats()
                initial_data["stats"] = stats

            message = {
                "type": "initial_data",
                "timestamp": datetime.now(UTC).isoformat(),
                "channel": channel,
                "data": initial_data,
            }

            await websocket.send_json(message)

        except Exception:
            logger.exception("Error sending initial data:")

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            logger.exception("Error sending personal message:")
            self.disconnect(websocket)

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                logger.exception("Error broadcasting message:")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_to_channel(self, channel: str, message: dict) -> None:
        """Broadcast message to specific channel (using batch processor)."""
        # Queue message for batch processing
        self.batch_processor.queue_message(channel, message)

    async def broadcast_to_channel_immediate(self, channel: str, message: dict) -> None:
        """Broadcast message immediately without batching (for urgent messages)."""
        await self.batch_processor.send_immediate(channel, message)

    async def broadcast_session_update(self, session_data: dict) -> None:
        """Broadcast session update to relevant channels."""
        message = {
            "type": "session_update",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": session_data,
        }

        await self.broadcast_to_channel("sessions", message)
        await self.broadcast_to_channel("dashboard", message)

    async def broadcast_health_update(self, health_data: dict) -> None:
        """Broadcast health update to relevant channels."""
        message = {
            "type": "health_update",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": health_data,
        }

        await self.broadcast_to_channel("health", message)
        await self.broadcast_to_channel("dashboard", message)

    async def broadcast_activity_update(self, activity_data: dict) -> None:
        """Broadcast activity update to relevant channels."""
        message = {
            "type": "activity_update",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": activity_data,
        }

        await self.broadcast_to_channel("activity", message)
        await self.broadcast_to_channel("dashboard", message)

    async def broadcast_log_update(self, log_entry: dict) -> None:
        """Broadcast log update to relevant channels."""
        message = {
            "type": "log_update",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": log_entry,
        }

        await self.broadcast_to_channel("logs", message)
        await self.broadcast_to_channel("dashboard", message)

    async def ping_connections(self) -> None:
        """Send periodic ping messages to keep connections alive."""
        while True:
            await asyncio.sleep(self.ping_interval)

            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(
                        {
                            "type": "ping",
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )

                    # Update last ping time
                    if connection in self.connection_metadata:
                        self.connection_metadata[connection]["last_ping"] = datetime.now(UTC)

                except Exception:
                    logger.exception("Error pinging connection:")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

    def get_connection_stats(self) -> dict[str, int | dict[str, int]]:
        """Get statistics about active connections.

        Returns:
        dict containing total_connections and channels with connection counts.
        """
        channels: dict[str, int] = {}
        for channel, connections in self.channel_connections.items():
            channels[channel] = len(connections)

        stats: dict[str, int | dict[str, int]] = {
            "total_connections": len(self.active_connections),
            "channels": channels,
        }

        return stats

    async def shutdown(self) -> None:
        """Shutdown the connection manager and batch processor."""
        logger.info("Shutting down WebSocket connection manager...")

        # Stop batch processor
        await self.batch_processor.stop()

        # Disconnect all active connections
        for connection in self.active_connections.copy():
            try:
                await connection.close()
            except Exception:
                logger.exception("Error closing connection:")

        self.active_connections.clear()
        self.channel_connections.clear()
        self.connection_metadata.clear()

        logger.info("WebSocket connection manager shutdown complete")

    def get_batch_statistics(self) -> dict[str, int | float | bool]:
        """Get batch processing statistics.

        Returns:
        dict containing batch processing statistics including counts, sizes, and status.
        """
        return cast(dict[str, int | float | bool], self.batch_processor.get_statistics())


# Create global connection manager instance
manager = ConnectionManager()


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket) -> None:
    """Main dashboard WebSocket endpoint."""
    await manager.connect(websocket, "dashboard")

    try:
        while True:
            # Receive and process messages
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "pong":
                # Client responded to ping
                logger.debug("Received pong from dashboard client")

            elif data.get("type") == "subscribe":
                # Client wants to subscribe to specific updates
                channels = data.get("channels", [])
                for channel in channels:
                    manager.channel_connections[channel].add(websocket)
                    logger.info(f"Dashboard client subscribed to channel: {channel}")  # noqa: G004

            elif data.get("type") == "unsubscribe":
                # Client wants to unsubscribe from specific updates
                channels = data.get("channels", [])
                for channel in channels:
                    if websocket in manager.channel_connections[channel]:
                        manager.channel_connections[channel].remove(websocket)
                        logger.info(f"Dashboard client unsubscribed from channel: {channel}")  # noqa: G004

            else:
                # Echo back unknown messages for debugging
                await manager.send_personal_message(
                    {
                        "type": "echo",
                        "original": data,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Dashboard WebSocket disconnected")
    except Exception:
        logger.exception("WebSocket error:")
        manager.disconnect(websocket)


@router.websocket("/sessions")
async def websocket_sessions(websocket: WebSocket) -> None:
    """Sessions-specific WebSocket endpoint."""
    await manager.connect(websocket, "sessions")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "pong":
                logger.debug("Received pong from sessions client")

            elif data.get("type") == "refresh":
                # Client requests fresh session data
                await manager.send_initial_data(websocket, "sessions")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Sessions WebSocket disconnected")
    except Exception:
        logger.exception("Sessions WebSocket error:")
        manager.disconnect(websocket)


@router.websocket("/health")
async def websocket_health(websocket: WebSocket) -> None:
    """Health metrics WebSocket endpoint."""
    await manager.connect(websocket, "health")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "pong":
                logger.debug("Received pong from health client")

            elif data.get("type") == "refresh":
                # Client requests fresh health data
                await manager.send_initial_data(websocket, "health")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Health WebSocket disconnected")
    except Exception:
        logger.exception("Health WebSocket error:")
        manager.disconnect(websocket)


@router.websocket("/activity")
async def websocket_activity(websocket: WebSocket) -> None:
    """Activity data WebSocket endpoint."""
    await manager.connect(websocket, "activity")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "pong":
                logger.debug("Received pong from activity client")

            elif data.get("type") == "refresh":
                # Client requests fresh activity data
                await manager.send_initial_data(websocket, "activity")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Activity WebSocket disconnected")
    except Exception:
        logger.exception("Activity WebSocket error:")
        manager.disconnect(websocket)


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """Logs WebSocket endpoint."""
    await manager.connect(websocket, "logs")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "pong":
                logger.debug("Received pong from logs client")

            elif data.get("type") == "refresh":
                # Client requests fresh log data
                try:
                    logs = get_logs(limit=100)
                    initial_data = {
                        "type": "initial_logs",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "data": [log.dict() for log in logs],
                    }
                    await manager.send_personal_message(initial_data, websocket)
                except Exception:
                    logger.exception("Error sending initial logs:")

            elif data.get("type") == "test_log":
                # For testing - client can trigger test logs
                test_log = {
                    "level": data.get("level", "info"),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "source": data.get("source", "test"),
                    "message": data.get("message", "Test log message"),
                    "raw": f"[{datetime.now(UTC).isoformat()}] [TEST] Test log message",
                }
                await manager.broadcast_log_update(test_log)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Logs WebSocket disconnected")
    except Exception:
        logger.exception("Logs WebSocket error:")
        manager.disconnect(websocket)


# Export manager for use in other modules
__all__ = ["manager", "router"]
