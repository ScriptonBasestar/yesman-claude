"""Asynchronous logger with queue-based processing for high performance."""

import asyncio
import logging
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from .batch_processor import BatchProcessor


class LogLevel(Enum):
    """Enhanced log levels with priorities."""

    TRACE = (5, "TRACE")
    DEBUG = (10, "DEBUG")
    INFO = (20, "INFO")
    WARNING = (30, "WARNING")
    ERROR = (40, "ERROR")
    CRITICAL = (50, "CRITICAL")

    def __init__(self, value: int, name: str):
        self.level_value = value
        self.level_name = name


@dataclass
class LogEntry:
    """Structured log entry."""

    level: LogLevel
    message: str
    timestamp: float = field(default_factory=time.time)
    logger_name: str = ""
    module: str = ""
    function: str = ""
    line_number: int = 0
    thread_id: int = field(default_factory=lambda: threading.get_ident())
    process_id: int = field(default_factory=lambda: os.getpid())
    extra_data: Dict[str, Any] = field(default_factory=dict)
    exception_info: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "level": self.level.level_name,
            "level_value": self.level.level_value,
            "message": self.message,
            "logger_name": self.logger_name,
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
            "thread_id": self.thread_id,
            "process_id": self.process_id,
            "extra_data": self.extra_data,
            "exception_info": self.exception_info,
        }


class AsyncLoggerConfig:
    """Configuration for AsyncLogger."""

    def __init__(
        self,
        name: str = "yesman_async",
        level: LogLevel = LogLevel.INFO,
        max_queue_size: int = 10000,
        batch_size: int = 50,
        flush_interval: float = 2.0,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_batch_processor: bool = True,
        log_format: str = "{timestamp} [{level}] {logger_name}: {message}",
        output_dir: Optional[Path] = None,
    ):
        self.name = name
        self.level = level
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_batch_processor = enable_batch_processor
        self.log_format = log_format
        self.output_dir = output_dir or Path.home() / ".yesman" / "logs"


class AsyncLogger:
    """High-performance asynchronous logger with queue-based processing."""

    _instance: Optional["AsyncLogger"] = None

    @classmethod
    def get_instance(cls, config: AsyncLoggerConfig = None) -> "AsyncLogger":
        """Get the singleton instance of the async logger."""
        if cls._instance is None:
            cls._instance = cls(config=config)
        elif config and cls._instance.config != config:
            # Re-initialize if config is different
            # Note: This might not be ideal for all singleton patterns
            cls._instance = cls(config=config)
        return cls._instance

    @classmethod
    async def reset_instance(cls):
        """Reset and stop the singleton instance."""
        if cls._instance:
            await cls._instance.stop()
        cls._instance = None


    def __init__(self, config: AsyncLoggerConfig = None):
        if AsyncLogger._instance is not None:
            raise RuntimeError("AsyncLogger is a singleton. Use get_instance().")

        self.config = config or AsyncLoggerConfig()

        # Queue for log entries
        self.log_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_queue_size)

        # Processing components
        self.batch_processor: Optional[BatchProcessor] = None
        if self.config.enable_batch_processor:
            self.batch_processor = BatchProcessor(
                max_batch_size=self.config.batch_size,
                max_batch_time=self.config.flush_interval,
                output_dir=self.config.output_dir,
            )

        # Standard logging integration
        self.standard_logger = logging.getLogger(self.config.name)
        self.standard_logger.setLevel(self.config.level.level_value)

        # Setup standard logging handlers if needed
        if self.config.enable_console and not self.standard_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.config.level.level_value)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )
            console_handler.setFormatter(formatter)
            self.standard_logger.addHandler(console_handler)

        # Statistics and monitoring
        self.stats = {
            "entries_queued": 0,
            "entries_processed": 0,
            "entries_dropped": 0,
            "queue_full_events": 0,
            "start_time": time.time(),
            "last_log_time": None,
        }

        # Processing task
        self._processing_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="async_logger")

        # Thread-safe logging from sync code
        self._sync_queue = asyncio.Queue()

    async def start(self):
        """Start the async logger."""
        if self._processing_task and not self._processing_task.done():
            return

        self._stop_event.clear()

        # Start batch processor
        if self.batch_processor:
            await self.batch_processor.start()

        # Start processing task
        self._processing_task = asyncio.create_task(self._processing_loop())

        self.standard_logger.info(f"AsyncLogger '{self.config.name}' started")

    async def stop(self):
        """Stop the async logger."""
        if not self._processing_task:
            return

        self._stop_event.set()

        # Process remaining items in queue
        while not self.log_queue.empty():
            try:
                entry = self.log_queue.get_nowait()
                await self._process_entry(entry)
            except asyncio.QueueEmpty:
                break

        # Wait for processing task to complete
        try:
            await asyncio.wait_for(self._processing_task, timeout=5.0)
        except asyncio.TimeoutError:
            self._processing_task.cancel()

        # Stop batch processor
        if self.batch_processor:
            await self.batch_processor.stop()

        # Cleanup executor
        self._executor.shutdown(wait=True)

        self.standard_logger.info(f"AsyncLogger '{self.config.name}' stopped")

    async def _processing_loop(self):
        """Main processing loop."""
        try:
            while not self._stop_event.is_set():
                try:
                    # Wait for log entry or timeout
                    entry = await asyncio.wait_for(
                        self.log_queue.get(),
                        timeout=self.config.flush_interval,
                    )
                    await self._process_entry(entry)
                    self.log_queue.task_done()

                except asyncio.TimeoutError:
                    # Timeout is normal, continue processing
                    continue

        except Exception as e:
            self.standard_logger.error(f"Error in async logger processing loop: {e}", exc_info=True)

    async def _process_entry(self, entry: LogEntry):
        """Process a single log entry."""
        try:
            self.stats["entries_processed"] += 1
            self.stats["last_log_time"] = time.time()

            # Send to standard logger (console/file)
            if self.config.enable_console or self.config.enable_file:
                await self._log_to_standard(entry)

            # Send to batch processor
            if self.batch_processor:
                self.batch_processor.add_entry(entry.to_dict())

        except Exception as e:
            self.standard_logger.error(f"Error processing log entry: {e}")

    async def _log_to_standard(self, entry: LogEntry):
        """Log entry to standard Python logging."""
        # Format message
        message = entry.message
        if entry.extra_data:
            extra_str = " | ".join([f"{k}={v}" for k, v in entry.extra_data.items()])
            message = f"{message} | {extra_str}"

        # Add exception info if present
        if entry.exception_info:
            message = f"{message}\n{entry.exception_info}"

        # Log to standard logger
        standard_level = entry.level.level_value
        self.standard_logger.log(standard_level, message)

    def _queue_entry(self, entry: LogEntry):
        """Queue a log entry (thread-safe)."""
        try:
            # Try to put entry in queue
            if self.log_queue.full():
                self.stats["queue_full_events"] += 1
                # Drop oldest entry to make room
                try:
                    self.log_queue.get_nowait()
                    self.stats["entries_dropped"] += 1
                except asyncio.QueueEmpty:
                    pass

            self.log_queue.put_nowait(entry)
            self.stats["entries_queued"] += 1

        except Exception as e:
            # Fallback to standard logging
            self.standard_logger.error(f"Failed to queue log entry: {e}")

    def log(self, level: LogLevel, message: str, **kwargs):
        """Log a message at specified level."""
        # Extract caller information
        frame = None
        try:
            import inspect

            frame = inspect.currentframe().f_back
            module = frame.f_globals.get("__name__", "")
            function = frame.f_code.co_name
            line_number = frame.f_lineno
        except (AttributeError, KeyError, IndexError):
            # Handle frame inspection errors gracefully
            module = function = ""
            line_number = 0
        finally:
            del frame  # Prevent reference cycles

        # Create log entry
        entry = LogEntry(
            level=level,
            message=str(message),
            logger_name=self.config.name,
            module=module,
            function=function,
            line_number=line_number,
            extra_data=kwargs,
        )

        # Add exception info if logging an exception
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            try:
                import sys

                if sys.exc_info()[0] is not None:
                    entry.exception_info = traceback.format_exc()
            except Exception as e:
                # Ignore errors in exception info collection
                self.standard_logger.debug(f"Failed to capture exception info: {e}", exc_info=False)

        # Queue the entry
        self._queue_entry(entry)

    # Convenience methods for different log levels
    def trace(self, message: str, **kwargs):
        """Log a trace message."""
        self.log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log an info message."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log an error message."""
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self.log(LogLevel.CRITICAL, message, **kwargs)

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    def get_statistics(self) -> Dict[str, Any]:
        """Get logger statistics."""
        batch_stats = {}
        if self.batch_processor:
            batch_stats = self.batch_processor.get_statistics()

        uptime = time.time() - self.stats["start_time"]
        processing_rate = self.stats["entries_processed"] / uptime if uptime > 0 else 0

        return {
            **self.stats,
            "current_queue_size": self.log_queue.qsize(),
            "uptime_seconds": uptime,
            "processing_rate_eps": processing_rate,
            "batch_processor_stats": batch_stats,
        }

    def set_level(self, level: LogLevel):
        """Change the logging level."""
        self.config.level = level
        self.standard_logger.setLevel(level.level_value)

    async def flush(self):
        """Force flush all pending log entries."""
        # Wait for queue to be empty
        await self.log_queue.join()

        # Flush batch processor if available
        if self.batch_processor:
            await self.batch_processor._flush_pending_entries()
