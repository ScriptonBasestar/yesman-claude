import pytest
from pathlib import Path
from libs.dashboard import DashboardLauncher

class TestDashboardLaunch:
    """Tests for end-to-end dashboard launch process"""

    @pytest.fixture
    def temp_project_root(self):
        """Create temporary project directory"""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create tauri-dashboard directory with package.json
            tauri_dir = project_root / "tauri-dashboard"
            tauri_dir.mkdir()
            (tauri_dir / "package.json").write_text('{"name": "test-dashboard"}')
            
            yield project_root

    @pytest.fixture
    def launcher(self, temp_project_root):
        """Create DashboardLauncher with temp project root"""
        return DashboardLauncher(project_root=temp_project_root)

    def test_end_to_end_dashboard_launch(self, launcher, temp_project_root):
        """Test 6: End-to-end dashboard launch process"""
        # 1. Interface detection
        interface = launcher.detect_best_interface()
        assert interface in ['tui', 'web', 'tauri']
        
        # 2. Check dependencies
        requirements = launcher.check_system_requirements()
        assert interface in requirements
        
        # 3. Get interface info
        interface_info = launcher.get_interface_info(interface)
        assert interface_info is not None
        assert interface_info.name
        assert interface_info.description
        
        # 4. Verify interface can be created
        if interface == 'tui':
            # TUI should always work
            assert interface_info.available is True
        elif interface == 'tauri':
            # Tauri depends on directory structure
            expected_available = (temp_project_root / "tauri-dashboard").exists()
            assert interface_info.available == expected_available
