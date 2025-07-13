"""Test content collection functionality"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from libs.core.content_collector import ClaudeContentCollector, ContentCollectionManager


class TestClaudeContentCollector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.session_name = "test_session"

        # Mock the log directory to use temp directory
        with patch("libs.core.content_collector.get_default_log_path") as mock_log_path:
            mock_log_path.return_value = Path(self.temp_dir)
            self.collector = ClaudeContentCollector(self.session_name)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_collect_interaction_success(self):
        """Test successful interaction collection"""
        content = "Do you want to make this edit? [1] Yes [2] No"
        prompt_info = {"type": "numbered", "count": 2}
        response = "1"

        result = self.collector.collect_interaction(content, prompt_info, response)
        self.assertTrue(result)

        # Check file was created
        files = list(self.collector.collection_path.glob("interaction_*.json"))
        self.assertEqual(len(files), 1)

        # Check file content
        with open(files[0]) as f:
            data = json.load(f)

        self.assertEqual(data["session_name"], self.session_name)
        self.assertEqual(data["content"], content)
        self.assertEqual(data["prompt_info"], prompt_info)
        self.assertEqual(data["auto_response"], response)
        self.assertTrue(data["prompt_detected"])

    def test_collect_interaction_no_duplicates(self):
        """Test that duplicate content is not collected"""
        content = "Same content"

        # First collection should succeed
        result1 = self.collector.collect_interaction(content)
        self.assertTrue(result1)

        # Second collection should be skipped
        result2 = self.collector.collect_interaction(content)
        self.assertFalse(result2)

        # Only one file should exist
        files = list(self.collector.collection_path.glob("interaction_*.json"))
        self.assertEqual(len(files), 1)

    def test_collect_raw_content(self):
        """Test raw content collection"""
        content = "Regular Claude output without prompts"
        metadata = {"source": "test"}

        result = self.collector.collect_raw_content(content, metadata)
        self.assertTrue(result)

        # Check file was created
        files = list(self.collector.collection_path.glob("raw_*.json"))
        self.assertEqual(len(files), 1)

        # Check file content
        with open(files[0]) as f:
            data = json.load(f)

        self.assertEqual(data["content"], content)
        self.assertEqual(data["metadata"], metadata)
        self.assertEqual(data["record_type"], "raw_content")

    def test_skip_empty_content(self):
        """Test that empty or very short content is skipped"""
        test_cases = ["", "   ", "short"]

        for content in test_cases:
            result = self.collector.collect_interaction(content)
            self.assertFalse(result)

        # No files should be created
        files = list(self.collector.collection_path.glob("*.json"))
        self.assertEqual(len(files), 0)

    def test_get_collection_stats(self):
        """Test collection statistics"""
        # Collect some interactions
        self.collector.collect_interaction("First interaction with prompt", {"type": "yn"}, "yes")
        self.collector.collect_raw_content("Raw content without prompts")

        stats = self.collector.get_collection_stats()

        self.assertEqual(stats["session_name"], self.session_name)
        self.assertEqual(stats["interaction_files"], 1)
        self.assertEqual(stats["raw_files"], 1)
        self.assertEqual(stats["total_files"], 2)
        self.assertGreater(stats["total_size_bytes"], 0)
        self.assertEqual(stats["last_interaction_count"], 1)

    def test_cleanup_old_files(self):
        """Test cleanup of old files"""
        # Create some test files
        self.collector.collect_interaction("Test interaction 1")
        self.collector.collect_raw_content("Test raw content 1")

        # Initially should have 2 files
        stats_before = self.collector.get_collection_stats()
        self.assertEqual(stats_before["total_files"], 2)

        # Cleanup with 0 days (delete all)
        deleted_count = self.collector.cleanup_old_files(days_to_keep=0)
        self.assertEqual(deleted_count, 2)

        # Should have no files left
        stats_after = self.collector.get_collection_stats()
        self.assertEqual(stats_after["total_files"], 0)


class TestContentCollectionManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # Mock the log directory
        with patch("libs.core.content_collector.get_default_log_path") as mock_log_path:
            mock_log_path.return_value = Path(self.temp_dir)
            self.manager = ContentCollectionManager()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_collector(self):
        """Test getting collector for session"""
        session_name = "test_session"

        collector1 = self.manager.get_collector(session_name)
        collector2 = self.manager.get_collector(session_name)

        # Should return same instance
        self.assertIs(collector1, collector2)
        self.assertEqual(len(self.manager.collectors), 1)

    def test_collect_for_session(self):
        """Test collecting content for session"""
        session_name = "test_session"
        content = "Test content with prompt"
        prompt_info = {"type": "yn"}
        response = "yes"

        result = self.manager.collect_for_session(session_name, content, prompt_info, response)
        self.assertTrue(result)

        # Collector should be created
        self.assertIn(session_name, self.manager.collectors)

    def test_get_all_stats(self):
        """Test getting stats for all sessions"""
        # Collect for multiple sessions
        self.manager.collect_for_session("session1", "Content for session 1")
        self.manager.collect_for_session("session2", "Content for session 2")

        stats = self.manager.get_all_stats()

        self.assertIn("session1", stats)
        self.assertIn("session2", stats)
        self.assertEqual(len(stats), 2)

        # Each should have stats
        for session_stats in stats.values():
            self.assertIn("total_files", session_stats)
            self.assertIn("session_name", session_stats)
