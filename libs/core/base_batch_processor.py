#!/usr/bin/env python3
"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Generic base batch processor for handling items in batches.

This module provides a thread-safe, async-compatible base class for
batch processing various types of items with configurable size and time limits.
"""

import asyncio
import contextlib
import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from libs.core.mixins import StatisticsProviderMixin

# Type variable for generic batch items
T = TypeVar("T")

# Type variable for batch container
B = TypeVar("B")


@dataclass
class BatchStatistics:
    """Statistics for batch processing."""

    total_batches: int = 0
    total_items: int = 0
    failed_batches: int = 0
    processing_time_ms: float = 0.0
    last_batch_time: datetime | None = None
    average_batch_size: float = 0.0
    average_processing_time_ms: float = 0.0


class BaseBatchProcessor(Generic[T, B], StatisticsProviderMixin, ABC):
    """Generic base class for batch processing.

    Type Parameters:
        T: The type of items to be batched
        B: The type of batch container

    This class provides:
    - Async lifecycle management (start/stop)
    - Configurable batch size and time limits
    - Thread-safe item addition
    - Automatic flush based on size/time thresholds
    - Statistics tracking
    - Graceful shutdown with pending items processing
    """

    def __init__(
        self,
        batch_size: int = 100,
        flush_interval: float = 1.0,
        max_pending_batches: int = 1000,
    ) -> None:
        """Initialize the batch processor.

        Args:
            batch_size: Maximum number of items per batch
            flush_interval: Maximum time (seconds) before forcing a flush
            max_pending_batches: Maximum number of pending batches before blocking
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_pending_batches = max_pending_batches

        # Internal state
        self._pending_items: deque[T] = deque()
        self._pending_batches: deque[B] = deque(maxlen=max_pending_batches)
        self._lock = threading.Lock()
        self._running = False
        self._processing_task: asyncio.Task | None = None
        self._stats = BatchStatistics()
        self._last_flush_time = time.time()

        # Logger
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @abstractmethod
    @staticmethod
    def create_batch(items: list[T]) -> B:
        """Create a batch container from a list of items.

        Args:
            items: List of items to batch

        Returns:
            A batch container of type B
        """
        raise NotImplementedError

    @abstractmethod
    @staticmethod
    async def process_batch(batch: B) -> None:
        """Process a single batch.

        This method should implement the actual batch processing logic.

        Args:
            batch: The batch to process

        Raises:
            Exception: If batch processing fails
        """
        raise NotImplementedError

    def add(self, item: T) -> None:
        """Add an item to the pending queue.

        Thread-safe method to add items for batching.

        Args:
            item: Item to add to the batch
        """
        with self._lock:
            self._pending_items.append(item)
            self._stats.total_items += 1

            # Check if we should flush immediately based on size
            if len(self._pending_items) >= self.batch_size:
                self._flush_pending_items()

    def _flush_pending_items(self) -> None:
        """Flush pending items to a batch.

        Must be called while holding the lock.
        """
        if not self._pending_items:
            return

        # Create batch from pending items
        items = list(self._pending_items)
        self._pending_items.clear()

        batch = self.create_batch(items)
        self._pending_batches.append(batch)
        self._stats.total_batches += 1
        self._last_flush_time = time.time()

        self.logger.debug(f"Created batch with {len(items)} items")  # noqa: G004

    async def start(self) -> None:
        """Start the batch processor."""
        if self._running:
            self.logger.warning("Batch processor already running")
            return

        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Batch processor started")

    async def stop(self) -> None:
        """Stop the batch processor and flush remaining items."""
        if not self._running:
            return

        self._running = False

        # Flush any remaining items
        with self._lock:
            self._flush_pending_items()

        # Process remaining batches
        while self._pending_batches:
            batch = self._pending_batches.popleft()
            try:
                await self.process_batch(batch)
            except Exception as e:
                self.logger.exception("Error processing final batch")  # noqa: G004
                self._stats.failed_batches += 1

        # Wait for processing task to complete
        if self._processing_task:
            self._processing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._processing_task

        self.logger.info("Batch processor stopped")

    async def _processing_loop(self) -> None:
        """Main processing loop for batches."""
        while self._running:
            try:
                # Check if we need to flush based on time
                current_time = time.time()
                time_since_last_flush = current_time - self._last_flush_time

                with self._lock:
                    if self._pending_items and time_since_last_flush >= self.flush_interval:
                        self._flush_pending_items()

                # Process pending batches
                while self._pending_batches and self._running:
                    batch = self._pending_batches.popleft()
                    start_time = time.time()

                    try:
                        await self.process_batch(batch)
                        processing_time = (time.time() - start_time) * 1000

                        # Update statistics
                        self._stats.processing_time_ms += processing_time
                        self._stats.last_batch_time = datetime.now(UTC)

                        # Calculate averages
                        if self._stats.total_batches > 0:
                            self._stats.average_processing_time_ms = self._stats.processing_time_ms / self._stats.total_batches
                            self._stats.average_batch_size = self._stats.total_items / self._stats.total_batches

                    except Exception as e:
                        self.logger.error(f"Error processing batch: {e}", exc_info=True)  # noqa: G004
                        self._stats.failed_batches += 1

                # Small sleep to prevent busy waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}", exc_info=True)  # noqa: G004
                await asyncio.sleep(1.0)  # Back off on error

    def get_statistics(self) -> dict[str, Any]:
        """Get current batch processor statistics.

        Returns:
            Dictionary containing processing statistics
        """
        with self._lock:
            pending_items = len(self._pending_items)
            pending_batches = len(self._pending_batches)

        return {
            "total_batches": self._stats.total_batches,
            "total_items": self._stats.total_items,
            "failed_batches": self._stats.failed_batches,
            "success_rate": ((self._stats.total_batches - self._stats.failed_batches) / self._stats.total_batches * 100 if self._stats.total_batches > 0 else 0.0),
            "average_batch_size": round(self._stats.average_batch_size, 2),
            "average_processing_time_ms": round(self._stats.average_processing_time_ms, 2),
            "pending_items": pending_items,
            "pending_batches": pending_batches,
            "last_batch_time": self._stats.last_batch_time.isoformat() if self._stats.last_batch_time else None,
            "is_running": self._running,
            "config": {
                "batch_size": self.batch_size,
                "flush_interval": self.flush_interval,
                "max_pending_batches": self.max_pending_batches,
            },
        }

    async def wait_for_pending(self, timeout: float = 30.0) -> bool:
        """Wait for all pending items and batches to be processed.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if all items were processed, False if timeout occurred
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self._lock:
                if not self._pending_items and not self._pending_batches:
                    return True

            await asyncio.sleep(0.1)

        return False

    def __repr__(self) -> str:
        """String representation of the batch processor."""
        return f"{self.__class__.__name__}(batch_size={self.batch_size}, flush_interval={self.flush_interval}, running={self._running})"
