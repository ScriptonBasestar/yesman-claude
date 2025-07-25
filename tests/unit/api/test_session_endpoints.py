# Copyright notice.

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# Import here to avoid circular imports
from api.main import app

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test for FastAPI session endpoints."""


class TestSessionEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("api.routes.sessions.SessionManager")
    def test_get_sessions_list(self, mock_session_manager: object) -> None:
        """Test GET /api/sessions returns session list."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_all_sessions.return_value = [
            {
                "session_name": "test-session",
                "status": "active",
                "windows": 2,
                "created_at": "2024-01-08T10:00:00",
            },
        ]
        mock_session_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.get("/api/sessions")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["session_name"] == "test-session"

    @patch("api.routes.sessions.SessionManager")
    def test_get_session_detail(self, mock_session_manager: object) -> None:
        """Test GET /api/sessions/{session_name} returns session details."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_session_info.return_value = {
            "session_name": "test-session",
            "status": "active",
            "windows": [
                {"name": "main", "panes": 2},
                {"name": "logs", "panes": 1},
            ],
            "controller_status": "running",
        }
        mock_session_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.get("/api/sessions/test-session")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_name"] == "test-session"
        assert data["controller_status"] == "running"
        assert len(data["windows"]) == 2

    @patch("api.routes.sessions.SessionManager")
    def test_create_session(self, mock_session_manager: object) -> None:
        """Test POST /api/sessions creates new session."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.post(
            "/api/sessions",
            json={
                "session_name": "new-session",
                "template": "template.yaml",
            },
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Session created"
        mock_manager_instance.create_session.assert_called_once_with(
            "new-session",
            "template.yaml",
        )

    @patch("api.routes.sessions.SessionManager")
    def test_delete_session(self, mock_session_manager: object) -> None:
        """Test DELETE /api/sessions/{session_name} removes session."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.kill_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.delete("/api/sessions/test-session")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session deleted"
        mock_manager_instance.kill_session.assert_called_once_with("test-session")

    @patch("api.routes.sessions.SessionManager")
    def test_get_nonexistent_session(self, mock_session_manager: object) -> None:
        """Test GET for non-existent session returns 404."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_session_info.return_value = None
        mock_session_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.get("/api/sessions/nonexistent")

        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("api.routes.sessions.SessionManager")
    def test_create_duplicate_session(self, mock_session_manager: object) -> None:
        """Test creating duplicate session returns 409."""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.side_effect = Exception(
            "Session already exists"
        )
        mock_session_manager.return_value = mock_manager_instance

        # Make request
        response = self.client.post(
            "/api/sessions",
            json={
                "session_name": "existing-session",
                "template": "template.yaml",
            },
        )

        # Assertions
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()
