#!/usr/bin/env python3

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""AsyncEventBus - Core event-driven architecture component for Yesman-Claude.

This module provides the foundational event bus infrastructure that enables
asynchronous, decoupled communication between system components. It supports
high-throughput event processing, error isolation, and comprehensive monitoring.

Key Features:
- Non-blocking event publishing and processing
- Concurrent event handler execution
- Error isolation preventing cascading failures
- Performance metrics and monitoring
- Type-safe event handling
- Graceful shutdown with cleanup
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any
from weakref import WeakSet

# Local imports


class EventPriority(Enum):
    """Event priority levels for processing order."""

    CRITICAL = "critical"  # System-critical events (errors, shutdowns)
    HIGH = "high"  # Important state changes
    NORMAL = "normal"  # Regular operations
    LOW = "low"  # Background updates, metrics


class EventType(Enum):
    """Standard event types in the Yesman-Claude system."""

    # Session lifecycle events
    SESSION_CREATED = "session.created"
    SESSION_DESTROYED = "session.destroyed"
    SESSION_STARTED = "session.started"
    SESSION_STOPPED = "session.stopped"
    SESSION_ERROR = "session.error"

    # Claude interaction events
    CLAUDE_RESPONSE = "claude.response"
    CLAUDE_PROMPT_SENT = "claude.prompt_sent"
    CLAUDE_ERROR = "claude.error"
    CLAUDE_STATUS_CHANGED = "claude.status_changed"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    # Performance events
    PERFORMANCE_ALERT = "performance.alert"
    PERFORMANCE_METRICS = "performance.metrics"

    # Dashboard events
    DASHBOARD_UPDATE = "dashboard.update"
    DASHBOARD_REFRESH = "dashboard.refresh"

    # Custom events (for extensions)
    CUSTOM = "custom"


@dataclass
class Event:
    """Event data structure for the async event bus.

    Attributes:
        type: Event type identifier
        data: Event payload data
        timestamp: Event creation timestamp
        source: Component that created the event
        correlation_id: Optional correlation ID for request tracking
        priority: Event processing priority
        metadata: Additional event metadata
    """

    type: EventType | str
    data: dict[str, Any]
    timestamp: float
    source: str
    correlation_id: str | None = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary representation."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        event_dict = self.to_dict()
        # Convert enum values to strings for JSON serialization
        if isinstance(event_dict["type"], EventType):
            event_dict["type"] = event_dict["type"].value
        if isinstance(event_dict["priority"], EventPriority):
            event_dict["priority"] = event_dict["priority"].value
        return json.dumps(event_dict, default=str)


@dataclass
class EventMetrics:
    """Metrics for event bus performance monitoring."""

    events_published: int = 0
    events_processed: int = 0
    events_dropped: int = 0
    processing_errors: int = 0
    handler_errors: int = 0
    average_processing_time: float = 0.0
    queue_size: int = 0
    active_handlers: int = 0

    # Enhanced queue depth monitoring
    max_queue_depth: int = 0
    queue_depth_history: list[int] = None
    queue_utilization_percent: float = 0.0
    queue_backlog_duration_ms: float = 0.0
    peak_queue_depth: int = 0
    queue_overflow_events: int = 0

    def __post_init__(self) -> None:
        """Initialize queue depth history after object creation."""
        if self.queue_depth_history is None:
            self.queue_depth_history = []

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.events_published = 0
        self.events_processed = 0
        self.events_dropped = 0
        self.processing_errors = 0
        self.handler_errors = 0
        self.average_processing_time = 0.0
        self.queue_size = 0
        self.active_handlers = 0

        # Reset enhanced metrics
        self.max_queue_depth = 0
        self.queue_depth_history = []
        self.queue_utilization_percent = 0.0
        self.queue_backlog_duration_ms = 0.0
        self.peak_queue_depth = 0
        self.queue_overflow_events = 0


class AsyncEventBus:
    """High-performance asynchronous event bus for inter-component communication.

    The AsyncEventBus provides a decoupled communication mechanism that allows
    components to publish events and subscribe to events of interest without
    direct coupling. It ensures non-blocking operations and provides comprehensive
    error handling and monitoring.
    """

    def __init__(self, max_queue_size: int = 10000, worker_count: int = 4) -> None:
        """Initialize the AsyncEventBus.

        Args:
            max_queue_size: Maximum number of events in the queue
            worker_count: Number of concurrent event processing workers
        """
        self._subscribers: dict[EventType | str, list[Callable]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._processing_tasks: list[asyncio.Task] = []
        self._is_running: bool = False
        self._shutdown_event = asyncio.Event()
        self._metrics = EventMetrics()
        self._processing_times: deque = deque(maxlen=1000)  # Keep last 1000 processing times
        self._worker_count = worker_count

        # Weak reference set to prevent memory leaks
        self._handler_refs: WeakSet = WeakSet()

        # Logger for event bus operations
        self.logger = logging.getLogger(__name__)

        # Event filtering capabilities
        self._event_filters: list[Callable[[Event], bool]] = []

        # Performance monitoring
        self._last_metrics_report = time.time()
        self._metrics_interval = 60.0  # Report metrics every 60 seconds

        # Enhanced queue depth monitoring
        self._queue_depth_samples: deque = deque(maxlen=100)  # Keep last 100 samples
        self._last_queue_update = time.time()
        self._queue_update_interval = 1.0  # Update queue metrics every second

    async def start(self) -> None:
        """Start the event bus processing.

        Initializes worker tasks for concurrent event processing and begins
        monitoring system performance.
        """
        if self._is_running:
            self.logger.warning("Event bus is already running")
            return

        self._is_running = True
        self._shutdown_event.clear()

        # Start worker tasks for concurrent processing
        self._processing_tasks = [asyncio.create_task(self._event_processing_worker(i)) for i in range(self._worker_count)]

        # Start metrics reporting task
        self._processing_tasks.append(asyncio.create_task(self._metrics_reporter()))

        self.logger.info(f"AsyncEventBus started with {self._worker_count} workers")

        # Publish startup event
        await self.publish(
            Event(
                type=EventType.SYSTEM_STARTUP,
                data={"worker_count": self._worker_count, "max_queue_size": self._event_queue.maxsize},
                timestamp=time.time(),
                source="async_event_bus",
                priority=EventPriority.HIGH,
            )
        )

    async def stop(self, timeout: float = 10.0) -> None:
        """Gracefully stop the event bus.

        Args:
            timeout: Maximum time to wait for graceful shutdown
        """
        if not self._is_running:
            return

        self.logger.info("Stopping AsyncEventBus...")

        # Publish shutdown event
        try:
            await self.publish(Event(type=EventType.SYSTEM_SHUTDOWN, data={"graceful": True}, timestamp=time.time(), source="async_event_bus", priority=EventPriority.CRITICAL))
        except Exception as e:
            self.logger.debug(f"Ignoring shutdown event error: {e}")

        # Signal shutdown to all workers
        self._is_running = False
        self._shutdown_event.set()

        # Wait for all processing tasks to complete
        if self._processing_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*self._processing_tasks, return_exceptions=True), timeout=timeout)
            except TimeoutError:
                self.logger.warning("Event bus shutdown timed out, cancelling tasks")
                for task in self._processing_tasks:
                    if not task.done():
                        task.cancel()

                # Wait a bit more for cancellation
                try:
                    await asyncio.wait_for(asyncio.gather(*self._processing_tasks, return_exceptions=True), timeout=2.0)
                except TimeoutError:
                    pass

        self._processing_tasks.clear()
        self.logger.info("AsyncEventBus stopped")

    def subscribe(self, event_type: EventType | str, handler: Callable) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of events to subscribe to
            handler: Async or sync function to handle events
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        self._handler_refs.add(handler)
        self._metrics.active_handlers = len(self._handler_refs)

        self.logger.debug(f"Subscribed handler to {event_type}")

    def unsubscribe(self, event_type: EventType | str, handler: Callable) -> bool:
        """Unsubscribe a handler from events.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove

        Returns:
            True if handler was removed, False if not found
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]

                # Update metrics
                self._metrics.active_handlers = len(self._handler_refs)

                self.logger.debug(f"Unsubscribed handler from {event_type}")
                return True
            except ValueError:
                pass

        return False

    def add_event_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """Add an event filter that can drop events before processing.

        Args:
            filter_func: Function that returns True to allow event, False to drop
        """
        self._event_filters.append(filter_func)

    async def publish(self, event: Event) -> bool:
        """Publish an event to the bus.

        Args:
            event: Event to publish

        Returns:
            True if event was queued successfully, False if dropped
        """
        if not self._is_running:
            self.logger.warning("Cannot publish event - event bus not running")
            return False

        # Apply event filters
        for filter_func in self._event_filters:
            try:
                if not filter_func(event):
                    self.logger.debug(f"Event {event.type} dropped by filter")
                    return False
            except Exception:
                self.logger.exception("Error in event filter")
                continue

        try:
            # Try to put event in queue immediately (non-blocking)
            self._event_queue.put_nowait(event)
            self._metrics.events_published += 1

            # Update enhanced queue depth metrics
            self._update_queue_depth_metrics()
            return True

        except asyncio.QueueFull:
            # Queue is full - implement overflow strategy
            self._metrics.events_dropped += 1
            self.logger.warning(f"Event queue full, dropping event: {event.type}")

            # For critical events, try to make room by dropping low priority events
            if event.priority == EventPriority.CRITICAL:
                await self._make_queue_room()
                try:
                    self._event_queue.put_nowait(event)
                    self._metrics.events_published += 1
                    return True
                except asyncio.QueueFull:
                    pass

            return False

    async def publish_and_wait(self, event: Event, timeout: float = 5.0) -> list[Any]:
        """Publish an event and wait for all handlers to complete.

        Args:
            event: Event to publish
            timeout: Maximum time to wait for handlers

        Returns:
            List of handler results
        """
        if not self._is_running:
            raise RuntimeError("Bus not running")  # noqa: TRY003

        # Get handlers for this event type
        handlers = self._subscribers.get(event.type, [])
        if not handlers:
            return []

        # Execute handlers directly for synchronous processing
        results = []
        async with asyncio.TaskGroup() as tg:
            handler_tasks = [tg.create_task(self._safe_handler_call(handler, event)) for handler in handlers]

        results = [task.result() for task in handler_tasks]
        return results

    async def _event_processing_worker(self, worker_id: int) -> None:
        """Event processing worker that handles events from the queue.

        Args:
            worker_id: Unique identifier for this worker
        """
        self.logger.debug(f"Event processing worker {worker_id} started")

        while self._is_running:
            try:
                # Wait for event or shutdown signal
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                except TimeoutError:
                    continue  # Check shutdown condition

                # Process the event
                start_time = time.perf_counter()
                await self._handle_event(event)
                processing_time = time.perf_counter() - start_time

                # Update metrics
                self._processing_times.append(processing_time)
                self._metrics.events_processed += 1

                # Update enhanced queue depth metrics
                self._update_queue_depth_metrics()

                # Calculate rolling average processing time
                if self._processing_times:
                    self._metrics.average_processing_time = sum(self._processing_times) / len(self._processing_times)

                # Mark task as done
                self._event_queue.task_done()

            except asyncio.CancelledError:
                self.logger.debug(f"Event processing worker {worker_id} cancelled")
                break
            except Exception:
                self._metrics.processing_errors += 1
                self.logger.exception(f"Error in event processing worker {worker_id}")

        self.logger.debug(f"Event processing worker {worker_id} stopped")

    async def _handle_event(self, event: Event) -> None:
        """Handle an individual event by calling all registered handlers.

        Args:
            event: Event to handle
        """
        handlers = self._subscribers.get(event.type, [])
        if not handlers:
            return

        # Execute all handlers concurrently with error isolation
        handler_tasks = [self._safe_handler_call(handler, event) for handler in handlers]

        if handler_tasks:
            # Use gather with return_exceptions to prevent one handler failure
            # from affecting others
            await asyncio.gather(*handler_tasks, return_exceptions=True)

    async def _safe_handler_call(self, handler: Callable, event: Event) -> Any:
        """Safely call an event handler with proper error handling.

        Args:
            handler: Handler function to call
            event: Event to pass to handler

        Returns:
            Handler result or None if error occurred
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(event)
            # Run sync handler in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, handler, event)

        except Exception as e:
            self._metrics.handler_errors += 1
            self.logger.exception(f"Error in event handler for {event.type}")

            # Publish error event for monitoring
            try:
                error_event = Event(
                    type=EventType.SYSTEM_ERROR,
                    data={"error": str(e), "handler": str(handler), "original_event": event.to_dict()},
                    timestamp=time.time(),
                    source="async_event_bus",
                    priority=EventPriority.HIGH,
                )
                # Use put_nowait to avoid blocking in error handler
                if not self._event_queue.full():
                    self._event_queue.put_nowait(error_event)
            except Exception as e:
                self.logger.debug(f"Error in error event publishing: {e}")

            return None

    async def _make_queue_room(self) -> None:
        """Try to make room in the queue by dropping low priority events."""
        try:
            # This is a simple implementation - in practice, you might want
            # a more sophisticated queue management strategy
            temp_events = []
            dropped_count = 0

            # Remove up to 10% of queue, prioritizing low priority events
            max_to_remove = max(1, self._event_queue.qsize() // 10)

            while not self._event_queue.empty() and dropped_count < max_to_remove:
                try:
                    event = self._event_queue.get_nowait()
                    if event.priority == EventPriority.LOW:
                        dropped_count += 1
                        self._metrics.events_dropped += 1
                    else:
                        temp_events.append(event)
                except asyncio.QueueEmpty:
                    break

            # Put back the events we want to keep
            for event in temp_events:
                try:
                    self._event_queue.put_nowait(event)
                except asyncio.QueueFull:
                    break

            if dropped_count > 0:
                self.logger.info(f"Dropped {dropped_count} low priority events to make room")

        except Exception:
            self.logger.exception("Error making queue room")

    async def _metrics_reporter(self) -> None:
        """Periodically report event bus metrics."""
        while self._is_running:
            try:
                await asyncio.sleep(self._metrics_interval)

                if time.time() - self._last_metrics_report >= self._metrics_interval:
                    await self._publish_metrics()
                    self._last_metrics_report = time.time()

            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Error in metrics reporter")

    async def _publish_metrics(self) -> None:
        """Publish current event bus metrics."""
        try:
            metrics_event = Event(
                type=EventType.PERFORMANCE_METRICS,
                data={"component": "async_event_bus", "metrics": asdict(self._metrics), "subscriber_count": len(self._subscribers), "queue_maxsize": self._event_queue.maxsize},
                timestamp=time.time(),
                source="async_event_bus",
                priority=EventPriority.LOW,
            )

            # Use put_nowait to avoid blocking in metrics reporting
            if not self._event_queue.full():
                self._event_queue.put_nowait(metrics_event)

        except Exception:
            self.logger.exception("Error publishing metrics")

    def _update_queue_depth_metrics(self) -> None:
        """Update enhanced queue depth monitoring metrics."""
        current_time = time.time()
        current_depth = self._event_queue.qsize()
        max_size = self._event_queue.maxsize

        # Update basic metrics
        self._metrics.queue_size = current_depth

        # Update peak tracking
        self._metrics.peak_queue_depth = max(self._metrics.peak_queue_depth, current_depth)

        # Update max depth for this interval
        self._metrics.max_queue_depth = max(self._metrics.max_queue_depth, current_depth)

        # Calculate utilization percentage
        if max_size > 0:
            self._metrics.queue_utilization_percent = (current_depth / max_size) * 100

        # Update queue depth history (every second)
        if current_time - self._last_queue_update >= self._queue_update_interval:
            self._queue_depth_samples.append(current_depth)
            self._metrics.queue_depth_history = list(self._queue_depth_samples)
            self._last_queue_update = current_time

            # Estimate backlog processing duration based on recent processing rate
            if self._processing_times and current_depth > 0:
                avg_processing_time = sum(self._processing_times) / len(self._processing_times)
                self._metrics.queue_backlog_duration_ms = current_depth * avg_processing_time * 1000

            # Track overflow events
            if current_depth >= max_size * 0.9:  # 90% full
                self._metrics.queue_overflow_events += 1

    def get_metrics(self) -> EventMetrics:
        """Get current event bus metrics.

        Returns:
            Current metrics snapshot
        """
        # Update enhanced queue depth metrics
        self._update_queue_depth_metrics()
        return self._metrics

    def get_subscriber_count(self, event_type: EventType | str = None) -> int:
        """Get number of subscribers for an event type or total.

        Args:
            event_type: Specific event type or None for total

        Returns:
            Number of subscribers
        """
        if event_type is not None:
            return len(self._subscribers.get(event_type, []))
        return sum(len(handlers) for handlers in self._subscribers.values())

    def is_running(self) -> bool:
        """Check if the event bus is currently running."""
        return self._is_running

    async def wait_for_empty_queue(self, timeout: float = 10.0) -> bool:
        """Wait for the event queue to be empty.

        Args:
            timeout: Maximum time to wait

        Returns:
            True if queue became empty, False if timeout
        """
        try:
            await asyncio.wait_for(self._event_queue.join(), timeout=timeout)
            return True
        except TimeoutError:
            return False


# Global event bus instance
# This provides a convenient singleton for the application
_global_event_bus: AsyncEventBus | None = None


def get_event_bus() -> AsyncEventBus:
    """Get the global event bus instance.

    Returns:
        Global AsyncEventBus instance
    """
    global _global_event_bus  # noqa: PLW0603
    if _global_event_bus is None:
        _global_event_bus = AsyncEventBus()
    return _global_event_bus


async def initialize_global_event_bus(**kwargs) -> AsyncEventBus:
    """Initialize and start the global event bus.

    Args:
        **kwargs: Arguments to pass to AsyncEventBus constructor

    Returns:
        Initialized global event bus
    """
    global _global_event_bus  # noqa: PLW0603
    if _global_event_bus is None:
        _global_event_bus = AsyncEventBus(**kwargs)

    if not _global_event_bus.is_running():
        await _global_event_bus.start()

    return _global_event_bus


async def shutdown_global_event_bus() -> None:
    """Shutdown the global event bus."""
    global _global_event_bus  # noqa: PLW0603
    if _global_event_bus is not None:
        await _global_event_bus.stop()
        _global_event_bus = None
