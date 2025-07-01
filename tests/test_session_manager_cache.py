"""Test session manager cache functionality"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from libs.core.session_manager import SessionManager
from libs.core.models import SessionInfo, WindowInfo, PaneInfo


class TestSessionManagerCache:
    """Test SessionManager caching functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock YesmanConfig"""
        config = Mock()
        config.get.return_value = "~/tmp/logs/yesman/"
        config.get_config_dir.return_value = Path("/tmp/test_config")
        return config
    
    @pytest.fixture
    def mock_tmux_manager(self):
        """Mock TmuxManager"""
        tmux_manager = Mock()
        tmux_manager.load_projects.return_value = {
            "sessions": {
                "test_project": {
                    "template_name": "test_template",
                    "override": {
                        "session_name": "test_session"
                    }
                }
            }
        }
        return tmux_manager
    
    @pytest.fixture
    def mock_server(self):
        """Mock libtmux.Server"""
        server = Mock()
        # Mock session not found initially
        server.find_where.return_value = None
        return server
    
    @pytest.fixture
    def session_manager(self, mock_config, mock_tmux_manager, mock_server):
        """Create SessionManager with mocked dependencies"""
        with patch('libs.core.session_manager.YesmanConfig', return_value=mock_config), \
             patch('libs.core.session_manager.TmuxManager', return_value=mock_tmux_manager), \
             patch('libs.core.session_manager.libtmux.Server', return_value=mock_server), \
             patch('libs.core.session_manager.ensure_log_directory'):
            
            manager = SessionManager()
            return manager
    
    def test_cache_initialization(self, session_manager):
        """Test that cache is properly initialized"""
        assert session_manager.cache is not None
        assert session_manager.cache.default_ttl == 3.0
        assert session_manager.cache.max_entries == 100
    
    def test_get_all_sessions_caching(self, session_manager):
        """Test that get_all_sessions uses caching"""
        # First call should compute and cache
        sessions1 = session_manager.get_all_sessions()
        assert len(sessions1) == 1
        assert sessions1[0].project_name == "test_project"
        
        # Second call should hit cache (same result)
        sessions2 = session_manager.get_all_sessions()
        assert sessions1 == sessions2
        
        # Verify cache stats
        stats = session_manager.get_cache_stats()
        assert stats['hits'] >= 1
        assert stats['total_entries'] >= 1
    
    def test_session_info_caching(self, session_manager):
        """Test individual session info caching"""
        project_conf = {
            "template_name": "test_template",
            "override": {"session_name": "test_session"}
        }
        
        # First call should compute and cache
        session_info1 = session_manager._get_session_info("test_project", project_conf)
        assert session_info1.project_name == "test_project"
        
        # Second call should hit cache
        session_info2 = session_manager._get_session_info("test_project", project_conf)
        assert session_info1 == session_info2
    
    def test_cache_invalidation_specific_project(self, session_manager):
        """Test invalidating cache for specific project"""
        # Populate cache
        session_manager.get_all_sessions()
        
        # Invalidate specific project
        session_manager.invalidate_cache("test_project")
        
        # Verify cache stats show eviction
        stats = session_manager.get_cache_stats()
        assert stats['evictions'] >= 1
    
    def test_cache_invalidation_all(self, session_manager):
        """Test invalidating all cache entries"""
        # Populate cache
        session_manager.get_all_sessions()
        
        # Invalidate all
        session_manager.invalidate_cache()
        
        # Verify cache is cleared
        stats = session_manager.get_cache_stats()
        assert stats['total_entries'] == 0
    
    def test_cache_ttl_expiration(self, session_manager):
        """Test cache TTL expiration"""
        # Create cache with very short TTL for testing
        session_manager.cache.default_ttl = 0.1
        
        # Populate cache
        sessions1 = session_manager.get_all_sessions()
        
        # Wait for TTL expiration
        time.sleep(0.2)
        
        # Next call should recompute (cache miss)
        sessions2 = session_manager.get_all_sessions()
        
        # Should have at least one miss from expiration
        stats = session_manager.get_cache_stats()
        assert stats['misses'] >= 1
    
    def test_cache_stats_format(self, session_manager):
        """Test cache stats format and content"""
        # Populate cache
        session_manager.get_all_sessions()
        
        stats = session_manager.get_cache_stats()
        
        # Verify required fields
        required_fields = ['hits', 'misses', 'hit_rate', 'total_entries', 
                          'memory_size_bytes', 'evictions']
        for field in required_fields:
            assert field in stats
            assert isinstance(stats[field], (int, float))
        
        # Hit rate should be percentage
        assert 0 <= stats['hit_rate'] <= 100
    
    def test_all_sessions_cache_invalidation(self, session_manager):
        """Test specific all_sessions cache invalidation"""
        # Populate cache
        session_manager.get_all_sessions()
        
        # Invalidate all_sessions specifically
        session_manager.invalidate_all_sessions_cache()
        
        # Next call should recompute
        session_manager.get_all_sessions()
        
        # Should have cache miss
        stats = session_manager.get_cache_stats()
        assert stats['misses'] >= 1
    
    def test_cache_with_running_session(self, session_manager, mock_server):
        """Test caching with a running tmux session"""
        # Mock a running session
        mock_session = Mock()
        mock_window = Mock()
        mock_pane = Mock()
        
        mock_pane.cmd.return_value.stdout = ["claude"]
        mock_pane.get.return_value = "pane_id_1"
        
        mock_window.list_panes.return_value = [mock_pane]
        mock_window.get.side_effect = lambda key: {
            'window_name': 'test_window',
            'window_index': 0
        }.get(key)
        
        mock_session.list_windows.return_value = [mock_window]
        mock_server.find_where.return_value = mock_session
        
        # Get sessions (should cache)
        sessions = session_manager.get_all_sessions()
        
        # Verify session is running
        assert len(sessions) == 1
        assert sessions[0].exists is True
        assert sessions[0].status == 'running'
        
        # Second call should hit cache
        sessions2 = session_manager.get_all_sessions()
        assert sessions == sessions2
    
    def test_cache_memory_estimation(self, session_manager):
        """Test cache memory size estimation"""
        # Populate cache with multiple entries
        session_manager.get_all_sessions()
        
        stats = session_manager.get_cache_stats()
        
        # Should have some memory usage
        assert stats['memory_size_bytes'] > 0
        assert isinstance(stats['memory_size_bytes'], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])