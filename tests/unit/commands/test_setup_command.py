"""
Test for setup command
"""

import unittest
from unittest.mock import patch, MagicMock, call
from click.testing import CliRunner
from commands.setup import setup


class TestSetupCommand(unittest.TestCase):
    
    def setUp(self):
        self.runner = CliRunner()
    
    @patch('commands.setup.SessionManager')
    def test_setup_creates_all_sessions(self, mock_session_manager):
        """Test setup command creates all sessions from projects.yaml"""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_all_projects.return_value = [
            {"name": "project1", "template": "template1.yaml"},
            {"name": "project2", "template": "template2.yaml"}
        ]
        mock_manager_instance.create_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance
        
        # Run command
        result = self.runner.invoke(setup)
        
        # Assertions
        assert result.exit_code == 0
        assert mock_manager_instance.create_session.call_count == 2
        mock_manager_instance.create_session.assert_has_calls([
            call("project1"),
            call("project2")
        ], any_order=True)
    
    @patch('commands.setup.SessionManager')
    def test_setup_with_specific_project(self, mock_session_manager):
        """Test setup command with specific project name"""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance
        
        # Run command with project name
        result = self.runner.invoke(setup, ['--project', 'myproject'])
        
        # Assertions
        assert result.exit_code == 0
        mock_manager_instance.create_session.assert_called_once_with('myproject')
    
    @patch('commands.setup.SessionManager')
    def test_setup_handles_session_exists(self, mock_session_manager):
        """Test setup handles existing session gracefully"""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.side_effect = Exception("Session already exists")
        mock_session_manager.return_value = mock_manager_instance
        
        # Run command
        result = self.runner.invoke(setup, ['--project', 'existing'])
        
        # Should handle error
        assert result.exit_code != 0
        assert "already exists" in result.output or "Error" in result.output
    
    @patch('commands.setup.SessionManager')
    def test_setup_with_force_flag(self, mock_session_manager):
        """Test setup with --force flag recreates session"""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.create_session.return_value = True
        mock_manager_instance.kill_session.return_value = True
        mock_session_manager.return_value = mock_manager_instance
        
        # Run command with force flag
        result = self.runner.invoke(setup, ['--project', 'myproject', '--force'])
        
        # Assertions
        assert result.exit_code == 0
        mock_manager_instance.kill_session.assert_called_once_with('myproject')
        mock_manager_instance.create_session.assert_called_once_with('myproject')
    
    @patch('commands.setup.SessionManager')
    def test_setup_no_projects_found(self, mock_session_manager):
        """Test setup when no projects are configured"""
        # Setup mock
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_all_projects.return_value = []
        mock_session_manager.return_value = mock_manager_instance
        
        # Run command
        result = self.runner.invoke(setup)
        
        # Should show appropriate message
        assert result.exit_code == 0
        assert "No projects" in result.output or "Nothing to setup" in result.output


