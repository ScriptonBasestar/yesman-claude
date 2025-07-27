import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from libs.core.error_handling import ConfigurationError
from libs.core.services import register_test_services

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Integration tests for API endpoints."""


@pytest.fixture
def client() -> object:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_services() -> None:
    """Setup test services before each test."""
    mock_config = MagicMock()
    mock_config.get.return_value = "test_value"
    mock_config.schema.logging.level = "INFO"
    # Add config dict that the API expects
    mock_config.config = {
        "log_level": "INFO",
        "log_path": "/tmp/test.log"
    }

    mock_tmux = MagicMock()
    mock_tmux.list_running_sessions.return_value = []
    mock_tmux.load_projects.return_value = {"sessions": {}}

    register_test_services(config=mock_config, tmux_manager=mock_tmux)


class TestHealthEndpoints:
    """Test health and info endpoints."""

    @staticmethod
    def test_health_check(client: TestClient) -> None:
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
        response = client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["log_level"] == "INFO"
        assert data["log_path"] == "/tmp/test.log"

    @staticmethod
    def test_get_config_error_handling(client: TestClient) -> None:
        """Test configuration error handling."""
        # Test the actual error handling in the API
        # We can't easily override the registered service, so we'll test a different error path
        # The endpoint catches specific exceptions, so let's patch deeper
        with patch("api.routers.config.get_config") as mock_get_config:
            # Make it raise an exception that will be caught
            mock_get_config.side_effect = ValueError("Config error")

            response = client.get("/api/config")

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            # Check the error format
            assert "Failed to get config" in data["error"]["message"]

    @staticmethod
    def test_get_available_projects(client: TestClient) -> None:
        """Test get available projects endpoint."""
        # The mock tmux_manager is already set up with an empty sessions dict
        response = client.get("/api/config/projects")

        assert response.status_code == 200
        data = response.json()
        # Should return an empty list since no sessions are configured
        assert isinstance(data, list)
        assert len(data) == 0


class TestSessionsAPI:
    """Test sessions API endpoints."""

    @staticmethod
    def test_get_sessions(client: TestClient) -> None:
        """Test get sessions endpoint."""
        response = client.get("/api/sessions")

        assert response.status_code == 200
        data = response.json()
        
        # Check that the response is a list
        assert isinstance(data, list)
        
        # If there are sessions, verify the structure
        if data:
            # Verify the first session has the expected structure
            session = data[0]
            assert "session_name" in session
            assert "status" in session
            assert "windows" in session
            assert isinstance(session["windows"], list)

    @staticmethod
    def test_setup_session(client: TestClient) -> None:
        """Test setup session endpoint."""
        # Try to setup a session that doesn't exist
        response = client.post("/api/sessions/test-session/setup")

        # Since the mocked tmux_manager has empty sessions, this should fail
        # The error is a CONFIGURATION error, not VALIDATION, so it returns 500
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "not found in projects configuration" in data["error"]["message"]


class TestErrorHandling:
    """Test API error handling."""

    @staticmethod
    def test_validation_error_response(client: TestClient) -> None:
        """Test validation error response format."""
        # Send invalid data to trigger validation error - POST /config expects AppConfig model
        response = client.post("/api/config", json={"invalid_field": "invalid_value"})

        assert response.status_code == 422
        data = response.json()
        # The API returns a custom error format
        assert "error" in data
        error = data["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["category"] == "validation"
        assert "request_id" in error
        # Check that validation errors are in the context
        assert "validation_errors" in error["context"]
        validation_errors = error["context"]["validation_errors"]
        assert len(validation_errors) == 2  # log_level and log_path are required
        assert any(e["field"] == "body.log_level" for e in validation_errors)
        assert any(e["field"] == "body.log_path" for e in validation_errors)

    @staticmethod
    def test_custom_error_response(client: TestClient) -> None:
        """Test custom YesmanError response format."""
        # Test with the setup endpoint which returns YesmanError
        response = client.post("/api/sessions/nonexistent-session/setup")

        # This should return a YesmanError with configuration category
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == "HTTP_500"  # HTTPException wraps the original error
        assert "not found in projects configuration" in error["message"]

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
        start_time = time.time()
        response = client.get("/healthz")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond within 100ms

    @staticmethod
    def test_concurrent_requests(client: TestClient) -> None:
        """Test handling multiple concurrent requests."""
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
