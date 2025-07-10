"""Tests for WebSocket batch processor functionality."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock
from api.utils import WebSocketBatchProcessor, BatchConfig


class TestBatchConfig:
    """Test BatchConfig class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = BatchConfig()
        
        assert config.max_batch_size == 10
        assert config.max_batch_time == 0.1
        assert config.max_memory_size == 1024 * 1024
        assert config.compression_threshold == 5
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = BatchConfig(
            max_batch_size=20,
            max_batch_time=0.2,
            compression_threshold=3
        )
        
        assert config.max_batch_size == 20
        assert config.max_batch_time == 0.2
        assert config.compression_threshold == 3


class TestWebSocketBatchProcessor:
    """Test WebSocketBatchProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Create a batch processor for testing"""
        config = BatchConfig(max_batch_size=3, max_batch_time=0.05)
        return WebSocketBatchProcessor(config)
    
    @pytest.fixture
    def mock_handler(self):
        """Create a mock message handler"""
        return AsyncMock()
    
    def test_initialization(self, processor):
        """Test processor initialization"""
        assert processor.config.max_batch_size == 3
        assert processor.config.max_batch_time == 0.05
        assert processor.stats['batches_sent'] == 0
        assert processor.stats['messages_processed'] == 0
    
    def test_register_handler(self, processor, mock_handler):
        """Test message handler registration"""
        processor.register_message_handler("test_channel", mock_handler)
        assert "test_channel" in processor._message_handlers
        assert processor._message_handlers["test_channel"] == mock_handler
    
    def test_queue_message(self, processor):
        """Test message queueing"""
        processor.queue_message("test_channel", {"type": "test", "data": "hello"})
        
        assert "test_channel" in processor.pending_messages
        assert len(processor.pending_messages["test_channel"]) == 1
        
        message = processor.pending_messages["test_channel"][0]
        assert message["type"] == "test"
        assert message["data"] == "hello"
        assert "queued_at" in message
    
    @pytest.mark.asyncio
    async def test_send_immediate(self, processor, mock_handler):
        """Test immediate message sending"""
        processor.register_message_handler("test_channel", mock_handler)
        
        test_message = {"type": "urgent", "data": "immediate"}
        await processor.send_immediate("test_channel", test_message)
        
        mock_handler.assert_called_once_with([test_message])
        assert processor.stats['messages_processed'] == 1
    
    @pytest.mark.asyncio
    async def test_batch_processing_by_size(self, processor, mock_handler):
        """Test batch processing triggered by size limit"""
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
    async def test_batch_processing_by_time(self, processor, mock_handler):
        """Test batch processing triggered by time limit"""
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
    
    def test_message_optimization(self, processor):
        """Test message optimization and combining"""
        # Test update message combining
        messages = [
            {"type": "session_update", "data": {"session1": "data1"}, "queued_at": 1.0},
            {"type": "session_update", "data": {"session2": "data2"}, "queued_at": 1.1},
            {"type": "session_update", "data": {"session1": "updated"}, "queued_at": 1.2}
        ]
        
        optimized = processor._optimize_messages(messages)
        
        # Should combine into single message
        assert len(optimized) == 1
        combined = optimized[0]
        assert combined["type"] == "session_update"
        assert "batch_info" in combined
        assert combined["data"]["session1"] == "updated"  # Latest data
        assert combined["data"]["session2"] == "data2"
    
    def test_log_message_optimization(self, processor):
        """Test log message batch optimization"""
        messages = [
            {"type": "log_update", "data": {"level": "info", "message": "Log 1"}, "queued_at": 1.0},
            {"type": "log_update", "data": {"level": "error", "message": "Log 2"}, "queued_at": 1.1}
        ]
        
        optimized = processor._optimize_messages(messages)
        
        # Should combine into log batch
        assert len(optimized) == 1
        combined = optimized[0]
        assert combined["type"] == "log_batch"
        assert len(combined["data"]["entries"]) == 2
        assert combined["data"]["count"] == 2
    
    def test_get_statistics(self, processor):
        """Test statistics reporting"""
        # Add some test data
        processor.queue_message("test1", {"type": "test"})
        processor.queue_message("test2", {"type": "test"})
        processor.stats['batches_sent'] = 5
        processor.stats['messages_processed'] = 25
        
        stats = processor.get_statistics()
        
        assert stats['batches_sent'] == 5
        assert stats['messages_processed'] == 25
        assert stats['avg_batch_size'] == 5.0
        assert stats['active_channels'] == 2
        assert stats['total_pending_messages'] == 2
        assert 'config' in stats
    
    def test_update_config(self, processor):
        """Test configuration updates"""
        processor.update_config(max_batch_size=15, max_batch_time=0.2)
        
        assert processor.config.max_batch_size == 15
        assert processor.config.max_batch_time == 0.2
    
    def test_clear_channel(self, processor):
        """Test clearing channel messages"""
        processor.queue_message("test_channel", {"type": "test1"})
        processor.queue_message("test_channel", {"type": "test2"})
        processor.queue_message("other_channel", {"type": "test3"})
        
        assert len(processor.pending_messages["test_channel"]) == 2
        assert len(processor.pending_messages["other_channel"]) == 1
        
        processor.clear_channel("test_channel")
        
        assert len(processor.pending_messages["test_channel"]) == 0
        assert len(processor.pending_messages["other_channel"]) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, processor):
        """Test error handling in message processing"""
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
    async def test_start_stop_lifecycle(self, processor):
        """Test processor start/stop lifecycle"""
        assert processor._processing_task is None
        
        await processor.start()
        assert processor._processing_task is not None
        assert not processor._processing_task.done()
        
        await processor.stop()
        assert processor._processing_task.done()
    
    def test_memory_size_calculation(self, processor):
        """Test memory size calculation for queues"""
        from collections import deque
        
        test_queue = deque([
            {"type": "test", "data": "small"},
            {"type": "test", "data": "larger message content"},
            {"type": "test", "data": {"complex": "object", "with": ["multiple", "values"]}}
        ])
        
        size = processor._get_queue_memory_size(test_queue)
        assert size > 0
        assert isinstance(size, int)


if __name__ == "__main__":
    pytest.main([__file__])