"""Integration tests for API endpoints"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from libs.core.services import register_test_services


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_services():
    """Setup test services before each test"""
    mock_config = MagicMock()
    mock_config.get.return_value = "test_value"
    mock_config.schema.logging.level = "INFO"

    mock_tmux = MagicMock()
    mock_tmux.list_running_sessions.return_value = []

    register_test_services(config=mock_config, tmux_manager=mock_tmux)


class TestHealthEndpoints:
    """Test health and info endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "yesman-claude-api"
        assert "timestamp" in data

    def test_api_info(self, client):
        """Test API info endpoint"""
        response = client.get("/api")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Yesman Claude API"
        assert "endpoints" in data
        assert "version" in data


class TestConfigAPI:
    """Test configuration API endpoints"""

    def test_get_config(self, client):
        """Test get configuration endpoint"""
        with patch("api.routers.config.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.config = {"log_level": "INFO", "log_path": "/tmp/test.log"}
            mock_get_config.return_value = mock_config

            response = client.get("/api/config")

            assert response.status_code == 200
            data = response.json()
            assert data["log_level"] == "INFO"

    def test_get_config_error_handling(self, client):
        """Test configuration error handling"""
        with patch("api.routers.config.get_config") as mock_get_config:
            mock_get_config.side_effect = Exception("Config error")

            response = client.get("/api/config")

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert data["error"]["category"] == "system"

    def test_get_available_projects(self, client):
        """Test get available projects endpoint"""
        with patch("api.routers.config.get_tmux_manager") as mock_get_tmux:
            mock_tmux = MagicMock()
            mock_tmux.load_projects.return_value = {"sessions": {"project1": {"name": "project1"}, "project2": {"name": "project2"}}}
            mock_get_tmux.return_value = mock_tmux

            response = client.get("/api/config/projects")

            assert response.status_code == 200
            data = response.json()
            assert "project1" in data
            assert "project2" in data


class TestSessionsAPI:
    """Test sessions API endpoints"""

    def test_get_sessions(self, client):
        """Test get sessions endpoint"""
        with patch("api.routers.sessions.get_tmux_manager") as mock_get_tmux:
            mock_tmux = MagicMock()
            mock_tmux.get_all_sessions.return_value = [{"name": "session1", "windows": 2}, {"name": "session2", "windows": 1}]
            mock_get_tmux.return_value = mock_tmux

            response = client.get("/api/sessions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "session1"

    def test_create_session(self, client):
        """Test create session endpoint"""
        with patch("api.routers.sessions.get_tmux_manager") as mock_get_tmux:
            mock_tmux = MagicMock()
            mock_tmux.create_session.return_value = True
            mock_get_tmux.return_value = mock_tmux

            response = client.post("/api/sessions", json={"name": "test-session", "project_path": "/tmp/test"})

            assert response.status_code == 201
            data = response.json()
            assert data["message"] == "Session created successfully"


class TestErrorHandling:
    """Test API error handling"""

    def test_validation_error_response(self, client):
        """Test validation error response format"""
        # Send invalid data to trigger validation error
        response = client.post("/api/sessions", json={"invalid_field": "invalid_value"})

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["category"] == "validation"
        assert "request_id" in data["error"]

    def test_custom_error_response(self, client):
        """Test custom YesmanError response format"""
        with patch("api.routers.config.get_config") as mock_get_config:
            from libs.core.error_handling import ConfigurationError

            mock_get_config.side_effect = ConfigurationError("Configuration file not found", config_file="/missing/config.yaml")

            response = client.get("/api/config")

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            error = data["error"]
            assert error["code"].startswith("CONFIGURATION_")
            assert error["category"] == "configuration"
            assert error["recovery_hint"] is not None
            assert "context" in error

    def test_request_id_header(self, client):
        """Test that request ID is added to response headers"""
        response = client.get("/healthz")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers


class TestAPIAuthentication:
    """Test API authentication (if implemented)"""

    @pytest.mark.skip(reason="Authentication not implemented yet")
    def test_protected_endpoint(self, client):
        """Test protected endpoint access"""
        response = client.get("/api/protected")
        assert response.status_code == 401


class TestAPIPerformance:
    """Test API performance"""

    def test_health_endpoint_performance(self, client):
        """Test health endpoint response time"""
        import time

        start_time = time.time()
        response = client.get("/healthz")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond within 100ms

    def test_concurrent_requests(self, client):
        """Test handling multiple concurrent requests"""
        import threading

        results = []

        def make_request():
            response = client.get("/healthz")
            results.append(response.status_code)

        # Start 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)
