#!/usr/bin/env python3
"""
Tests for progress indicator utilities
"""

import time

import pytest

from libs.core.progress_indicators import (
    ProgressManager,
    ProgressStyle,
    bar_progress,
    multi_stage_progress,
    spinner_progress,
    track_items,
    with_analysis_progress,
    with_processing_progress,
    with_startup_progress,
)


class TestProgressIndicators:
    """Test progress indicator utilities"""

    def test_spinner_progress_context_manager(self):
        """Test spinner progress context manager"""
        with spinner_progress("Testing spinner") as update:
            # Should not raise any exceptions
            update("Updated description")
            assert True  # If we get here, context manager worked

    def test_bar_progress_context_manager(self):
        """Test bar progress context manager"""
        with bar_progress("Testing bar", total=10) as update:
            # Simulate processing items
            for i in range(5):
                update(1, f"Processing item {i}")
            assert True  # If we get here, context manager worked

    def test_track_items(self):
        """Test track_items function"""
        items = ["item1", "item2", "item3"]
        processed_items = []

        for item in track_items(items, "Processing items"):
            processed_items.append(item)

        assert processed_items == items

    def test_multi_stage_progress(self):
        """Test multi-stage progress indicator"""
        stages = ["Stage 1", "Stage 2", "Stage 3"]

        with multi_stage_progress(stages) as next_stage:
            next_stage(1)  # Move to stage 1
            next_stage(2, "Custom description")  # Move to stage 2 with custom description
            assert True  # If we get here, context manager worked

    def test_progress_manager_startup_sequence(self):
        """Test ProgressManager startup sequence"""

        def mock_operation_1():
            return "result1"

        def mock_operation_2():
            return "result2"

        operations = [
            ("Operation 1", mock_operation_1),
            ("Operation 2", mock_operation_2),
        ]

        results = ProgressManager.startup_sequence(operations)

        assert "stage_0" in results
        assert "stage_1" in results
        assert results["stage_0"]["success"] is True
        assert results["stage_0"]["result"] == "result1"
        assert results["stage_1"]["success"] is True
        assert results["stage_1"]["result"] == "result2"

    def test_progress_manager_startup_sequence_with_error(self):
        """Test ProgressManager startup sequence with error handling"""

        def mock_operation_success():
            return "success"

        def mock_operation_failure():
            raise ValueError("Test error")

        operations = [
            ("Success Operation", mock_operation_success),
            ("Failure Operation", mock_operation_failure),
        ]

        with pytest.raises(ValueError):
            ProgressManager.startup_sequence(operations)

    def test_progress_manager_file_batch_operation(self):
        """Test ProgressManager file batch operation"""
        # Mock file objects
        files = ["file1.txt", "file2.txt", "file3.txt"]

        def mock_operation(file_name):
            return f"processed_{file_name}"

        results = ProgressManager.file_batch_operation(files, mock_operation, "Processing test files")

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["success"] is True
            assert result["result"] == f"processed_{files[i]}"
            assert result["file"] == files[i]

    def test_progress_manager_file_batch_operation_with_errors(self):
        """Test ProgressManager file batch operation with error handling"""
        files = ["file1.txt", "error_file.txt", "file3.txt"]

        def mock_operation(file_name):
            if "error" in file_name:
                raise OSError("File read error")
            return f"processed_{file_name}"

        results = ProgressManager.file_batch_operation(files, mock_operation, "Processing test files")

        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "File read error" in results[1]["error"]
        assert results[2]["success"] is True

    def test_convenience_decorators(self):
        """Test convenience decorator functions"""
        # Test that decorators return context managers
        with with_startup_progress("Starting up") as update:
            update("Started")
            assert True

        with with_processing_progress("Processing") as update:
            update("Processing data")
            assert True

        with with_analysis_progress("Analyzing") as update:
            update("Analyzing results")
            assert True

    def test_progress_styles(self):
        """Test that progress styles are defined"""
        assert hasattr(ProgressStyle, "STARTUP")
        assert hasattr(ProgressStyle, "PROCESSING")
        assert hasattr(ProgressStyle, "ANALYZING")
        assert hasattr(ProgressStyle, "CLEANUP")
        assert hasattr(ProgressStyle, "ERROR")
        assert hasattr(ProgressStyle, "SUCCESS")
        assert hasattr(ProgressStyle, "FILE_OPERATIONS")
        assert hasattr(ProgressStyle, "NETWORK_OPERATIONS")
        assert hasattr(ProgressStyle, "DATA_PROCESSING")


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_session_setup_scenario(self):
        """Test progress indicators for session setup scenario"""
        sessions = ["session1", "session2", "session3"]

        with with_startup_progress("Setting up sessions") as update:
            for i, session in enumerate(sessions):
                update(f"Setting up {session} ({i + 1}/{len(sessions)})")
                time.sleep(0.01)  # Simulate work
            update("✅ All sessions setup complete")

        assert True  # Test passes if no exceptions

    def test_multi_agent_startup_scenario(self):
        """Test progress indicators for multi-agent startup"""
        agents = ["agent1", "agent2", "agent3"]

        with multi_stage_progress(["Initializing agent pool", "Starting agents", "Monitoring setup", "Ready"]) as next_stage:
            next_stage(0)
            time.sleep(0.01)

            for i, agent in enumerate(agents):
                next_stage(1, f"Starting {agent} ({i + 1}/{len(agents)})")
                time.sleep(0.01)

            next_stage(2, "Setting up monitoring dashboard")
            time.sleep(0.01)

            next_stage(3, "✅ Agent pool ready")

        assert True  # Test passes if no exceptions

    def test_file_processing_scenario(self):
        """Test progress indicators for file processing"""
        # Simulate file processing
        mock_files = [f"file_{i}.txt" for i in range(5)]

        def process_file(filename):
            time.sleep(0.001)  # Simulate processing time
            return f"processed_{filename}"

        results = ProgressManager.file_batch_operation(mock_files, process_file, "🔧 Processing configuration files", ProgressStyle.FILE_OPERATIONS)

        assert len(results) == 5
        assert all(result["success"] for result in results)

    def test_complex_workflow_scenario(self):
        """Test progress indicators for complex workflow"""
        # Simulate complex workflow with multiple stages

        # Stage 1: Initialization
        with with_startup_progress("🔧 Initializing workflow") as update:
            update("Loading configuration")
            time.sleep(0.01)
            update("Validating parameters")
            time.sleep(0.01)
            update("✅ Initialization complete")

        # Stage 2: Data processing
        data_items = list(range(10))
        processed_data = []

        for item in track_items(data_items, "📊 Processing data items", ProgressStyle.DATA_PROCESSING):
            time.sleep(0.001)
            processed_data.append(item * 2)

        # Stage 3: Analysis
        with with_analysis_progress("🔍 Analyzing results") as update:
            update("Computing statistics")
            time.sleep(0.01)
            update("Generating report")
            time.sleep(0.01)
            update("✅ Analysis complete")

        assert len(processed_data) == 10
        assert processed_data == [i * 2 for i in range(10)]


# Performance tests
class TestProgressPerformance:
    """Test progress indicator performance"""

    def test_progress_overhead(self):
        """Test that progress indicators don't add excessive overhead"""
        import time

        # Test with meaningful work to measure relative overhead
        start = time.time()
        for i in range(1000):
            sum(range(10))  # Some actual work
        no_progress_time = time.time() - start

        # Test with progress
        start = time.time()
        items = list(range(1000))
        for item in track_items(items, "Testing"):
            sum(range(10))  # Same work
        with_progress_time = time.time() - start

        # Progress should complete within reasonable time (less than 1 second for this test)
        assert with_progress_time < 1.0
        # And shouldn't be more than 100x slower than without progress for real work
        assert with_progress_time < no_progress_time * 100
