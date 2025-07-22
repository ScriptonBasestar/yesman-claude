import asyncio
from dataclasses import dataclass

import pytest

from libs.core.base_batch_processor import BaseBatchProcessor

# !/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Tests for the base batch processor."""


@dataclass
class TestBatch:
    """Test batch container."""

    items: list[str]
    size: int = 0

    def __post_init__(self) -> object:
        self.size = len(self.items)


class TestBatchProcessor(BaseBatchProcessor[str, TestBatch]):
    """Test implementation of batch processor."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.processed_batches: list[TestBatch] = []
        self.process_delay = 0.0  # For testing timing

    @staticmethod
    def create_batch(items: list[str]) -> TestBatch:
        """Create a test batch."""
        return TestBatch(items=items.copy())

    async def process_batch(self, batch: TestBatch) -> None:
        """Process a test batch."""
        if self.process_delay > 0:
            await asyncio.sleep(self.process_delay)
        self.processed_batches.append(batch)


class TestBaseBatchProcessor:
    """Test cases for base batch processor."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_basic_functionality() -> None:
        """Test basic batch processing functionality."""
        processor = TestBatchProcessor(batch_size=3, flush_interval=1.0)
        await processor.start()

        # Add items
        for i in range(5):
            processor.add(f"item_{i}")

        # Wait a bit for processing
        await asyncio.sleep(0.2)

        # Should have one batch processed (first 3 items)
        assert len(processor.processed_batches) == 1
        assert processor.processed_batches[0].size == 3

        # Wait for flush interval
        await asyncio.sleep(1.2)

        # Should have second batch with remaining items
        assert len(processor.processed_batches) == 2
        assert processor.processed_batches[1].size == 2

        await processor.stop()

    @pytest.mark.asyncio
    @staticmethod
    async def test_immediate_flush_on_size() -> None:
        """Test that batches are flushed immediately when size is reached."""
        processor = TestBatchProcessor(batch_size=2, flush_interval=10.0)
        await processor.start()

        # Add exactly batch_size items
        processor.add("item_1")
        processor.add("item_2")

        # Should flush immediately
        await asyncio.sleep(0.2)
        assert len(processor.processed_batches) == 1
        assert processor.processed_batches[0].items == ["item_1", "item_2"]

        await processor.stop()

    @pytest.mark.asyncio
    @staticmethod
    async def test_time_based_flush() -> None:
        """Test that batches are flushed based on time interval."""
        processor = TestBatchProcessor(batch_size=10, flush_interval=0.5)
        await processor.start()

        # Add fewer items than batch size
        processor.add("item_1")

        # Wait for flush interval
        await asyncio.sleep(0.7)

        # Should have flushed based on time
        assert len(processor.processed_batches) == 1
        assert processor.processed_batches[0].items == ["item_1"]

        await processor.stop()

    @pytest.mark.asyncio
    @staticmethod
    async def test_stop_flushes_pending() -> None:
        """Test that stopping flushes all pending items."""
        processor = TestBatchProcessor(batch_size=5, flush_interval=10.0)
        await processor.start()

        # Add items but don't reach batch size
        processor.add("item_1")
        processor.add("item_2")

        # Stop should flush pending items
        await processor.stop()

        assert len(processor.processed_batches) == 1
        assert processor.processed_batches[0].items == ["item_1", "item_2"]

    @pytest.mark.asyncio
    @staticmethod
    async def test_statistics() -> None:
        """Test statistics collection."""
        processor = TestBatchProcessor(batch_size=2)
        await processor.start()

        # Add items
        for i in range(5):
            processor.add(f"item_{i}")

        # Wait for processing
        await asyncio.sleep(0.5)

        stats = processor.get_statistics()
        assert stats["total_items"] == 5
        assert stats["total_batches"] == 2  # 2 + 2 items in first two batches
        assert stats["pending_items"] == 1  # 1 item pending
        assert stats["is_running"] is True

        await processor.stop()

        # After stop, all items should be processed
        final_stats = processor.get_statistics()
        assert final_stats["total_batches"] == 3
        assert final_stats["pending_items"] == 0
        assert final_stats["is_running"] is False

    @pytest.mark.asyncio
    @staticmethod
    async def test_wait_for_pending() -> None:
        """Test waiting for pending items to be processed."""
        processor = TestBatchProcessor(batch_size=2)
        processor.process_delay = 0.1  # Add delay to test waiting
        await processor.start()

        # Add items
        for i in range(4):
            processor.add(f"item_{i}")

        # Wait for all pending items
        processed = await processor.wait_for_pending(timeout=2.0)
        assert processed is True
        assert len(processor.processed_batches) == 2

        await processor.stop()

    @pytest.mark.asyncio
    @staticmethod
    async def test_concurrent_adds() -> None:
        """Test thread-safe concurrent additions."""
        processor = TestBatchProcessor(batch_size=5)
        await processor.start()

        async def add_items(prefix: str, count: int) -> None:
            for i in range(count):
                processor.add(f"{prefix}_{i}")
                await asyncio.sleep(0.01)

        # Add items concurrently
        await asyncio.gather(
            add_items("A", 10),
            add_items("B", 10),
            add_items("C", 10),
        )

        await processor.wait_for_pending()
        await processor.stop()

        # Should have processed all 30 items
        total_items = sum(batch.size for batch in processor.processed_batches)
        assert total_items == 30

    @pytest.mark.asyncio
    @staticmethod
    async def test_error_handling() -> None:
        """Test error handling in batch processing."""

        class ErrorBatchProcessor(TestBatchProcessor):
            @staticmethod
            async def process_batch(batch: TestBatch) -> None:
                if "error" in batch.items[0]:
                    msg = "Test error"
                    raise ValueError(msg)
                await super().process_batch(batch)

        processor = ErrorBatchProcessor(batch_size=2)
        await processor.start()

        # Add normal items
        processor.add("item_1")
        processor.add("item_2")

        # Add error items
        processor.add("error_1")
        processor.add("error_2")

        await asyncio.sleep(0.5)

        stats = processor.get_statistics()
        assert stats["failed_batches"] == 1
        assert stats["total_batches"] == 2
        assert len(processor.processed_batches) == 1  # Only successful batch

        await processor.stop()

    @staticmethod
    def test_repr() -> None:
        """Test string representation."""
        processor = TestBatchProcessor(batch_size=100, flush_interval=2.0)
        repr_str = repr(processor)
        assert "TestBatchProcessor" in repr_str
        assert "batch_size=100" in repr_str
        assert "flush_interval=2.0" in repr_str
