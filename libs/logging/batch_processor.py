"""Batch log processor for optimized I/O operations."""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Deque, Dict, Any, Callable
import json
import gzip


@dataclass
class LogBatch:
    """A batch of log entries to be processed together."""
    entries: List[Dict[str, Any]]
    timestamp: float
    batch_id: str
    size_bytes: int = 0
    
    def __post_init__(self):
        """Calculate size after initialization."""
        if not self.size_bytes:
            self.size_bytes = sum(len(str(entry)) for entry in self.entries)


class BatchProcessor:
    """Processes log entries in batches for optimized I/O."""
    
    def __init__(self, 
                 max_batch_size: int = 100,
                 max_batch_time: float = 5.0,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 compression_enabled: bool = True,
                 output_dir: Optional[Path] = None):
        
        self.max_batch_size = max_batch_size
        self.max_batch_time = max_batch_time
        self.max_file_size = max_file_size
        self.compression_enabled = compression_enabled
        self.output_dir = output_dir or Path.home() / ".yesman" / "logs"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Batch management
        self.pending_entries: Deque[Dict[str, Any]] = deque()
        self.last_flush_time = time.time()
        self.batch_counter = 0
        self.current_file_size = 0
        self.current_log_file: Optional[Path] = None
        
        # Statistics
        self.stats = {
            'batches_processed': 0,
            'entries_processed': 0,
            'bytes_written': 0,
            'compression_ratio': 1.0,
            'avg_batch_size': 0,
            'files_created': 0
        }
        
        # Processing task
        self._processing_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        self.logger = logging.getLogger("yesman.batch_processor")
        
    async def start(self):
        """Start the batch processing task."""
        if self._processing_task and not self._processing_task.done():
            self.logger.warning("Batch processor already running")
            return
            
        self._stop_event.clear()
        self._processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Batch processor started")
        
    async def stop(self):
        """Stop the batch processing task."""
        if not self._processing_task:
            return
            
        self._stop_event.set()
        
        try:
            await asyncio.wait_for(self._processing_task, timeout=10.0)
        except asyncio.TimeoutError:
            self.logger.warning("Batch processor stop timeout, cancelling task")
            self._processing_task.cancel()
            
        # Flush any remaining entries
        await self._flush_pending_entries()
        
        self.logger.info("Batch processor stopped")
        
    def add_entry(self, entry: Dict[str, Any]):
        """Add a log entry to the processing queue."""
        # Add timestamp if not present
        if 'timestamp' not in entry:
            entry['timestamp'] = time.time()
            
        self.pending_entries.append(entry)
        
        # Check if we should flush immediately
        if len(self.pending_entries) >= self.max_batch_size:
            # We can't await here, so we'll let the processing loop handle it
            pass
            
    async def _processing_loop(self):
        """Main processing loop that handles batching and flushing."""
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
                
                should_flush = (
                    len(self.pending_entries) >= self.max_batch_size or
                    (len(self.pending_entries) > 0 and 
                     time.time() - self.last_flush_time >= self.max_batch_time)
                )
                
                if should_flush:
                    await self._flush_pending_entries()
                    
        except Exception as e:
            self.logger.error(f"Error in batch processing loop: {e}", exc_info=True)
            
    async def _flush_pending_entries(self):
        """Flush pending entries to storage."""
        if not self.pending_entries:
            return
            
        # Create batch
        entries = []
        while self.pending_entries and len(entries) < self.max_batch_size:
            entries.append(self.pending_entries.popleft())
            
        if not entries:
            return
            
        batch = LogBatch(
            entries=entries,
            timestamp=time.time(),
            batch_id=f"batch_{self.batch_counter:06d}",
        )
        
        try:
            await self._write_batch(batch)
            
            # Update statistics
            self.stats['batches_processed'] += 1
            self.stats['entries_processed'] += len(entries)
            self.stats['avg_batch_size'] = (
                self.stats['entries_processed'] / self.stats['batches_processed']
            )
            
            self.last_flush_time = time.time()
            self.batch_counter += 1
            
        except Exception as e:
            self.logger.error(f"Failed to write batch {batch.batch_id}: {e}")
            # Re-queue entries for retry
            self.pending_entries.extendleft(reversed(entries))
            
    async def _write_batch(self, batch: LogBatch):
        """Write a batch to storage."""
        # Check if we need a new log file
        if (not self.current_log_file or 
            self.current_file_size >= self.max_file_size):
            await self._rotate_log_file()
            
        # Prepare batch data
        batch_data = {
            'batch_id': batch.batch_id,
            'timestamp': batch.timestamp,
            'entry_count': len(batch.entries),
            'entries': batch.entries
        }
        
        # Serialize to JSON
        json_data = json.dumps(batch_data, default=str, separators=(',', ':'))
        raw_size = len(json_data.encode('utf-8'))
        
        # Write to file (with optional compression)
        if self.compression_enabled and self.current_log_file.suffix == '.gz':
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            self.current_log_file.write_bytes(compressed_data)
            written_size = len(compressed_data)
            
            # Update compression ratio
            compression_ratio = written_size / raw_size if raw_size > 0 else 1.0
            self.stats['compression_ratio'] = (
                (self.stats['compression_ratio'] * (self.stats['batches_processed'] - 1) + 
                 compression_ratio) / self.stats['batches_processed']
            )
        else:
            # Write uncompressed
            json_data += '\n'  # Add newline for easier reading
            self.current_log_file.write_text(json_data, encoding='utf-8')
            written_size = len(json_data.encode('utf-8'))
            
        self.current_file_size += written_size
        self.stats['bytes_written'] += written_size
        
        self.logger.debug(f"Wrote batch {batch.batch_id}: {len(batch.entries)} entries, {written_size} bytes")
        
    async def _rotate_log_file(self):
        """Rotate to a new log file."""
        timestamp = int(time.time())
        file_extension = '.jsonl.gz' if self.compression_enabled else '.jsonl'
        
        self.current_log_file = self.output_dir / f"yesman_logs_{timestamp}{file_extension}"
        self.current_file_size = 0
        self.stats['files_created'] += 1
        
        self.logger.info(f"Rotated to new log file: {self.current_log_file}")
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        uptime = time.time() - (self.last_flush_time if self.stats['batches_processed'] > 0 else time.time())
        
        return {
            **self.stats,
            'pending_entries': len(self.pending_entries),
            'current_file_size': self.current_file_size,
            'max_batch_size': self.max_batch_size,
            'max_batch_time': self.max_batch_time,
            'compression_enabled': self.compression_enabled,
            'uptime_seconds': uptime,
            'entries_per_second': self.stats['entries_processed'] / max(uptime, 1),
            'output_directory': str(self.output_dir)
        }
        
    async def cleanup_old_files(self, days_to_keep: int = 7) -> int:
        """Clean up old log files."""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        removed_count = 0
        
        try:
            for log_file in self.output_dir.glob("yesman_logs_*.jsonl*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    removed_count += 1
                    
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old log files")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old log files: {e}")
            
        return removed_count
        
    async def read_batch_file(self, file_path: Path) -> List[LogBatch]:
        """Read and parse a batch log file."""
        batches = []
        
        try:
            if file_path.suffix == '.gz':
                # Read compressed file
                compressed_data = file_path.read_bytes()
                json_data = gzip.decompress(compressed_data).decode('utf-8')
            else:
                # Read uncompressed file
                json_data = file_path.read_text(encoding='utf-8')
                
            # Parse JSON lines
            for line in json_data.strip().split('\n'):
                if line.strip():
                    batch_data = json.loads(line)
                    batch = LogBatch(
                        entries=batch_data['entries'],
                        timestamp=batch_data['timestamp'],
                        batch_id=batch_data['batch_id']
                    )
                    batches.append(batch)
                    
        except Exception as e:
            self.logger.error(f"Error reading batch file {file_path}: {e}")
            
        return batches
        
    def get_recent_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries from memory (pending entries)."""
        recent = list(self.pending_entries)
        return recent[-limit:] if len(recent) > limit else recent