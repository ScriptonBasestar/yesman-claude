"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Integration tests for API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from libs.core.services import register_test_services


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_services() -> None:
    """Setup test services before each test."""
    mock_config = MagicMock()
    mock_config.get.return_value = "test_value"
    mock_config.schema.logging.level = "INFO"

    mock_tmux = MagicMock()
    mock_tmux.list_running_sessions.return_value = []

    register_test_services(config=mock_config, tmux_manager=mock_tmux)


class TestHealthEndpoints:
    """Test health and info endpoints."""

    @staticmethod
    def test_health_check( client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "yesman-claude-api"
        assert "timestamp" in data

    @staticmethod
    def test_api_info(client: TestClient) -> None:
        """Test API info endpoint."""
        response = client.get("/api")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Yesman Claude API"
        assert "endpoints" in data
        assert "version" in data


class TestConfigAPI:
    """Test configuration API endpoints."""

    @staticmethod
    def test_get_config(client: TestClient) -> None:
        """Test get configuration endpoint."""
        with patch("api.routers.config.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.config = {"log_level": "INFO", "log_path": "/tmp/test.log"}
            mock_get_config.return_value = mock_config

            response = client.get("/api/config")

            assert response.status_code == 200
            data = response.json()
            assert data["log_level"] == "INFO"

    @staticmethod
    def test_get_config_error_handling(client: TestClient) -> None:
        """Test configuration error handling."""
        with patch("api.routers.config.get_config") as mock_get_config:
            mock_get_config.side_effect = Exception("Config error")

            response = client.get("/api/config")

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert data["error"]["category"] == "system"

    @staticmethod
    def test_get_available_projects(client: TestClient) -> None:
        """Test get available projects endpoint."""
        with patch("api.routers.config.get_tmux_manager") as mock_get_tmux:
            mock_tmux = MagicMock()
            mock_tmux.load_projects.return_value = {
                "sessions": {
                    "project1": {"name": "project1"},
                    "project2": {"name": "project2"},
                }
            }
            mock_get_tmux.return_value = mock_tmux

            response = client.get("/api/config/projects")

            assert response.status_code == 200
            data = response.json()
            assert "project1" in data
            assert "project2" in data


class TestSessionsAPI:
    """Test sessions API endpoints."""

    @staticmethod
    def test_get_sessions(client: TestClient) -> None:
        """Test get sessions endpoint."""
        with patch("api.routers.sessions.get_tmux_manager") as mock_get_tmux:
            mock_tmux = MagicMock()
            mock_tmux.get_all_sessions.return_value = [
                {"name": "session1", "windows": 2},
                {"name": "session2", "windows": 1},
            ]
            mock_get_tmux.return_value = mock_tmux

            response = client.get("/api/sessions")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "session1"

    @staticmethod
    def test_create_session(client: TestClient) -> None:
        """Test create session endpoint."""
        with patch("api.routers.sessions.get_tmux_manager") as mock_get_tmux:
            mock_tmux = MagicMock()
            mock_tmux.create_session.return_value = True
            mock_get_tmux.return_value = mock_tmux

            response = client.post(
                "/api/sessions",
                json={"name": "test-session", "project_path": "/tmp/test"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["message"] == "Session created successfully"


class TestErrorHandling:
    """Test API error handling."""

    @staticmethod
    def test_validation_error_response(client: TestClient) -> None:
        """Test validation error response format."""
        # Send invalid data to trigger validation error
        response = client.post("/api/sessions", json={"invalid_field": "invalid_value"})

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["category"] == "validation"
        assert "request_id" in data["error"]

    @staticmethod
    def test_custom_error_response(client: TestClient) -> None:
        """Test custom YesmanError response format."""
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

    @staticmethod
    def test_request_id_header(client: TestClient) -> None:
        """Test that request ID is added to response headers."""
        response = client.get("/healthz")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers


class TestAPIAuthentication:
    """Test API authentication (if implemented)."""

    @pytest.mark.skip(reason="Authentication not implemented yet")
    @staticmethod
    def test_protected_endpoint(client: TestClient) -> None:
        """Test protected endpoint access."""
        response = client.get("/api/protected")
        assert response.status_code == 401


class TestAPIPerformance:
    """Test API performance."""

    @staticmethod
    def test_health_endpoint_performance(client: TestClient) -> None:
        """Test health endpoint response time."""
        import time

        start_time = time.time()
        response = client.get("/healthz")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond within 100ms

    @staticmethod
    def test_concurrent_requests(client: TestClient) -> None:
        """Test handling multiple concurrent requests."""
        import threading

        results = []

        def make_request() -> None:
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
