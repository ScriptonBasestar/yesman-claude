"""WebSocket message batch processor for optimized real-time updates - Refactored version."""

import json
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from libs.core.base_batch_processor import BaseBatchProcessor


@dataclass
class MessageBatch:
    """A batch of WebSocket messages to be sent together."""

    messages: list[dict[str, Any]]
    timestamp: float
    batch_id: str
    channel: str
    size_bytes: int = 0

    def __post_init__(self):
        """Calculate batch size after initialization."""
        if not self.size_bytes:
            self.size_bytes = sum(len(json.dumps(msg)) for msg in self.messages)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    max_batch_size: int = 10  # Maximum messages per batch
    max_batch_time: float = 0.1  # Maximum time to wait (100ms)
    max_memory_size: int = 1024 * 1024  # 1MB max memory usage
    compression_threshold: int = 5  # Start batching after 5 messages


class ChannelBatchProcessor(BaseBatchProcessor[dict[str, Any], MessageBatch]):
    """Batch processor for a single channel."""

    def __init__(
        self,
        channel: str,
        handler: Callable,
        config: BatchConfig,
        parent_stats: dict[str, Any],
    ) -> None:
        """Initialize channel-specific batch processor."""
        super().__init__(
            batch_size=config.max_batch_size,
            flush_interval=config.max_batch_time,
        )
        self.channel = channel
        self.handler = handler
        self.config = config
        self.parent_stats = parent_stats  # Reference to parent statistics
        self.batch_counter = 0

    def create_batch(self, items: list[dict[str, Any]]) -> MessageBatch:
        """Create a MessageBatch from messages."""
        # Add metadata to messages
        for msg in items:
            if "queued_at" not in msg:
                msg["queued_at"] = time.time()
            msg["batch_eligible"] = True

        batch = MessageBatch(
            messages=items,
            timestamp=time.time(),
            batch_id=f"{self.channel}_batch_{self.batch_counter:06d}",
            channel=self.channel,
        )

        self.batch_counter += 1
        return batch

    async def process_batch(self, batch: MessageBatch) -> None:
        """Process a batch by sending through the handler."""
        # Optimize batch if large enough
        optimized_messages = self._optimize_messages(batch.messages) if len(batch.messages) >= self.config.compression_threshold else batch.messages

        # Calculate compression savings
        original_size = batch.size_bytes
        optimized_size = sum(len(json.dumps(msg)) for msg in optimized_messages)

        if original_size > optimized_size:
            bytes_saved = original_size - optimized_size
            self.parent_stats["bytes_saved"] += bytes_saved

            # Update compression ratio
            compression_ratio = optimized_size / original_size if original_size > 0 else 1.0
            batches_sent = self.parent_stats["batches_sent"]
            if batches_sent > 0:
                self.parent_stats["compression_ratio"] = (self.parent_stats["compression_ratio"] * (batches_sent - 1) + compression_ratio) / batches_sent

        # Send optimized batch
        await self.handler(optimized_messages)

        # Update parent statistics
        self.parent_stats["batches_sent"] += 1
        self.parent_stats["messages_processed"] += len(batch.messages)

        self.logger.debug(f"Sent batch {batch.batch_id}: {len(batch.messages)} messages")

    def _optimize_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Optimize a batch of messages by combining similar ones."""
        optimized = []

        # Group messages by type for potential combination
        message_groups = defaultdict(list)
        for msg in messages:
            msg_type = msg.get("type", "unknown")
            message_groups[msg_type].append(msg)

        for msg_type, group in message_groups.items():
            if msg_type in ["session_update", "health_update", "activity_update"]:
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

    def _combine_update_messages(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Combine multiple update messages into a single message."""
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

    def _combine_log_messages(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Combine multiple log messages into a batched log message."""
        if not messages:
            return {}

        log_entries = []
        for msg in messages:
            if "data" in msg:
                log_entries.append(msg["data"])

        # Create batched log message
        return {
            "type": "log_batch",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "entries": log_entries,
                "count": len(log_entries),
                "time_span": messages[-1].get("queued_at", 0) - messages[0].get("queued_at", 0),
            },
        }


class WebSocketBatchProcessor:
    """Manages batch processors for multiple WebSocket channels."""

    def __init__(self, config: BatchConfig | None = None) -> None:
        """Initialize the WebSocket batch processor."""
        self.config = config or BatchConfig()

        # Channel processors
        self._channel_processors: dict[str, ChannelBatchProcessor] = {}
        self._message_handlers: dict[str, Callable] = {}

        # Shared statistics
        self.stats = {
            "batches_sent": 0,
            "messages_processed": 0,
            "bytes_saved": 0,
            "avg_batch_size": 0,
            "compression_ratio": 1.0,
            "channels_active": 0,
        }

        # Control flags
        self._running = False

        self.logger = logging.getLogger("yesman.websocket_batch")

    def register_message_handler(self, channel: str, handler: Callable) -> None:
        """Register a message handler for a specific channel."""
        self._message_handlers[channel] = handler
        self.logger.info(f"Registered message handler for channel: {channel}")

    async def start(self) -> None:
        """Start the batch processing system."""
        if self._running:
            self.logger.warning("Batch processor already running")
            return

        self._running = True

        # Start any existing channel processors
        for processor in self._channel_processors.values():
            await processor.start()

        self.logger.info("WebSocket batch processor started")

    async def stop(self) -> None:
        """Stop the batch processing system."""
        if not self._running:
            return

        self._running = False

        # Stop all channel processors
        for processor in self._channel_processors.values():
            await processor.stop()

        self.logger.info("WebSocket batch processor stopped")

    def queue_message(self, channel: str, message: dict[str, Any]) -> None:
        """Queue a message for batch processing."""
        # Create channel processor if it doesn't exist
        if channel not in self._channel_processors:
            handler = self._message_handlers.get(channel)
            if not handler:
                self.logger.error(f"No handler registered for channel: {channel}")
                return

            processor = ChannelBatchProcessor(
                channel=channel,
                handler=handler,
                config=self.config,
                parent_stats=self.stats,
            )
            self._channel_processors[channel] = processor

            # Start processor if we're running
            if self._running:
                import asyncio

                asyncio.create_task(processor.start())

        # Add message to channel processor
        self._channel_processors[channel].add(message)

    async def send_immediate(self, channel: str, message: dict[str, Any]) -> None:
        """Send a message immediately without batching (for urgent messages)."""
        handler = self._message_handlers.get(channel)
        if handler:
            try:
                await handler([message])
                self.stats["messages_processed"] += 1
            except Exception as e:
                self.logger.exception(f"Error sending immediate message to {channel}: {e}")
        else:
            self.logger.warning(f"No handler registered for channel: {channel}")

    def get_statistics(self) -> dict[str, Any]:
        """Get processing statistics."""
        # Collect statistics from all channel processors
        channel_stats = {}
        total_pending = 0
        active_channels = 0

        for channel, processor in self._channel_processors.items():
            proc_stats = processor.get_statistics()
            channel_stats[channel] = proc_stats
            total_pending += proc_stats["pending_items"] + proc_stats["pending_batches"]
            if proc_stats["pending_items"] > 0 or proc_stats["pending_batches"] > 0:
                active_channels += 1

        # Calculate average batch size
        if self.stats["batches_sent"] > 0:
            self.stats["avg_batch_size"] = self.stats["messages_processed"] / self.stats["batches_sent"]

        return {
            **self.stats,
            "active_channels": active_channels,
            "total_pending_messages": total_pending,
            "channel_statistics": channel_stats,
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_batch_time": self.config.max_batch_time,
                "compression_threshold": self.config.compression_threshold,
            },
        }

    def update_config(self, **kwargs) -> None:
        """Update batch processing configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated config {key} = {value}")

                # Update config for all channel processors
                for processor in self._channel_processors.values():
                    processor.batch_size = self.config.max_batch_size
                    processor.flush_interval = self.config.max_batch_time
            else:
                self.logger.warning(f"Unknown config key: {key}")

    def clear_channel(self, channel: str) -> None:
        """Clear all pending messages for a specific channel."""
        if channel in self._channel_processors:
            processor = self._channel_processors[channel]
            stats = processor.get_statistics()
            cleared_count = stats["pending_items"]

            # Reset the processor's pending items
            with processor._lock:
                processor._pending_items.clear()

            self.logger.info(f"Cleared {cleared_count} pending messages from {channel}")

    async def get_channel_processor(self, channel: str) -> ChannelBatchProcessor | None:
        """Get the batch processor for a specific channel."""
        return self._channel_processors.get(channel)
