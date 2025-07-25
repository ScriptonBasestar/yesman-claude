# Copyright notice.

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from libs.core.content_collector import ClaudeContentCollector, ContentCollectionManager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test content collection functionality."""


class TestClaudeContentCollector(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.session_name = "test_session"

        # Mock the log directory to use temp directory
        with patch("libs.core.content_collector.get_default_log_path") as mock_log_path:
            mock_log_path.return_value = Path(self.temp_dir)
            self.collector = ClaudeContentCollector(self.session_name)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def test_collect_interaction_success(self) -> None:
        """Test successful interaction collection."""
        content = "Do you want to make this edit? [1] Yes [2] No"
        prompt_info = {"type": "numbered", "count": 2}
        response = "1"

        result = self.collector.collect_interaction(content, prompt_info, response)
        assert result

        # Check file was created
        files = list(self.collector.collection_path.glob("interaction_*.json"))
        assert len(files) == 1

        # Check file content
        with open(files[0], encoding="utf-8") as f:
            data = json.load(f)

        assert data["session_name"] == self.session_name
        assert data["content"] == content
        assert data["prompt_info"] == prompt_info
        assert data["auto_response"] == response
        assert data["prompt_detected"]

    def test_collect_interaction_no_duplicates(self) -> None:
        """Test that duplicate content is not collected."""
        content = "Same content"

        # First collection should succeed
        result1 = self.collector.collect_interaction(content)
        assert result1

        # Second collection should be skipped
        result2 = self.collector.collect_interaction(content)
        assert not result2

        # Only one file should exist
        files = list(self.collector.collection_path.glob("interaction_*.json"))
        assert len(files) == 1

    def test_collect_raw_content(self) -> None:
        """Test raw content collection."""
        content = "Regular Claude output without prompts"
        metadata = {"source": "test"}

        result = self.collector.collect_raw_content(content, metadata)
        assert result

        # Check file was created
        files = list(self.collector.collection_path.glob("raw_*.json"))
        assert len(files) == 1

        # Check file content
        with open(files[0], encoding="utf-8") as f:
            data = json.load(f)

        assert data["content"] == content
        assert data["metadata"] == metadata
        assert data["record_type"] == "raw_content"

    def test_skip_empty_content(self) -> None:
        """Test that empty or very short content is skipped."""
        test_cases = ["", "   ", "short"]

        for content in test_cases:
            result = self.collector.collect_interaction(content)
            assert not result

        # No files should be created
        files = list(self.collector.collection_path.glob("*.json"))
        assert len(files) == 0

    def test_get_collection_stats(self) -> None:
        """Test collection statistics."""
        # Collect some interactions
        self.collector.collect_interaction(
            "First interaction with prompt", {"type": "yn"}, "yes"
        )
        self.collector.collect_raw_content("Raw content without prompts")

        stats = self.collector.get_collection_stats()

        assert stats["session_name"] == self.session_name
        assert stats["interaction_files"] == 1
        assert stats["raw_files"] == 1
        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["last_interaction_count"] == 1

    def test_cleanup_old_files(self) -> None:
        """Test cleanup of old files."""
        # Create some test files
        self.collector.collect_interaction("Test interaction 1")
        self.collector.collect_raw_content("Test raw content 1")

        # Initially should have 2 files
        stats_before = self.collector.get_collection_stats()
        assert stats_before["total_files"] == 2

        # Cleanup with 0 days (delete all)
        deleted_count = self.collector.cleanup_old_files(days_to_keep=0)
        assert deleted_count == 2

        # Should have no files left
        stats_after = self.collector.get_collection_stats()
        assert stats_after["total_files"] == 0


class TestContentCollectionManager(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()

        # Mock the log directory
        with patch("libs.core.content_collector.get_default_log_path") as mock_log_path:
            mock_log_path.return_value = Path(self.temp_dir)
            self.manager = ContentCollectionManager()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def test_get_collector(self) -> None:
        """Test getting collector for session."""
        session_name = "test_session"

        collector1 = self.manager.get_collector(session_name)
        collector2 = self.manager.get_collector(session_name)

        # Should return same instance
        assert collector1 is collector2
        assert len(self.manager.collectors) == 1

    def test_collect_for_session(self) -> None:
        """Test collecting content for session."""
        session_name = "test_session"
        content = "Test content with prompt"
        prompt_info = {"type": "yn"}
        response = "yes"

        result = self.manager.collect_for_session(
            session_name, content, prompt_info, response
        )
        assert result

        # Collector should be created
        assert session_name in self.manager.collectors

    def test_get_all_stats(self) -> None:
        """Test getting stats for all sessions."""
        # Collect for multiple sessions
        self.manager.collect_for_session("session1", "Content for session 1")
        self.manager.collect_for_session("session2", "Content for session 2")

        stats = self.manager.get_all_stats()

        assert "session1" in stats
        assert "session2" in stats
        assert len(stats) == 2

        # Each should have stats
        for session_stats in stats.values():
            assert "total_files" in session_stats
            assert "session_name" in session_stats
