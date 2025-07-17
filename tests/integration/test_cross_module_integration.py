#!/usr/bin/env python3
"""
Cross-Module Integration Tests

Tests integration across all major system modules including CLI, automation,
AI learning, session management, and dashboard coordination.
"""

from commands.automate import AutomateDetectCommand, AutomateMonitorCommand
from commands.browse import BrowseCommand
from commands.setup import SetupCommand
from commands.status import StatusCommand
from libs.ai.learning_engine import LearningEngine

from .test_framework import AsyncIntegrationTestBase, CommandTestRunner, MockClaudeEnvironment, PerformanceMonitor


class TestFullSystemIntegration(AsyncIntegrationTestBase):
    """Test complete system integration across all modules"""

    def setup_method(self):
        """Setup for full system integration tests"""
        super().setup_method()
        self.command_runner = CommandTestRunner(self)
        self.performance_monitor = PerformanceMonitor()
        self.mock_claude = MockClaudeEnvironment(self.test_dir)

        # Setup comprehensive mock responses
        self._setup_comprehensive_responses()

    def _setup_comprehensive_responses(self):
        """Setup mock Claude responses for comprehensive testing"""
        responses = {
            "develop web application": "I'll help you develop a web application. Let me set up the project structure...",
            "test the application": "Running comprehensive tests... All tests passed successfully!",
            "deploy to production": "Deploying application to production environment... Deployment successful!",
            "monitor performance": "Monitoring application performance... All metrics within normal ranges.",
            "optimize database": "Analyzing database performance... Optimization recommendations ready.",
            "security audit": "Performing security audit... No critical vulnerabilities found.",
            "backup data": "Creating data backup... Backup completed successfully.",
            "scale infrastructure": "Scaling infrastructure based on load... Scaling completed.",
        }

        for prompt, response in responses.items():
            self.mock_claude.add_mock_response(prompt, response)

    async def test_complete_development_workflow(self):
        """Test complete development workflow across all system modules"""
        # Phase 1: Project Setup and Session Management
        project_name = "full-system-project"
        project_dir = self.test_dir / project_name
        project_dir.mkdir()

        # Create comprehensive project structure
        self._create_comprehensive_project(project_dir)

        # Create and setup session
        session_name = f"{project_name}-session"
        self.create_test_session(session_name, description="Full system integration test")

        self.performance_monitor.start_timing("session_setup")

        session_result = self.command_runner.run_command(SetupCommand, session_name=session_name)

        session_duration = self.performance_monitor.end_timing("session_setup")

        assert session_result["success"] is True
        assert session_duration < 10.0

        # Phase 2: Automation and Context Detection
        self.performance_monitor.start_timing("automation_detection")

        detect_result = self.command_runner.run_command(AutomateDetectCommand, project_path=str(project_dir), suggest_workflows=True)

        detection_duration = self.performance_monitor.end_timing("automation_detection")

        assert detect_result["success"] is True
        assert len(detect_result.get("contexts", [])) >= 3  # Should detect multiple contexts
        assert detection_duration < 5.0

        # Phase 3: AI Learning Integration
        learning_engine = LearningEngine(config=self.get_test_config(), session_name=session_name)

        # Simulate development interactions for learning
        development_interactions = [
            {"prompt": "develop web application", "context": "web_development"},
            {"prompt": "test the application", "context": "testing"},
            {"prompt": "deploy to production", "context": "deployment"},
            {"prompt": "monitor performance", "context": "monitoring"},
        ]

        self.performance_monitor.start_timing("ai_learning")

        for interaction in development_interactions:
            response = self.mock_claude.simulate_interaction(interaction["prompt"])
            await learning_engine.record_interaction(prompt=interaction["prompt"], response=response, context=interaction["context"], session_id=session_name)

        learning_duration = self.performance_monitor.end_timing("ai_learning")

        assert learning_duration < 3.0

        # Test pattern detection
        patterns = await learning_engine.detect_patterns()
        assert len(patterns) > 0

        # Phase 4: Browse Integration with Session Context
        self.performance_monitor.start_timing("browse_integration")

        browse_result = self.command_runner.run_command(BrowseCommand, path=str(project_dir), session_context=session_name)

        browse_duration = self.performance_monitor.end_timing("browse_integration")

        assert browse_result["success"] is True
        assert browse_duration < 8.0

        # Phase 5: Status Integration with All Modules
        self.performance_monitor.start_timing("status_integration")

        status_result = self.command_runner.run_command(StatusCommand, detailed=True, include_automation=True, include_ai_metrics=True)

        status_duration = self.performance_monitor.end_timing("status_integration")

        assert status_result["success"] is True
        assert status_duration < 3.0

        # Verify comprehensive status data
        assert "sessions" in status_result
        assert "automation" in status_result
        assert "ai_learning" in status_result

        # Phase 6: Monitoring Integration
        self.performance_monitor.start_timing("monitoring_integration")

        monitor_result = self.command_runner.run_command(AutomateMonitorCommand, project_path=str(project_dir), duration=2, enable_ai_insights=True, session_integration=session_name)

        monitoring_duration = self.performance_monitor.end_timing("monitoring_integration")

        assert monitor_result["success"] is True
        assert monitoring_duration < 8.0

        # Total workflow performance check
        total_workflow_time = session_duration + detection_duration + learning_duration + browse_duration + status_duration + monitoring_duration

        assert total_workflow_time < 45.0, f"Complete workflow took {total_workflow_time:.2f}s, should be < 45s"

    def _create_comprehensive_project(self, project_dir):
        """Create a comprehensive project with multiple contexts"""
        # Python web application
        (project_dir / "app.py").write_text("""
from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/api/data')
def get_data():
    return jsonify({'data': 'sample'})

if __name__ == '__main__':
    app.run(debug=True)
""")

        (project_dir / "requirements.txt").write_text("""
flask==2.0.0
pytest==6.0.0
pytest-cov==2.12.0
gunicorn==20.1.0
""")

        # Database files
        (project_dir / "database").mkdir()
        (project_dir / "database" / "schema.sql").write_text("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
""")

        # Test files
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "__init__.py").write_text("")
        (project_dir / "tests" / "test_app.py").write_text("""
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert b'healthy' in rv.data

def test_get_data(client):
    rv = client.get('/api/data')
    assert rv.status_code == 200
    assert b'data' in rv.data
""")

        # Docker files
        (project_dir / "Dockerfile").write_text("""
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
""")

        (project_dir / "docker-compose.yml").write_text("""
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""")

        # CI/CD configuration
        (project_dir / ".github").mkdir()
        (project_dir / ".github" / "workflows").mkdir()
        (project_dir / ".github" / "workflows" / "ci.yml").write_text("""
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest --cov=app tests/

    - name: Build Docker image
      run: |
        docker build -t app:latest .
""")

        # Configuration files
        (project_dir / "config.py").write_text("""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
""")

        # Git configuration
        (project_dir / ".git").mkdir()
        (project_dir / ".gitignore").write_text("""
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.pytest_cache/
htmlcov/
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

*.db
*.sqlite3

.env
.env.local
.env.*.local

node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
""")

        # Documentation
        (project_dir / "README.md").write_text("""
# Full System Integration Test Project

This project demonstrates a comprehensive web application with multiple technology contexts:

## Features
- Flask web API
- SQLite database with schema
- Comprehensive test suite
- Docker containerization
- CI/CD pipeline
- Production-ready configuration

## Technology Stack
- Python/Flask
- SQLite/PostgreSQL
- Docker & Docker Compose
- GitHub Actions CI/CD
- Pytest for testing

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Start development server: `python app.py`
4. Build Docker image: `docker build -t app .`
5. Run with Docker Compose: `docker-compose up`

## Project Structure
- `app.py` - Main Flask application
- `tests/` - Test suite
- `database/` - Database schema and migrations
- `config.py` - Application configuration
- `Dockerfile` & `docker-compose.yml` - Container configuration
- `.github/workflows/` - CI/CD pipelines
""")

    async def test_cross_module_data_flow(self):
        """Test data flow and communication between modules"""
        # Setup project and session
        project_dir = self.test_dir / "data_flow_project"
        project_dir.mkdir()

        (project_dir / "main.py").write_text("print('Data flow test')")
        (project_dir / "config.yaml").write_text("setting: value")

        session_name = "data-flow-session"
        self.create_test_session(session_name)

        # Initialize all modules
        learning_engine = LearningEngine(config=self.get_test_config(), session_name=session_name)

        session_manager = self.get_session_manager()

        # Test 1: Session → Automation data flow
        setup_result = self.command_runner.run_command(SetupCommand, session_name=session_name)
        assert setup_result["success"] is True

        # Automation should be aware of session context
        detect_result = self.command_runner.run_command(AutomateDetectCommand, project_path=str(project_dir), session_context=session_name)
        assert detect_result["success"] is True

        # Test 2: Automation → AI Learning data flow
        for context in detect_result.get("contexts", [])[:3]:  # Limit for testing
            await learning_engine.record_context_detection(project_path=str(project_dir), detected_context=context, accuracy_feedback=1.0, session_id=session_name)

        # AI should learn from automation data
        patterns = await learning_engine.detect_patterns()
        assert len(patterns) > 0

        # Test 3: AI Learning → Session enhancement data flow
        prediction = await learning_engine.predict_response_context("setup development environment", session_id=session_name)

        if prediction:
            assert prediction.get("confidence", 0) > 0

        # Test 4: Cross-module status integration
        status_result = self.command_runner.run_command(StatusCommand, session_name=session_name, include_ai_metrics=True, include_automation=True)

        assert status_result["success"] is True

        # Status should include data from all modules
        assert "sessions" in status_result
        assert session_name in [s["name"] for s in status_result.get("sessions", [])]

    async def test_error_propagation_and_recovery(self):
        """Test error handling and recovery across modules"""
        # Create problematic project
        project_dir = self.test_dir / "error_test_project"
        project_dir.mkdir()

        # Files that might cause issues
        (project_dir / "broken.py").write_text("import non_existent_module\nsyntax error here")
        (project_dir / "empty.txt").write_text("")

        session_name = "error-recovery-session"

        # Test 1: Session creation with problematic project should still work
        self.create_test_session(session_name, start_directory=str(project_dir))

        setup_result = self.command_runner.run_command(SetupCommand, session_name=session_name)

        # Should succeed despite problematic files in directory
        assert setup_result["success"] is True

        # Test 2: Automation should handle problematic files gracefully
        detect_result = self.command_runner.run_command(AutomateDetectCommand, project_path=str(project_dir), ignore_errors=True)

        # Should succeed with error handling
        assert detect_result["success"] is True
        if "errors" in detect_result:
            assert len(detect_result["errors"]) > 0  # Should report errors

        # Test 3: AI learning should handle incomplete data
        learning_engine = LearningEngine(config=self.get_test_config(), session_name=session_name)

        # Record interaction with error context
        await learning_engine.record_interaction(prompt="fix this broken code", response="I see syntax errors in your code. Let me help fix them.", context="error_handling", session_id=session_name)

        patterns = await learning_engine.detect_patterns()
        # Should work despite error context
        assert isinstance(patterns, list)

        # Test 4: Browse should handle problematic files
        browse_result = self.command_runner.run_command(BrowseCommand, path=str(project_dir), ignore_errors=True)

        assert browse_result["success"] is True

        # Test 5: Status should report system health despite errors
        status_result = self.command_runner.run_command(StatusCommand)
        assert status_result["success"] is True

    async def test_performance_under_concurrent_load(self):
        """Test system performance under concurrent operations"""
        # Create multiple projects and sessions
        project_count = 5
        projects = []
        sessions = []

        # Setup phase
        self.performance_monitor.start_timing("concurrent_setup")

        for i in range(project_count):
            project_dir = self.test_dir / f"concurrent_project_{i}"
            project_dir.mkdir()

            (project_dir / "app.py").write_text(f"print('Project {i}')")
            (project_dir / "requirements.txt").write_text("requests==2.25.1")

            session_name = f"concurrent-session-{i}"
            self.create_test_session(session_name)

            projects.append(project_dir)
            sessions.append(session_name)

        setup_duration = self.performance_monitor.end_timing("concurrent_setup")

        # Concurrent operations phase
        self.performance_monitor.start_timing("concurrent_operations")

        # Setup all sessions concurrently (simulated)
        for session_name in sessions:
            result = self.command_runner.run_command(SetupCommand, session_name=session_name)
            assert result["success"] is True

        # Run automation detection on all projects
        for project_dir in projects:
            result = self.command_runner.run_command(AutomateDetectCommand, project_path=str(project_dir))
            assert result["success"] is True

        operations_duration = self.performance_monitor.end_timing("concurrent_operations")

        # AI learning phase
        self.performance_monitor.start_timing("concurrent_ai_learning")

        learning_engine = LearningEngine(config=self.get_test_config())

        # Record interactions for all sessions
        for i, session_name in enumerate(sessions):
            await learning_engine.record_interaction(prompt=f"develop project {i}", response=f"Developing project {i} with Python...", context="development", session_id=session_name)

        ai_learning_duration = self.performance_monitor.end_timing("concurrent_ai_learning")

        # Global status check
        self.performance_monitor.start_timing("global_status")

        status_result = self.command_runner.run_command(StatusCommand)
        assert status_result["success"] is True

        # Should show all sessions
        status_sessions = status_result.get("sessions", [])
        status_session_names = [s["name"] for s in status_sessions]

        for session_name in sessions:
            assert session_name in status_session_names

        status_duration = self.performance_monitor.end_timing("global_status")

        # Performance assertions
        total_duration = setup_duration + operations_duration + ai_learning_duration + status_duration

        assert setup_duration < 15.0, f"Concurrent setup took {setup_duration:.2f}s, should be < 15s"
        assert operations_duration < 25.0, f"Concurrent operations took {operations_duration:.2f}s, should be < 25s"
        assert ai_learning_duration < 5.0, f"AI learning took {ai_learning_duration:.2f}s, should be < 5s"
        assert status_duration < 3.0, f"Global status took {status_duration:.2f}s, should be < 3s"
        assert total_duration < 50.0, f"Total concurrent load test took {total_duration:.2f}s, should be < 50s"
