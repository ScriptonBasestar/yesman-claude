#!/usr/bin/env python3

# Copyright notice.

from commands.automate import AutomateDetectCommand
from libs.ai.learning_engine import LearningEngine

from .test_framework import (
    AsyncIntegrationTestBase,
    CommandTestRunner,
    MockClaudeEnvironment,
    PerformanceMonitor,
)

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""AI Learning System Integration Tests.

Tests the AI learning system's integration with session interactions,
pattern detection, and prediction accuracy across real workflows.
"""


class TestAILearningIntegration(AsyncIntegrationTestBase):
    """Test AI learning system integration with real session interactions."""

    def setup_method(self) -> None:
        """Setup for AI learning tests."""
        super().setup_method()
        self.mock_claude = MockClaudeEnvironment(self.test_dir)
        self.command_runner = CommandTestRunner(self)
        self.performance_monitor = PerformanceMonitor()

        # Setup mock Claude responses for learning scenarios
        self._setup_claude_responses()

    def _setup_claude_responses(self) -> None:
        """Setup mock Claude responses for different learning scenarios."""
        # Code-related responses
        self.mock_claude.add_mock_response("write a function", "def example_function():\n    return 'Hello World'")

        self.mock_claude.add_mock_response(
            "fix this bug",
            "The issue is in line 42. Try changing the variable assignment.",
        )

        self.mock_claude.add_mock_response(
            "explain this code",
            "This code implements a sorting algorithm using quicksort.",
        )

        # Project management responses
        self.mock_claude.add_mock_response("create a task", "I'll help you create a task. What's the task description?")

        self.mock_claude.add_mock_response(
            "project status",
            "Here's your project status: 5 completed tasks, 3 in progress.",
        )

    async def test_learning_from_session_interactions(self) -> None:
        """Test that AI learns patterns from session interactions."""
        # Create test session for learning
        session_name = "ai-learning-session"
        self.create_test_session(session_name)

        # Initialize learning engine
        learning_engine = LearningEngine(config=self.get_test_config(), session_name=session_name)

        # Simulate series of interactions
        interaction_patterns = [
            {"prompt": "write a function to sort numbers", "context": "coding"},
            {"prompt": "write a function to reverse a string", "context": "coding"},
            {"prompt": "write a function to calculate fibonacci", "context": "coding"},
            {"prompt": "explain this sorting function", "context": "explanation"},
            {"prompt": "explain this recursion code", "context": "explanation"},
            {"prompt": "fix this syntax error", "context": "debugging"},
            {"prompt": "fix this logic error", "context": "debugging"},
        ]

        # Feed interactions to learning engine
        self.performance_monitor.start_timing("learning_phase")

        for interaction in interaction_patterns:
            claude_response = self.mock_claude.simulate_interaction(interaction["prompt"])

            # Record interaction in learning engine
            await learning_engine.record_interaction(
                prompt=interaction["prompt"],
                response=claude_response,
                context=interaction["context"],
                session_id=session_name,
            )

        learning_duration = self.performance_monitor.end_timing("learning_phase")

        # Test pattern detection
        self.performance_monitor.start_timing("pattern_detection")

        detected_patterns = await learning_engine.detect_patterns()

        detection_duration = self.performance_monitor.end_timing("pattern_detection")

        # Verify learning occurred
        assert len(detected_patterns) > 0, "No patterns detected from interactions"

        # Should detect coding pattern
        coding_patterns = [p for p in detected_patterns if "coding" in p.get("category", "").lower()]
        assert len(coding_patterns) > 0, "No coding patterns detected"

        # Should detect explanation pattern
        explanation_patterns = [p for p in detected_patterns if "explanation" in p.get("category", "").lower()]
        assert len(explanation_patterns) > 0, "No explanation patterns detected"

        # Performance checks
        assert learning_duration < 5.0, f"Learning phase took {learning_duration:.2f}s, should be < 5s"
        assert detection_duration < 2.0, f"Pattern detection took {detection_duration:.2f}s, should be < 2s"

    async def test_prediction_accuracy_improvement(self) -> None:
        """Test that prediction accuracy improves with more data."""
        session_name = "prediction-accuracy-session"
        self.create_test_session(session_name)

        learning_engine = LearningEngine(config=self.get_test_config(), session_name=session_name)

        # Phase 1: Initial training with limited data
        initial_interactions = [
            {"prompt": "create a login function", "context": "authentication"},
            {"prompt": "create a logout function", "context": "authentication"},
        ]

        for interaction in initial_interactions:
            response = self.mock_claude.simulate_interaction(interaction["prompt"])
            await learning_engine.record_interaction(
                prompt=interaction["prompt"],
                response=response,
                context=interaction["context"],
                session_id=session_name,
            )

        # Test initial prediction accuracy
        test_prompt = "create a password reset function"
        initial_prediction = await learning_engine.predict_response_context(test_prompt)

        # Phase 2: Extended training with more authentication data
        extended_interactions = [
            {"prompt": "implement user registration", "context": "authentication"},
            {"prompt": "add password validation", "context": "authentication"},
            {"prompt": "create session management", "context": "authentication"},
            {"prompt": "implement two-factor auth", "context": "authentication"},
        ]

        for interaction in extended_interactions:
            response = self.mock_claude.simulate_interaction(interaction["prompt"])
            await learning_engine.record_interaction(
                prompt=interaction["prompt"],
                response=response,
                context=interaction["context"],
                session_id=session_name,
            )

        # Test improved prediction accuracy
        improved_prediction = await learning_engine.predict_response_context(test_prompt)

        # Verify improvement
        assert improved_prediction is not None, "No prediction generated after extended training"

        # Confidence should improve with more data
        initial_confidence = initial_prediction.get("confidence", 0.0) if initial_prediction else 0.0
        improved_confidence = improved_prediction.get("confidence", 0.0)

        assert improved_confidence > initial_confidence, f"Confidence didn't improve: {initial_confidence} -> {improved_confidence}"
        assert improved_confidence > 0.7, f"Final confidence {improved_confidence} should be > 0.7"

    async def test_cross_session_learning(self) -> None:
        """Test that learning transfers across multiple sessions."""
        # Create multiple sessions
        sessions = ["session-1", "session-2", "session-3"]
        for session in sessions:
            self.create_test_session(session)

        learning_engine = LearningEngine(config=self.get_test_config())

        # Train on different sessions with overlapping patterns
        session_interactions = {
            "session-1": [
                {"prompt": "write a REST API endpoint", "context": "web_development"},
                {"prompt": "create database models", "context": "web_development"},
            ],
            "session-2": [
                {
                    "prompt": "implement API authentication",
                    "context": "web_development",
                },
                {"prompt": "add error handling to API", "context": "web_development"},
            ],
            "session-3": [
                {"prompt": "write unit tests for API", "context": "testing"},
                {"prompt": "create integration tests", "context": "testing"},
            ],
        }

        # Record interactions across sessions
        for session, interactions in session_interactions.items():
            for interaction in interactions:
                response = self.mock_claude.simulate_interaction(interaction["prompt"])
                await learning_engine.record_interaction(
                    prompt=interaction["prompt"],
                    response=response,
                    context=interaction["context"],
                    session_id=session,
                )

        # Test cross-session pattern detection
        global_patterns = await learning_engine.detect_patterns(session_id=None)  # All sessions

        # Should detect web development pattern across sessions
        web_dev_patterns = [p for p in global_patterns if "web" in p.get("category", "").lower()]
        assert len(web_dev_patterns) > 0, "No web development patterns detected across sessions"

        # Test prediction using cross-session knowledge
        test_prompt = "create API documentation"
        prediction = await learning_engine.predict_response_context(test_prompt, session_id=None)

        assert prediction is not None, "No cross-session prediction generated"
        assert prediction.get("confidence", 0.0) > 0.6, "Cross-session prediction confidence should be > 0.6"


class TestAutomationLearningIntegration(AsyncIntegrationTestBase):
    """Test integration between AI learning and automation workflows."""

    def setup_method(self) -> None:
        """Setup for automation learning tests."""
        super().setup_method()
        self.command_runner = CommandTestRunner(self)
        self.performance_monitor = PerformanceMonitor()

    async def test_context_detection_learning(self) -> None:
        """Test that AI learns to better detect contexts for automation."""
        # Create test project directory with various file types
        project_dir = self.test_dir / "test_project"
        project_dir.mkdir()

        # Create files that should trigger different contexts
        (project_dir / "requirements.txt").write_text("flask==2.0.0\npytest==6.0.0")
        (project_dir / "app.py").write_text("from flask import Flask\napp = Flask(__name__)")
        (project_dir / "test_app.py").write_text("import pytest\ndef test_app(): pass")
        (project_dir / ".git").mkdir()
        (project_dir / "README.md").write_text("# Test Project")

        # Initialize automation with learning
        learning_engine = LearningEngine(config=self.get_test_config())

        # Test initial context detection
        self.performance_monitor.start_timing("initial_context_detection")

        initial_result = self.command_runner.run_command(AutomateDetectCommand, project_path=str(project_dir))

        initial_duration = self.performance_monitor.end_timing("initial_context_detection")

        assert initial_result["success"] is True
        initial_contexts = initial_result.get("contexts", [])

        # Simulate learning from context detection results
        for context in initial_contexts:
            await learning_engine.record_context_detection(
                project_path=str(project_dir),
                detected_context=context,
                accuracy_feedback=1.0,  # Assume accurate
                session_id="automation-learning",
            )

        # Add more project complexity
        (project_dir / "Dockerfile").write_text("FROM python:3.9")
        (project_dir / "docker-compose.yml").write_text("version: '3.8'")
        (project_dir / "migrations").mkdir()

        # Test improved context detection
        self.performance_monitor.start_timing("improved_context_detection")

        improved_result = self.command_runner.run_command(AutomateDetectCommand, project_path=str(project_dir))

        improved_duration = self.performance_monitor.end_timing("improved_context_detection")

        assert improved_result["success"] is True
        improved_contexts = improved_result.get("contexts", [])

        # Should detect more contexts with learning
        assert len(improved_contexts) >= len(initial_contexts), "Learning didn't improve context detection"

        # Performance should be reasonable
        assert initial_duration < 3.0, f"Initial detection took {initial_duration:.2f}s, should be < 3s"
        assert improved_duration < 3.0, f"Improved detection took {improved_duration:.2f}s, should be < 3s"

    async def test_workflow_optimization_learning(self) -> None:
        """Test that AI learns to optimize automation workflows."""
        project_dir = self.test_dir / "workflow_project"
        project_dir.mkdir()

        # Create Python project structure
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "requirements.txt").write_text("pytest==6.0.0")
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "src" / "main.py").write_text("def main(): pass")
        (project_dir / "tests" / "test_main.py").write_text("def test_main(): pass")

        learning_engine = LearningEngine(config=self.get_test_config())

        # Simulate workflow execution and learning
        workflow_executions = [
            {
                "context": "python_project",
                "workflow": "run_tests",
                "execution_time": 2.5,
                "success": True,
            },
            {
                "context": "python_project",
                "workflow": "run_linting",
                "execution_time": 1.8,
                "success": True,
            },
            {
                "context": "python_project",
                "workflow": "run_tests",
                "execution_time": 2.2,  # Improved
                "success": True,
            },
        ]

        # Record workflow learning data
        for execution in workflow_executions:
            await learning_engine.record_workflow_execution(
                project_path=str(project_dir),
                workflow_type=execution["workflow"],
                context=execution["context"],
                execution_time=execution["execution_time"],
                success=execution["success"],
                session_id="workflow-optimization",
            )

        # Test workflow recommendations
        recommendations = await learning_engine.get_workflow_recommendations(project_path=str(project_dir), context="python_project")

        assert len(recommendations) > 0, "No workflow recommendations generated"

        # Should recommend faster workflows first
        run_test_recs = [r for r in recommendations if r.get("workflow") == "run_tests"]
        if run_test_recs:
            assert run_test_recs[0].get("estimated_time", 999) < 3.0, "Test execution time not optimized"


class TestLearningPersistenceIntegration(AsyncIntegrationTestBase):
    """Test that AI learning data persists correctly across sessions."""

    async def test_learning_data_persistence(self) -> None:
        """Test that learned patterns persist across system restarts."""
        session_name = "persistence-test-session"
        self.create_test_session(session_name)

        # Phase 1: Initial learning
        learning_engine_1 = LearningEngine(config=self.get_test_config(), session_name=session_name)

        # Train with specific patterns
        training_data = [
            {"prompt": "deploy to staging", "context": "deployment"},
            {"prompt": "deploy to production", "context": "deployment"},
            {"prompt": "rollback deployment", "context": "deployment"},
        ]

        for data in training_data:
            await learning_engine_1.record_interaction(
                prompt=data["prompt"],
                response=f"Executing {data['prompt']}...",
                context=data["context"],
                session_id=session_name,
            )

        # Save learned patterns
        patterns_1 = await learning_engine_1.detect_patterns()
        await learning_engine_1.save_patterns(patterns_1)

        # Phase 2: Simulate system restart with new learning engine instance
        learning_engine_2 = LearningEngine(config=self.get_test_config(), session_name=session_name)

        # Load persisted patterns
        loaded_patterns = await learning_engine_2.load_patterns()

        # Verify persistence
        assert len(loaded_patterns) > 0, "No patterns loaded from persistence"

        deployment_patterns = [p for p in loaded_patterns if "deployment" in p.get("category", "").lower()]
        assert len(deployment_patterns) > 0, "Deployment patterns not persisted"

        # Test prediction with persisted data
        test_prompt = "deploy to development"
        prediction = await learning_engine_2.predict_response_context(test_prompt)

        assert prediction is not None, "No prediction from persisted patterns"
        assert prediction.get("confidence", 0.0) > 0.5, "Low confidence from persisted patterns"

    async def test_incremental_learning_persistence(self) -> None:
        """Test that incremental learning updates are persisted correctly."""
        session_name = "incremental-learning-session"
        self.create_test_session(session_name)

        learning_engine = LearningEngine(config=self.get_test_config(), session_name=session_name)

        # Initial training batch
        initial_batch = [
            {"prompt": "create user model", "context": "database"},
            {"prompt": "create product model", "context": "database"},
        ]

        for data in initial_batch:
            await learning_engine.record_interaction(
                prompt=data["prompt"],
                response=f"Creating {data['prompt']}...",
                context=data["context"],
                session_id=session_name,
            )

        initial_patterns = await learning_engine.detect_patterns()
        initial_count = len(initial_patterns)

        # Incremental training batch
        incremental_batch = [
            {"prompt": "create order model", "context": "database"},
            {"prompt": "add database indexes", "context": "database"},
            {"prompt": "optimize database queries", "context": "database"},
        ]

        for data in incremental_batch:
            await learning_engine.record_interaction(
                prompt=data["prompt"],
                response=f"Executing {data['prompt']}...",
                context=data["context"],
                session_id=session_name,
            )

        # Detect patterns after incremental learning
        updated_patterns = await learning_engine.detect_patterns()
        updated_count = len(updated_patterns)

        # Verify incremental learning
        assert updated_count >= initial_count, "Incremental learning didn't add patterns"

        # Save and reload to test persistence
        await learning_engine.save_patterns(updated_patterns)

        # New engine instance
        new_engine = LearningEngine(config=self.get_test_config(), session_name=session_name)

        reloaded_patterns = await new_engine.load_patterns()
        assert len(reloaded_patterns) == updated_count, "Incremental patterns not persisted correctly"
