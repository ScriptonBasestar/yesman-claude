# Copyright notice.

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# Import here to avoid circular imports
from api.main import app

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test for FastAPI controller endpoints."""


class TestControllerEndpoints(unittest.TestCase):
    def setUp(self) -> None:

        self.client = TestClient(app)

    @patch("api.routes.controllers.ClaudeManager")
    def test_start_controller(self, mock_claude_manager: MagicMock) -> None:
        """Test POST /api/controllers/{session_name}/start."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_controller = MagicMock()
        mock_controller.start.return_value = True
        mock_controller.pid = 12345
        mock_manager_instance.get_controller.return_value = mock_controller
        mock_claude_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.post("/api/controllers/test-session/start")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["pid"] == 12345
        mock_controller.start.assert_called_once()

    @patch("api.routes.controllers.ClaudeManager")
    def test_stop_controller(self, mock_claude_manager: MagicMock) -> None:
        """Test POST /api/controllers/{session_name}/stop."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_controller = MagicMock()
        mock_controller.stop.return_value = True
        mock_manager_instance.get_controller.return_value = mock_controller
        mock_claude_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.post("/api/controllers/test-session/stop")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        mock_controller.stop.assert_called_once()

    @patch("api.routes.controllers.ClaudeManager")
    def test_restart_controller(self, mock_claude_manager: MagicMock) -> None:
        """Test POST /api/controllers/{session_name}/restart."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_controller = MagicMock()
        mock_controller.restart.return_value = True
        mock_controller.pid = 54321
        mock_manager_instance.get_controller.return_value = mock_controller
        mock_claude_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.post("/api/controllers/test-session/restart")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "restarted"
        assert data["pid"] == 54321
        mock_controller.restart.assert_called_once()

    @patch("api.routes.controllers.ClaudeManager")
    def test_get_controller_status(self, mock_claude_manager: MagicMock) -> None:
        """Test GET /api/controllers/{session_name}/status."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_controller = MagicMock()
        mock_controller.get_status.return_value = {
            "status": "running",
            "pid": 12345,
            "uptime": "2h 30m",
            "auto_response_enabled": True,
        }
        mock_manager_instance.get_controller.return_value = mock_controller
        mock_claude_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.get("/api/controllers/test-session/status")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["pid"] == 12345
        assert data["auto_response_enabled"]

    @patch("api.routes.controllers.ClaudeManager")
    def test_controller_not_found(self, mock_claude_manager: MagicMock) -> None:
        """Test controller operations on non-existent session."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_controller.return_value = None
        mock_claude_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.post("/api/controllers/nonexistent/start")

        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("api.routes.controllers.ClaudeManager")
    def test_enable_auto_response(self, mock_claude_manager: MagicMock) -> None:
        """Test PUT /api/controllers/{session_name}/auto-response."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_controller = MagicMock()
        mock_controller.set_auto_response.return_value = True
        mock_manager_instance.get_controller.return_value = mock_controller
        mock_claude_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.put(
            "/api/controllers/test-session/auto-response",
            json={
                "enabled": True,
                "default_choice": "1",
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["auto_response_enabled"]
        mock_controller.set_auto_response.assert_called_once_with(True, "1")

    @patch("api.routes.controllers.ClaudeManager")
    def test_controller_error_handling(self, mock_claude_manager: MagicMock) -> None:
        """Test controller error handling."""
        # Setup mock to raise exception
        mock_manager_instance = MagicMock()
        mock_controller = MagicMock()
        mock_controller.start.side_effect = Exception("Failed to start controller")
        mock_manager_instance.get_controller.return_value = mock_controller
        mock_claude_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.post("/api/controllers/test-session/start")

        # Assertions
        assert response.status_code == 500
        data = response.json()
        assert "failed" in data["detail"].lower()
