# Copyright notice.

import asyncio
import json
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""WebSocket message batch processor for optimized real-time updates."""



@dataclass
class MessageBatch:
    """A batch of WebSocket messages to be sent together."""

    messages: list[dict[str, object]]
    timestamp: float
    batch_id: str
    channel: str
    size_bytes: int = 0

    def __post_init__(self) -> object:
        """Calculate batch size after initialization.

        Returns:
        object: Description of return value.
        """
        if not self.size_bytes:
            self.size_bytes = sum(len(json.dumps(msg)) for msg in self.messages)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    max_batch_size: int = 10  # Maximum messages per batch
    max_batch_time: float = 0.1  # Maximum time to wait (100ms)
    max_memory_size: int = 1024 * 1024  # 1MB max memory usage
    compression_threshold: int = 5  # Start batching after 5 messages


class WebSocketBatchProcessor:
    """Processes WebSocket messages in batches for optimized performance."""

    def __init__(self, config: BatchConfig | None = None) -> None:
        self.config = config or BatchConfig()

        # Message queues per channel
        self.pending_messages: dict[str, deque] = {}
        self.last_flush_time: dict[str, float] = {}
        self.batch_counter = 0

        # Statistics tracking
        self.stats = {
            "batches_sent": 0,
            "messages_processed": 0,
            "bytes_saved": 0,
            "avg_batch_size": 0,
            "compression_ratio": 1.0,
            "channels_active": 0,
        }

        # Processing control
        self._processing_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._message_handlers: dict[str, Callable[[list[dict[str, object]]], Awaitable[None]]] = {}

        self.logger = logging.getLogger("yesman.websocket_batch")

    def register_message_handler(self, channel: str, handler: Callable[[list[dict[str, object]]], Awaitable[None]]) -> None:
        """Register a message handler for a specific channel.

        """
        self._message_handlers[channel] = handler
        self.logger.info("Registered message handler for channel: %s", channel)

    async def start(self) -> None:
        """Start the batch processing system."""
        if self._processing_task and not self._processing_task.done():
            self.logger.warning("Batch processor already running")
            return

        self._stop_event.clear()
        self._processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("WebSocket batch processor started")

    async def stop(self) -> None:
        """Stop the batch processing system."""
        if not self._processing_task:
            return

        self._stop_event.set()

        try:
            await asyncio.wait_for(self._processing_task, timeout=5.0)
        except TimeoutError:
            self.logger.warning("Batch processor stop timeout, cancelling task")
            self._processing_task.cancel()

        # Flush any remaining messages
        await self._flush_all_channels()

        self.logger.info("WebSocket batch processor stopped")

    def queue_message(self, channel: str, message: dict[str, object]) -> None:
        """Queue a message for batch processing.

        """
        # Initialize channel if not exists
        if channel not in self.pending_messages:
            self.pending_messages[channel] = deque()
            self.last_flush_time[channel] = time.time()

        # Add message to queue
        message_with_metadata = {
            **message,
            "queued_at": time.time(),
            "batch_eligible": True,
        }

        self.pending_messages[channel].append(message_with_metadata)

        # Check if immediate flush is needed
        queue_size = len(self.pending_messages[channel])
        if queue_size >= self.config.max_batch_size:
            # Schedule immediate flush for this channel
            asyncio.create_task(self._flush_channel(channel))

    async def send_immediate(self, channel: str, message: dict[str, object]) -> None:
        """Send a message immediately without batching (for urgent messages)."""
        handler = self._message_handlers.get(channel)
        if handler:
            try:
                await handler([message])
                self.stats["messages_processed"] += 1
            except Exception:
                self.logger.exception("Error sending immediate message to %s", channel)
        else:
            self.logger.warning("No handler registered for channel: %s", channel)

    async def _processing_loop(self) -> None:
        """Main processing loop for batch management."""
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(0.01)  # Check every 10ms

                current_time = time.time()
                channels_to_flush = []

                # Check each channel for flush conditions
                for channel in list(self.pending_messages.keys()):
                    queue = self.pending_messages[channel]
                    last_flush = self.last_flush_time[channel]

                    should_flush = (
                        len(queue) >= self.config.max_batch_size
                        or (len(queue) > 0 and current_time - last_flush >= self.config.max_batch_time)
                        or self._get_queue_memory_size(queue) >= self.config.max_memory_size
                    )

                    if should_flush:
                        channels_to_flush.append(channel)

                # Flush channels that need it
                for channel in channels_to_flush:
                    await self._flush_channel(channel)

        except Exception:
            self.logger.error("Error in batch processing loop", exc_info=True)

    async def _flush_channel(self, channel: str) -> None:
        """Flush pending messages for a specific channel."""
        if channel not in self.pending_messages:
            return

        queue = self.pending_messages[channel]
        if not queue:
            return

        # Collect messages for this batch
        messages = []
        batch_size = min(len(queue), self.config.max_batch_size)

        for _ in range(batch_size):
            if queue:
                messages.append(queue.popleft())

        if not messages:
            return

        # Create batch
        batch = MessageBatch(
            messages=messages,
            timestamp=time.time(),
            batch_id=f"batch_{self.batch_counter:06d}",
            channel=channel,
        )

        try:
            await self._send_batch(batch)

            # Update statistics
            self.stats["batches_sent"] += 1
            self.stats["messages_processed"] += len(messages)
            self.stats["avg_batch_size"] = self.stats["messages_processed"] / self.stats["batches_sent"]

            self.last_flush_time[channel] = time.time()
            self.batch_counter += 1

            self.logger.debug("Flushed batch %s to %s: %d messages", batch.batch_id, channel, len(messages))

        except Exception:
            self.logger.exception("Failed to send batch %s to %s", batch.batch_id, channel)
            # Re-queue messages for retry (with retry limit to prevent infinite loops)
            retry_messages = []
            for msg in messages:
                retry_count = msg.get("retry_count", 0)
                if retry_count < 3:  # Max 3 retries
                    msg["retry_count"] = retry_count + 1
                    retry_messages.append(msg)
                else:
                    self.logger.warning("Dropping message after 3 failed retries: %s", msg)

            if retry_messages:
                self.pending_messages[channel].extendleft(reversed(retry_messages))

    async def _send_batch(self, batch: MessageBatch) -> None:
        """Send a batch of messages using the registered handler."""
        handler = self._message_handlers.get(batch.channel)
        if not handler:
            self.logger.error("No handler registered for channel: %s", batch.channel)
            return

        # Optimize batch if it's large enough
        optimized_messages = self._optimize_messages(batch.messages) if len(batch.messages) >= self.config.compression_threshold else batch.messages

        # Calculate compression savings
        original_size = batch.size_bytes
        optimized_size = sum(len(json.dumps(msg)) for msg in optimized_messages)

        if original_size > optimized_size:
            self.stats["bytes_saved"] += original_size - optimized_size
            compression_ratio = optimized_size / original_size if original_size > 0 else 1.0
            self.stats["compression_ratio"] = (self.stats["compression_ratio"] * (self.stats["batches_sent"] - 1) + compression_ratio) / self.stats["batches_sent"]

        # Send optimized batch
        try:
            await handler(optimized_messages)
        except Exception:
            self.logger.exception("Handler error for channel %s", batch.channel)
            raise

    def _optimize_messages(self, messages: list[dict[str, object]]) -> list[dict[str, object]]:
        """Optimize a batch of messages by combining similar ones.

        Returns:
        object: Description of return value.
        """
        optimized = []

        # Group messages by type for potential combination
        message_groups: dict[str, list[dict[str, object]]] = {}
        for msg in messages:
            msg_type = msg.get("type", "unknown")
            if msg_type not in message_groups:
                message_groups[msg_type] = []
            message_groups[msg_type].append(msg)

        for msg_type, group in message_groups.items():
            if msg_type in {"session_update", "health_update", "activity_update"}:
                # For update messages, combine data and keep only the latest
                if len(group) > 1:
                    combined_message = self._combine_update_messages(group)
                    optimized.append(combined_message)
                else:
                    optimized.extend(group)
            elif msg_type == "log_update":
                # For log messages, can batch multiple logs into one message
                if len(group) > 1:
                    combined_message = self._combine_log_messages(group)
                    optimized.append(combined_message)
                else:
                    optimized.extend(group)
            else:
                # For other message types, keep as-is
                optimized.extend(group)

        return optimized

    @staticmethod
    def _combine_update_messages(messages: list[dict[str, object]]) -> dict[str, object]:
        """Combine multiple update messages into a single message.

        Returns:
        object: Description of return value.
        """
        if not messages:
            return {}

        # Use the latest message as base
        latest_message = messages[-1]

        # Combine data from all messages
        combined_data = {}
        for msg in messages:
            if "data" in msg and isinstance(msg["data"], dict):
                combined_data.update(msg["data"])

        # Create combined message
        return {
            **latest_message,
            "data": combined_data,
            "batch_info": {
                "original_count": len(messages),
                "time_span": messages[-1].get("queued_at", 0) - messages[0].get("queued_at", 0),
                "combined_at": time.time(),
            },
        }

    @staticmethod
    def _combine_log_messages(messages: list[dict[str, object]]) -> dict[str, object]:
        """Combine multiple log messages into a batched log message.

        Returns:
        object: Description of return value.
        """
        if not messages:
            return {}

        # base_message = messages[0]  # Not used currently
        log_entries = []

        for msg in messages:
            if "data" in msg:
                log_entries.append(msg["data"])

        # Create batched log message
        return {
            "type": "log_batch",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {
                "entries": log_entries,
                "count": len(log_entries),
                "time_span": messages[-1].get("queued_at", 0) - messages[0].get("queued_at", 0),
            },
        }

    @staticmethod
    def _get_queue_memory_size(queue: deque) -> int:
        """Estimate memory usage of a message queue.

        Returns:
        int: Description of return value.
        """
        return sum(len(json.dumps(msg)) for msg in queue)

    async def _flush_all_channels(self) -> None:
        """Flush all pending messages from all channels."""
        for channel in list(self.pending_messages.keys()):
            await self._flush_channel(channel)

    def get_statistics(self) -> dict[str, object]:
        """Get processing statistics.

        Returns:
        object: Description of return value.
        """
        active_channels = len([ch for ch, queue in self.pending_messages.items() if queue])
        total_pending = sum(len(queue) for queue in self.pending_messages.values())

        return {
            **self.stats,
            "active_channels": active_channels,
            "total_pending_messages": total_pending,
            "pending_by_channel": {ch: len(queue) for ch, queue in self.pending_messages.items()},
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_batch_time": self.config.max_batch_time,
                "compression_threshold": self.config.compression_threshold,
            },
        }

    def update_config(self, **kwargs: dict[str, object]) -> None:
        """Update batch processing configuration.

        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info("Updated config %s = %s", key, value)
            else:
                self.logger.warning("Unknown config key: %s", key)

    def clear_channel(self, channel: str) -> None:
        """Clear all pending messages for a specific channel.

        """
        if channel in self.pending_messages:
            cleared_count = len(self.pending_messages[channel])
            self.pending_messages[channel].clear()
            self.logger.info("Cleared %d pending messages from %s", cleared_count, channel)
