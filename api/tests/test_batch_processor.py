# Copyright notice.

import asyncio
from collections import deque
from typing import cast
from unittest.mock import AsyncMock

import pytest

from api.utils import BatchConfig, WebSocketBatchProcessor

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Tests for WebSocket batch processor functionality."""


class TestBatchConfig:
    """Test BatchConfig class."""

    @staticmethod
    def test_default_config() -> None:
        """Test default configuration values."""
        config = BatchConfig()

        assert config.max_batch_size == 10
        assert config.max_batch_time == 0.1
        assert config.max_memory_size == 1024 * 1024
        assert config.compression_threshold == 5

    @staticmethod
    def test_custom_config() -> None:
        """Test custom configuration values."""
        config = BatchConfig(
            max_batch_size=20,
            max_batch_time=0.2,
            compression_threshold=3,
        )

        assert config.max_batch_size == 20
        assert config.max_batch_time == 0.2
        assert config.compression_threshold == 3


class TestWebSocketBatchProcessor:
    """Test WebSocketBatchProcessor class."""

    @pytest.fixture
    @staticmethod
    def processor() -> WebSocketBatchProcessor:
        """Create a batch processor for testing.

        Returns:
        Websocketbatchprocessor object.
        """
        config = BatchConfig(max_batch_size=3, max_batch_time=0.05)
        return WebSocketBatchProcessor(config)

    @pytest.fixture
    @staticmethod
    def mock_handler() -> AsyncMock:
        """Create a mock message handler.

        Returns:
        Asyncmock object.
        """
        return AsyncMock()

    @staticmethod
    def test_initialization(processor: WebSocketBatchProcessor) -> None:
        """Test processor initialization."""
        assert processor.config.max_batch_size == 3
        assert processor.config.max_batch_time == 0.05
        assert processor.stats["batches_sent"] == 0
        assert processor.stats["messages_processed"] == 0

    @staticmethod
    def test_register_handler(processor: WebSocketBatchProcessor, mock_handler: AsyncMock) -> None:
        """Test message handler registration."""
        processor.register_message_handler("test_channel", mock_handler)
        assert "test_channel" in processor._message_handlers
        assert processor._message_handlers["test_channel"] == mock_handler

    @staticmethod
    def test_queue_message(processor: WebSocketBatchProcessor) -> None:
        """Test message queueing."""
        processor.queue_message("test_channel", {"type": "test", "data": "hello"})

        assert "test_channel" in processor.pending_messages
        assert len(processor.pending_messages["test_channel"]) == 1

        message = processor.pending_messages["test_channel"][0]
        assert message["type"] == "test"
        assert message["data"] == "hello"
        assert "queued_at" in message

    @pytest.mark.asyncio
    @staticmethod
    async def test_send_immediate(processor: WebSocketBatchProcessor, mock_handler: AsyncMock) -> None:
        """Test immediate message sending."""
        processor.register_message_handler("test_channel", mock_handler)

        test_message = {"type": "urgent", "data": "immediate"}
        await processor.send_immediate("test_channel", cast("dict[str, object]", test_message))

        mock_handler.assert_called_once_with([test_message])
        assert processor.stats["messages_processed"] == 1

    @pytest.mark.asyncio
    @staticmethod
    async def test_batch_processing_by_size(processor: WebSocketBatchProcessor, mock_handler: AsyncMock) -> None:
        """Test batch processing triggered by size limit."""
        processor.register_message_handler("test_channel", mock_handler)
        await processor.start()

        try:
            # Queue messages up to batch size limit
            for i in range(3):
                processor.queue_message("test_channel", {"type": "test", "id": i})

            # Wait a bit for processing
            await asyncio.sleep(0.1)

            # Should have triggered batch processing
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[0][0]
            assert len(call_args) == 3

        finally:
            await processor.stop()

    @pytest.mark.asyncio
    @staticmethod
    async def test_batch_processing_by_time(processor: WebSocketBatchProcessor, mock_handler: AsyncMock) -> None:
        """Test batch processing triggered by time limit."""
        processor.register_message_handler("test_channel", mock_handler)
        await processor.start()

        try:
            # Queue a single message
            processor.queue_message("test_channel", {"type": "test", "id": 1})

            # Wait for time-based flush (config has 0.05s max_batch_time)
            await asyncio.sleep(0.1)

            # Should have triggered batch processing due to time
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[0][0]
            assert len(call_args) == 1

        finally:
            await processor.stop()

    @staticmethod
    def test_message_optimization(processor: WebSocketBatchProcessor) -> None:
        """Test message optimization and combining."""
        # Test update message combining
        messages = [
            {"type": "session_update", "data": {"session1": "data1"}, "queued_at": 1.0},
            {"type": "session_update", "data": {"session2": "data2"}, "queued_at": 1.1},
            {
                "type": "session_update",
                "data": {"session1": "updated"},
                "queued_at": 1.2,
            },
        ]

        optimized = processor._optimize_messages(messages)

        # Should combine into single message
        assert len(optimized) == 1
        combined = cast("dict", optimized[0])
        assert combined["type"] == "session_update"
        assert "batch_info" in combined
        assert cast("dict", combined["data"])["session1"] == "updated"  # Latest data
        assert cast("dict", combined["data"])["session2"] == "data2"

    @staticmethod
    def test_log_message_optimization(processor: WebSocketBatchProcessor) -> None:
        """Test log message batch optimization."""
        messages = [
            {
                "type": "log_update",
                "data": {"level": "info", "message": "Log 1"},
                "queued_at": 1.0,
            },
            {
                "type": "log_update",
                "data": {"level": "error", "message": "Log 2"},
                "queued_at": 1.1,
            },
        ]

        optimized = processor._optimize_messages(messages)

        # Should combine into log batch
        assert len(optimized) == 1
        combined = cast("dict", optimized[0])
        assert combined["type"] == "log_batch"
        assert len(cast("dict", cast("dict", combined["data"])["entries"])) == 2
        assert cast("dict", combined["data"])["count"] == 2

    @staticmethod
    def test_get_statistics(processor: WebSocketBatchProcessor) -> None:
        """Test statistics reporting."""
        # Add some test data
        processor.queue_message("test1", {"type": "test"})
        processor.queue_message("test2", {"type": "test"})
        processor.stats["batches_sent"] = 5
        processor.stats["messages_processed"] = 25

        stats = processor.get_statistics()

        assert stats["batches_sent"] == 5
        assert stats["messages_processed"] == 25
        assert stats["avg_batch_size"] == 5.0
        assert stats["active_channels"] == 2
        assert stats["total_pending_messages"] == 2
        assert "config" in stats

    @staticmethod
    def test_update_config(processor: WebSocketBatchProcessor) -> None:
        """Test configuration updates."""
        processor.update_config(max_batch_size=15, max_batch_time=0.2)

        assert processor.config.max_batch_size == 15
        assert processor.config.max_batch_time == 0.2

    @staticmethod
    def test_clear_channel(processor: WebSocketBatchProcessor) -> None:
        """Test clearing channel messages."""
        processor.queue_message("test_channel", {"type": "test1"})
        processor.queue_message("test_channel", {"type": "test2"})
        processor.queue_message("other_channel", {"type": "test3"})

        assert len(processor.pending_messages["test_channel"]) == 2
        assert len(processor.pending_messages["other_channel"]) == 1

        processor.clear_channel("test_channel")

        assert len(processor.pending_messages["test_channel"]) == 0
        assert len(processor.pending_messages["other_channel"]) == 1

    @pytest.mark.asyncio
    @staticmethod
    async def test_error_handling(processor: WebSocketBatchProcessor) -> None:
        """Test error handling in message processing."""
        # Register a handler that raises an exception
        error_handler = AsyncMock(side_effect=Exception("Test error"))
        processor.register_message_handler("error_channel", error_handler)

        await processor.start()

        try:
            # Queue a message that will cause an error
            processor.queue_message("error_channel", {"type": "test"})

            # Wait for processing attempt
            await asyncio.sleep(0.1)

            # Handler should have been called despite error
            error_handler.assert_called_once()

            # Message should be re-queued for retry
            assert len(processor.pending_messages["error_channel"]) > 0

        finally:
            await processor.stop()

    @pytest.mark.asyncio
    @staticmethod
    async def test_start_stop_lifecycle(processor: WebSocketBatchProcessor) -> None:
        """Test processor start/stop lifecycle."""
        assert processor._processing_task is None

        await processor.start()
        assert processor._processing_task is not None
        assert not processor._processing_task.done()

        await processor.stop()
        assert processor._processing_task.done()

    @staticmethod
    def test_memory_size_calculation(processor: WebSocketBatchProcessor) -> None:
        """Test memory size calculation for queues."""
        test_queue = deque(
            [
                {"type": "test", "data": "small"},
                {"type": "test", "data": "larger message content"},
                {
                    "type": "test",
                    "data": {"complex": "object", "with": ["multiple", "values"]},
                },
            ]
        )

        size = processor._get_queue_memory_size(test_queue)
        assert size > 0
        assert isinstance(size, int)


if __name__ == "__main__":
    pytest.main([__file__])
