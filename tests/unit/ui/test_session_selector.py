# Copyright notice.

import unittest
from unittest.mock import MagicMock, patch
from libs.ui.session_selector import SessionSelector

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test for session selector UI."""


class TestSessionSelector(unittest.TestCase):
    def setUp(self) -> None:
        self.test_sessions = [
            {"project": "project1", "session": "session1"},
            {"project": "project2", "session": "session2"},
            {"project": "myapp", "session": "myapp-dev"},
        ]

    @patch("libs.ui.session_selector.libtmux.Server")
    def test_get_session_details(self, mock_server_class: MagicMock) -> None:
        """Test getting session details from tmux."""
        # Mock tmux session
        mock_session = MagicMock()
        mock_session.windows = [MagicMock(name="window1"), MagicMock(name="window2")]
        mock_session.attached = 1

        mock_server = MagicMock()
        mock_server.find_where.return_value = mock_session
        mock_server_class.return_value = mock_server

        selector = SessionSelector(self.test_sessions)
        details = selector._get_session_details("session1")

        assert details["windows"] == 2
        assert details["attached"]
        assert details["clients"] == 1

    def test_create_display_no_filter(self) -> None:
        """Test creating display without filter."""
        selector = SessionSelector(self.test_sessions)

        with patch.object(selector, "_get_session_details") as mock_get_details:
            mock_get_details.return_value = {
                "windows": 3,
                "window_names": "win1, win2, win3",
                "attached": False,
                "clients": 0,
            }

            table, filtered = selector._create_display()

            # Should return all sessions
            assert len(filtered) == 3
            assert filtered == self.test_sessions

    def test_create_display_with_filter(self) -> None:
        """Test creating display with search filter."""
        selector = SessionSelector(self.test_sessions)

        with patch.object(selector, "_get_session_details") as mock_get_details:
            mock_get_details.return_value = {
                "windows": 1,
                "window_names": "dev",
                "attached": True,
                "clients": 1,
            }

            # Filter for 'app'
            table, filtered = selector._create_display("app")

            # Should only return myapp session
            assert len(filtered) == 1
            assert filtered[0]["project"] == "myapp"

    @patch("libs.ui.session_selector.Prompt.ask")
    @patch("libs.ui.session_selector.Console")
    def test_select_session_quit(self, mock_console_class: MagicMock, mock_prompt: MagicMock) -> None:  # noqa: ARG002
        """Test quitting the selector."""
        mock_prompt.return_value = "q"

        selector = SessionSelector(self.test_sessions)
        result = selector.select_session()

        assert result is None

    @patch("libs.ui.session_selector.Prompt.ask")
    @patch("libs.ui.session_selector.Console")
    def test_select_session_valid_choice(self, mock_console_class: MagicMock, mock_prompt: MagicMock) -> None:  # noqa: ARG002
        """Test selecting a valid session."""
        mock_prompt.return_value = "2"  # Select second session

        selector = SessionSelector(self.test_sessions)
        with patch.object(selector, "_get_session_details") as mock_get_details:
            mock_get_details.return_value = {
                "windows": 1,
                "window_names": "",
                "attached": False,
                "clients": 0,
            }

            result = selector.select_session()

            assert result == "session2"


if __name__ == "__main__":
    unittest.main()
