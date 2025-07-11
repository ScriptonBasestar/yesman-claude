"""Test branch testing integration system"""

import asyncio
import pytest
import tempfile
import os
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from libs.multi_agent.branch_test_manager import (
    BranchTestManager, 
    TestSuite, 
    TestType, 
    TestStatus,
    TestResult
)
from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.types import Task, TaskStatus


class TestBranchTestManager:
    """Test branch testing functionality"""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Initialize actual git repository
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, capture_output=True)
            
            # Create basic directory structure
            (repo_path / "tests").mkdir()
            (repo_path / "src").mkdir()
            
            # Create basic test files
            (repo_path / "tests" / "test_example.py").write_text(
                "def test_example():\n    assert True\n"
            )
            (repo_path / "pyproject.toml").write_text(
                "[build-system]\nrequires = ['setuptools']\n"
            )
            
            # Create initial commit
            subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)
            
            # Create develop branch
            subprocess.run(["git", "branch", "develop"], cwd=repo_path, capture_output=True)
            
            yield repo_path

    @pytest.fixture
    def branch_test_manager(self, temp_repo):
        """Create branch test manager for testing"""
        return BranchTestManager(
            repo_path=str(temp_repo),
            results_dir=str(temp_repo / ".yesman" / "test_results")
        )

    def test_test_suite_creation(self):
        """Test TestSuite dataclass creation"""
        suite = TestSuite(
            name="unit_tests",
            test_type=TestType.UNIT,
            command=["python", "-m", "pytest"],
            timeout=300,
            critical=True
        )
        
        assert suite.name == "unit_tests"
        assert suite.test_type == TestType.UNIT
        assert suite.critical is True
        assert suite.timeout == 300

    def test_test_result_serialization(self):
        """Test TestResult serialization/deserialization"""
        result = TestResult(
            test_id="test-123",
            test_type=TestType.UNIT,
            branch_name="feat/test-branch",
            status=TestStatus.PASSED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=10.5,
            coverage=85.0
        )
        
        # Test serialization
        data = result.to_dict()
        assert data["test_id"] == "test-123"
        assert data["test_type"] == "unit"
        assert data["status"] == "passed"
        assert data["coverage"] == 85.0
        
        # Test deserialization
        restored = TestResult.from_dict(data)
        assert restored.test_id == result.test_id
        assert restored.test_type == result.test_type
        assert restored.status == result.status
        assert restored.coverage == result.coverage

    def test_default_configuration_creation(self, branch_test_manager):
        """Test creation of default test configuration"""
        # Should have default test suites
        assert len(branch_test_manager.test_suites) > 0
        assert "unit_tests" in branch_test_manager.test_suites
        assert "lint_check" in branch_test_manager.test_suites
        
        # Check that config file was created
        config_file = branch_test_manager._get_config_file()
        assert config_file.exists()

    def test_test_suite_configuration(self, branch_test_manager):
        """Test configuring custom test suites"""
        branch_test_manager.configure_test_suite(
            name="custom_test",
            test_type=TestType.INTEGRATION,
            command=["npm", "test"],
            timeout=120,
            critical=False
        )
        
        assert "custom_test" in branch_test_manager.test_suites
        suite = branch_test_manager.test_suites["custom_test"]
        assert suite.test_type == TestType.INTEGRATION
        assert suite.command == ["npm", "test"]
        assert suite.timeout == 120
        assert suite.critical is False

    @pytest.mark.asyncio
    async def test_single_test_execution(self, branch_test_manager):
        """Test execution of a single test suite"""
        # Configure a simple test that should pass
        branch_test_manager.configure_test_suite(
            name="simple_test",
            test_type=TestType.UNIT,
            command=["python", "-c", "print('Test passed'); exit(0)"],
            timeout=30
        )
        
        # Mock branch switching
        with patch.object(branch_test_manager.branch_manager, 'switch_branch', return_value=True):
            with patch.object(branch_test_manager.branch_manager, '_get_current_branch', return_value="test-branch"):
                result = await branch_test_manager.run_test_suite(
                    branch_name="test-branch",
                    suite_name="simple_test"
                )
        
        assert result.status == TestStatus.PASSED
        assert result.exit_code == 0
        assert "Test passed" in result.output
        assert result.duration > 0

    @pytest.mark.asyncio
    async def test_failed_test_execution(self, branch_test_manager):
        """Test execution of a failing test"""
        # Configure a test that should fail
        branch_test_manager.configure_test_suite(
            name="failing_test",
            test_type=TestType.UNIT,
            command=["python", "-c", "print('Test failed'); exit(1)"],
            timeout=30
        )
        
        with patch.object(branch_test_manager.branch_manager, 'switch_branch', return_value=True):
            with patch.object(branch_test_manager.branch_manager, '_get_current_branch', return_value="test-branch"):
                result = await branch_test_manager.run_test_suite(
                    branch_name="test-branch",
                    suite_name="failing_test"
                )
        
        assert result.status == TestStatus.FAILED
        assert result.exit_code == 1
        assert "Test failed" in result.output

    @pytest.mark.asyncio
    async def test_timeout_handling(self, branch_test_manager):
        """Test handling of test timeouts"""
        # Configure a test that should timeout
        branch_test_manager.configure_test_suite(
            name="timeout_test",
            test_type=TestType.UNIT,
            command=["python", "-c", "import time; time.sleep(10)"],
            timeout=1  # 1 second timeout
        )
        
        with patch.object(branch_test_manager.branch_manager, 'switch_branch', return_value=True):
            with patch.object(branch_test_manager.branch_manager, '_get_current_branch', return_value="test-branch"):
                result = await branch_test_manager.run_test_suite(
                    branch_name="test-branch",
                    suite_name="timeout_test"
                )
        
        assert result.status == TestStatus.ERROR
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio 
    async def test_all_tests_execution(self, branch_test_manager):
        """Test execution of all test suites"""
        # Configure multiple test suites
        branch_test_manager.configure_test_suite(
            name="critical_test",
            test_type=TestType.UNIT,
            command=["python", "-c", "print('Critical test passed')"],
            critical=True
        )
        
        branch_test_manager.configure_test_suite(
            name="normal_test",
            test_type=TestType.LINT,
            command=["python", "-c", "print('Normal test passed')"],
            critical=False
        )
        
        with patch.object(branch_test_manager.branch_manager, 'switch_branch', return_value=True):
            with patch.object(branch_test_manager.branch_manager, '_get_current_branch', return_value="test-branch"):
                results = await branch_test_manager.run_all_tests(
                    branch_name="test-branch",
                    parallel=False  # Sequential for deterministic testing
                )
        
        assert len(results) >= 2
        
        # Find our test results
        critical_result = next((r for r in results if "critical_test" in r.test_id), None)
        normal_result = next((r for r in results if "normal_test" in r.test_id), None)
        
        assert critical_result is not None
        assert normal_result is not None
        assert critical_result.status == TestStatus.PASSED
        assert normal_result.status == TestStatus.PASSED

    @pytest.mark.asyncio
    async def test_critical_test_failure_stops_execution(self, branch_test_manager):
        """Test that critical test failure stops remaining tests"""
        # Configure critical test that fails
        branch_test_manager.configure_test_suite(
            name="critical_failing",
            test_type=TestType.UNIT,
            command=["python", "-c", "exit(1)"],
            critical=True
        )
        
        branch_test_manager.configure_test_suite(
            name="should_not_run",
            test_type=TestType.LINT,
            command=["python", "-c", "print('Should not run')"],
            critical=False
        )
        
        with patch.object(branch_test_manager.branch_manager, 'switch_branch', return_value=True):
            with patch.object(branch_test_manager.branch_manager, '_get_current_branch', return_value="test-branch"):
                results = await branch_test_manager.run_all_tests(
                    branch_name="test-branch",
                    parallel=False
                )
        
        # Should have stopped after critical test failure
        assert len(results) == 1
        assert results[0].status == TestStatus.FAILED

    def test_branch_test_summary(self, branch_test_manager):
        """Test branch test summary generation"""
        branch_name = "test-branch"
        
        # Add some test results
        results = [
            TestResult(
                test_id="test-1",
                test_type=TestType.UNIT,
                branch_name=branch_name,
                status=TestStatus.PASSED,
                start_time=datetime.now()
            ),
            TestResult(
                test_id="test-2", 
                test_type=TestType.LINT,
                branch_name=branch_name,
                status=TestStatus.FAILED,
                start_time=datetime.now()
            )
        ]
        
        branch_test_manager.branch_results[branch_name] = results
        
        summary = branch_test_manager.get_branch_test_summary(branch_name)
        
        assert summary["branch"] == branch_name
        assert summary["total_tests"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["status"] == "failed"  # Overall status should be failed

    def test_results_persistence(self, branch_test_manager):
        """Test that test results are persisted to disk"""
        branch_name = "test-branch"
        
        result = TestResult(
            test_id="test-persist",
            test_type=TestType.UNIT,
            branch_name=branch_name,
            status=TestStatus.PASSED,
            start_time=datetime.now()
        )
        
        # Add result and save
        branch_test_manager.branch_results[branch_name] = [result]
        branch_test_manager._save_test_results(branch_name)
        
        # Verify file was created
        results_file = branch_test_manager._get_results_file(branch_name)
        assert results_file.exists()
        
        # Verify content
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["test_id"] == "test-persist"

    def test_auto_testing_configuration(self, branch_test_manager):
        """Test auto-testing configuration"""
        # Initially disabled
        assert not branch_test_manager.auto_testing_enabled
        
        # Enable auto-testing
        branch_test_manager.enable_auto_testing(True)
        assert branch_test_manager.auto_testing_enabled
        
        # Verify configuration was saved
        config_file = branch_test_manager._get_config_file()
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        assert config["settings"]["auto_testing_enabled"] is True


class TestAgentPoolTestIntegration:
    """Test AgentPool integration with branch testing"""

    @pytest.fixture
    def agent_pool(self):
        """Create agent pool for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pool = AgentPool(max_agents=2, work_dir=tmpdir)
            yield pool

    def test_branch_testing_enablement(self, agent_pool):
        """Test enabling branch testing in agent pool"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_branch_testing(repo_path=tmpdir)
            
            assert agent_pool._test_integration_enabled
            assert agent_pool.branch_test_manager is not None

    def test_test_task_creation(self, agent_pool):
        """Test creation of test tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_branch_testing(repo_path=tmpdir)
            
            task = agent_pool.create_test_task(
                branch_name="test-branch",
                test_suite_name="unit_tests",
                priority=8
            )
            
            assert task.title == "Test unit_tests on test-branch"
            assert task.priority == 8
            assert task.metadata["type"] == "test"
            assert task.metadata["branch"] == "test-branch"
            assert "python" in task.command[0]

    @pytest.mark.asyncio
    async def test_auto_test_branch(self, agent_pool):
        """Test automatic test task creation for a branch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_branch_testing(repo_path=tmpdir)
            
            # Mock some test suites
            agent_pool.branch_test_manager.test_suites = {
                "critical_test": TestSuite(
                    name="critical_test",
                    test_type=TestType.UNIT,
                    command=["pytest"],
                    critical=True
                ),
                "normal_test": TestSuite(
                    name="normal_test", 
                    test_type=TestType.LINT,
                    command=["ruff"],
                    critical=False
                )
            }
            
            task_ids = await agent_pool.auto_test_branch("test-branch")
            
            # Should create tasks for critical test + combined non-critical
            assert len(task_ids) == 2
            
            # Verify tasks were added to pool
            assert len(agent_pool.tasks) == 2

    def test_branch_test_status_retrieval(self, agent_pool):
        """Test retrieving branch test status"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_branch_testing(repo_path=tmpdir)
            
            # Mock some test results
            branch_name = "test-branch"
            agent_pool.branch_test_manager.branch_results[branch_name] = [
                TestResult(
                    test_id="test-1",
                    test_type=TestType.UNIT,
                    branch_name=branch_name,
                    status=TestStatus.PASSED,
                    start_time=datetime.now()
                )
            ]
            
            status = agent_pool.get_branch_test_status(branch_name)
            
            assert status["branch"] == branch_name
            assert status["total_tests"] == 1
            assert status["passed"] == 1
            assert status["status"] == "passed"

    def test_error_handling_when_testing_disabled(self, agent_pool):
        """Test error handling when branch testing is not enabled"""
        # Don't enable branch testing
        
        with pytest.raises(RuntimeError, match="Branch testing is not enabled"):
            agent_pool.create_test_task("test-branch", "unit_tests")
        
        status = agent_pool.get_branch_test_status("test-branch")
        assert "error" in status

    def test_test_task_metadata(self, agent_pool):
        """Test that test tasks have proper metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_pool.enable_branch_testing(repo_path=tmpdir)
            
            task = agent_pool.create_test_task(
                branch_name="feature/new-feature",
                test_suite_name="integration_tests"
            )
            
            assert task.metadata["type"] == "test"
            assert task.metadata["branch"] == "feature/new-feature"
            assert task.metadata["test_suite"] == "integration_tests"
            assert task.metadata["auto_generated"] is True
            assert task.complexity == 6  # Medium complexity for tests


if __name__ == "__main__":
    pytest.main([__file__])