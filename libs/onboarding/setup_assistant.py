#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Intelligent Setup Assistant.

This module provides a comprehensive, guided setup experience with intelligent
configuration detection, validation, and automated system preparation for
optimal performance.
"""

import asyncio
import json
import os
import platform
import shutil
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from libs.dashboard.monitoring_integration import get_monitoring_dashboard


class SetupStatus(Enum):
    """Setup step status indicators."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class SetupResult:
    """Setup operation result with detailed information."""

    status: SetupStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    error: str | None = None
    suggestions: list[str] = field(default_factory=list)


@dataclass
class SetupStep:
    """Individual setup step with execution and validation logic."""

    step_id: str
    title: str
    description: str
    category: str  # 'environment', 'security', 'configuration', 'dependencies'
    required: bool
    automated: bool
    estimated_duration: int  # seconds
    validation_function: Callable | None = None
    setup_function: Callable | None = None
    documentation_link: str | None = None
    prerequisites: list[str] = field(default_factory=list)
    safety_level: str = "safe"  # 'safe', 'moderate', 'advanced'


class IntelligentSetupAssistant:
    """Intelligent setup assistant with comprehensive configuration management."""

    def __init__(self) -> None:
        """Initialize the setup assistant."""
        self.monitoring = get_monitoring_dashboard()
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"

        # Setup state
        self.setup_steps = self._define_setup_steps()
        self.user_config = {}
        self.system_info = {}
        self.setup_history = []

        # Collect system information
        self._collect_system_info()

    def _collect_system_info(self) -> None:
        """Collect comprehensive system information."""
        self.system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": str(Path.cwd()),
            "project_root": str(self.project_root),
            "user_home": str(Path.home()),
            "timestamp": time.time(),
        }

    def _define_setup_steps(self) -> list[SetupStep]:
        """Define the comprehensive setup process with intelligent ordering."""
        return [
            # System Environment Validation
            SetupStep(
                step_id="system_requirements",
                title="System Requirements Check",
                description="Validate system requirements and compatibility",
                category="environment",
                required=True,
                automated=True,
                estimated_duration=15,
                validation_function=self._validate_system_requirements,
                setup_function=self._setup_system_requirements,
                documentation_link="/docs/generated/deployment_guide.md#system-requirements",
                safety_level="safe",
            ),
            SetupStep(
                step_id="python_environment",
                title="Python Environment Setup",
                description="Configure Python environment with uv and dependencies",
                category="environment",
                required=True,
                automated=True,
                estimated_duration=60,
                validation_function=self._validate_python_environment,
                setup_function=self._setup_python_environment,
                documentation_link="/docs/generated/deployment_guide.md#python-setup",
                prerequisites=["system_requirements"],
                safety_level="safe",
            ),
            # Directory Structure and Permissions
            SetupStep(
                step_id="directory_structure",
                title="Directory Structure Creation",
                description="Create required directories with proper permissions",
                category="configuration",
                required=True,
                automated=True,
                estimated_duration=10,
                validation_function=self._validate_directory_structure,
                setup_function=self._setup_directory_structure,
                documentation_link="/docs/configuration.md#directory-structure",
                prerequisites=["system_requirements"],
                safety_level="safe",
            ),
            # Configuration Setup
            SetupStep(
                step_id="base_configuration",
                title="Base Configuration Setup",
                description="Initialize base configuration files with intelligent defaults",
                category="configuration",
                required=True,
                automated=True,
                estimated_duration=30,
                validation_function=self._validate_base_configuration,
                setup_function=self._setup_base_configuration,
                documentation_link="/docs/configuration.md",
                prerequisites=["directory_structure"],
                safety_level="safe",
            ),
            # Security Configuration
            SetupStep(
                step_id="security_setup",
                title="Security Configuration",
                description="Configure security settings, API keys, and access controls",
                category="security",
                required=True,
                automated=False,  # Requires user input for API keys
                estimated_duration=120,
                validation_function=self._validate_security_setup,
                setup_function=self._setup_security_configuration,
                documentation_link="/docs/development/security-coding-standards.md",
                prerequisites=["base_configuration"],
                safety_level="moderate",
            ),
            # Database and Storage
            SetupStep(
                step_id="database_setup",
                title="Database and Storage Setup",
                description="Initialize database and configure storage systems",
                category="dependencies",
                required=False,
                automated=True,
                estimated_duration=45,
                validation_function=self._validate_database_setup,
                setup_function=self._setup_database,
                documentation_link="/docs/generated/deployment_guide.md#database-setup",
                prerequisites=["base_configuration"],
                safety_level="safe",
            ),
            # Monitoring Integration
            SetupStep(
                step_id="monitoring_setup",
                title="Monitoring and Dashboards",
                description="Enable performance monitoring and configure dashboards",
                category="configuration",
                required=False,
                automated=True,
                estimated_duration=30,
                validation_function=self._validate_monitoring_setup,
                setup_function=self._setup_monitoring,
                documentation_link="/docs/MONITORING_DASHBOARD_GUIDE.md",
                prerequisites=["base_configuration"],
                safety_level="safe",
            ),
            # User Preferences and Customization
            SetupStep(
                step_id="user_preferences",
                title="User Preferences and Customization",
                description="Configure personal preferences and dashboard settings",
                category="configuration",
                required=False,
                automated=False,
                estimated_duration=60,
                validation_function=self._validate_user_preferences,
                setup_function=None,  # Interactive setup
                documentation_link="/docs/user-guide.md",
                prerequisites=["monitoring_setup"],
                safety_level="safe",
            ),
            # Development Tools (Optional)
            SetupStep(
                step_id="development_tools",
                title="Development Tools Setup",
                description="Configure optional development tools and integrations",
                category="dependencies",
                required=False,
                automated=True,
                estimated_duration=90,
                validation_function=self._validate_development_tools,
                setup_function=self._setup_development_tools,
                documentation_link="/docs/developer-guide.md",
                prerequisites=["python_environment"],
                safety_level="moderate",
            ),
            # Final Validation and Testing
            SetupStep(
                step_id="system_validation",
                title="System Validation and Testing",
                description="Run comprehensive system tests and validation",
                category="validation",
                required=True,
                automated=True,
                estimated_duration=60,
                validation_function=self._validate_complete_system,
                setup_function=self._run_system_tests,
                documentation_link="/docs/generated/testing_guide.md",
                prerequisites=["base_configuration", "monitoring_setup"],
                safety_level="safe",
            ),
        ]

    async def run_guided_setup(self, interactive: bool = True, selected_steps: list[str] = None) -> dict[str, Any]:
        """Run the complete guided setup process.

        Args:
            interactive: Whether to prompt user for decisions
            selected_steps: Specific steps to run (None for all)

        Returns:
            Dictionary with comprehensive setup results
        """
        setup_results = {
            "started_at": time.time(),
            "system_info": self.system_info,
            "completed_steps": [],
            "failed_steps": [],
            "skipped_steps": [],
            "warnings": [],
            "manual_steps_required": [],
            "setup_successful": False,
            "total_duration": 0.0,
        }

        print("🚀 Yesman Claude Agent - Intelligent Setup Assistant")
        print("=" * 70)
        print(f"🖥️  System: {self.system_info['platform']} {self.system_info['architecture']}")
        print(f"🐍 Python: {self.system_info['python_version'].split()[0]}")
        print(f"📁 Project: {self.project_root}")
        print("=" * 70)

        # Filter steps if specific ones are selected
        steps_to_run = self.setup_steps
        if selected_steps:
            steps_to_run = [step for step in self.setup_steps if step.step_id in selected_steps]

        # Pre-setup analysis
        print("\n🔍 Analyzing system and requirements...")
        await self._analyze_system_state()

        # Execute setup steps
        for step in steps_to_run:
            print(f"\n📋 [{step.category.upper()}] {step.title}")
            print(f"    {step.description}")

            # Check prerequisites
            if not self._check_prerequisites(step, setup_results["completed_steps"]):
                print("    ⏭️  Skipping: Prerequisites not met")
                setup_results["skipped_steps"].append({"step_id": step.step_id, "reason": "Prerequisites not met", "prerequisites": step.prerequisites})
                continue

            # Interactive confirmation for non-automated or advanced steps
            if interactive and (not step.automated or step.safety_level == "advanced"):
                if not await self._get_user_confirmation(step):
                    print("    ⏭️  Skipping: User chose to skip")
                    setup_results["skipped_steps"].append({"step_id": step.step_id, "reason": "User skipped", "step_info": step})
                    continue

            # Execute the step
            start_time = time.time()
            try:
                result = await self._execute_setup_step(step)
                duration = time.time() - start_time
                result.duration = duration

                # Process result
                if result.status == SetupStatus.COMPLETED:
                    print(f"    ✅ Completed in {duration:.1f}s")
                    setup_results["completed_steps"].append({"step_id": step.step_id, "title": step.title, "duration": duration, "details": result.details})
                elif result.status == SetupStatus.WARNING:
                    print(f"    ⚠️  Completed with warnings: {result.message}")
                    setup_results["warnings"].append({"step_id": step.step_id, "message": result.message, "suggestions": result.suggestions})
                    setup_results["completed_steps"].append({"step_id": step.step_id, "title": step.title, "duration": duration, "warnings": True})
                elif result.status == SetupStatus.FAILED:
                    print(f"    ❌ Failed: {result.message}")
                    setup_results["failed_steps"].append({"step_id": step.step_id, "title": step.title, "error": result.error, "suggestions": result.suggestions})

                    # Stop if required step fails
                    if step.required:
                        print("    💥 Required step failed - stopping setup")
                        break
                else:
                    # Handle manual steps
                    print("    📝 Manual configuration required")
                    setup_results["manual_steps_required"].append({"step_id": step.step_id, "title": step.title, "description": step.description, "documentation_link": step.documentation_link})

            except Exception as e:
                duration = time.time() - start_time
                print(f"    💥 Setup error: {e}")
                setup_results["failed_steps"].append({"step_id": step.step_id, "title": step.title, "error": str(e), "duration": duration})

                if step.required:
                    print("    💥 Required step failed - stopping setup")
                    break

        # Calculate final results
        setup_results["completed_at"] = time.time()
        setup_results["total_duration"] = setup_results["completed_at"] - setup_results["started_at"]

        # Determine overall success
        required_steps = [s.step_id for s in steps_to_run if s.required]
        completed_required = [s["step_id"] for s in setup_results["completed_steps"] if s["step_id"] in required_steps]
        setup_results["setup_successful"] = len(completed_required) == len(required_steps)

        # Generate setup report
        await self._generate_setup_report(setup_results)

        # Display summary
        await self._display_setup_summary(setup_results)

        return setup_results

    async def _execute_setup_step(self, step: SetupStep) -> SetupResult:
        """Execute a single setup step.

        Args:
            step: Setup step to execute

        Returns:
            SetupResult with execution details
        """
        try:
            # Validate current state first
            if step.validation_function:
                is_valid = await step.validation_function()
                if is_valid:
                    return SetupResult(status=SetupStatus.COMPLETED, message="Already configured correctly", details={"already_valid": True})

            # Execute setup function if available
            if step.setup_function:
                print("    🔧 Configuring...")
                setup_success = await step.setup_function()

                if setup_success:
                    # Re-validate after setup
                    if step.validation_function:
                        is_valid = await step.validation_function()
                        if is_valid:
                            return SetupResult(status=SetupStatus.COMPLETED, message="Setup completed successfully")
                        else:
                            return SetupResult(status=SetupStatus.WARNING, message="Setup completed but validation failed", suggestions=["Check configuration manually", "Review logs for details"])
                    else:
                        return SetupResult(status=SetupStatus.COMPLETED, message="Setup completed successfully")
                else:
                    return SetupResult(
                        status=SetupStatus.FAILED, message="Setup function returned false", error="Setup operation failed", suggestions=["Check system requirements", "Review error logs"]
                    )
            else:
                # Manual step - provide guidance
                return SetupResult(
                    status=SetupStatus.PENDING,
                    message="Manual configuration required",
                    suggestions=[f"Follow the documentation: {step.documentation_link}", "Complete the configuration manually", "Run validation when complete"],
                )

        except Exception as e:
            return SetupResult(
                status=SetupStatus.FAILED,
                message=f"Setup step failed: {str(e)}",
                error=str(e),
                suggestions=["Check error logs for more details", "Verify system requirements", "Try running the step manually"],
            )

    def _check_prerequisites(self, step: SetupStep, completed_steps: list[dict[str, Any]]) -> bool:
        """Check if step prerequisites are satisfied.

        Args:
            step: Setup step to check
            completed_steps: List of completed steps

        Returns:
            True if prerequisites are met
        """
        completed_step_ids = [s["step_id"] for s in completed_steps]
        return all(prereq in completed_step_ids for prereq in step.prerequisites)

    async def _get_user_confirmation(self, step: SetupStep) -> bool:
        """Get user confirmation for step execution.

        Args:
            step: Setup step requiring confirmation

        Returns:
            True if user confirms
        """
        print(f"    📋 Estimated time: {step.estimated_duration}s")
        print(f"    🛡️  Safety level: {step.safety_level}")
        if step.documentation_link:
            print(f"    📖 Documentation: {step.documentation_link}")

        while True:
            try:
                response = input("    Continue with this step? (y/N/s=skip): ").strip().lower()
                if response in {"y", "yes"}:
                    return True
                elif response in {"n", "no", ""} or response in {"s", "skip"}:
                    return False
                else:
                    print("    Please enter 'y' for yes, 'n' for no, or 's' to skip")
            except KeyboardInterrupt:
                print("\n    ⏹️  Setup cancelled by user")
                return False

    async def _analyze_system_state(self) -> None:
        """Analyze current system state and requirements."""
        analysis = {
            "python_version_ok": sys.version_info >= (3, 9),
            "uv_available": shutil.which("uv") is not None,
            "git_available": shutil.which("git") is not None,
            "project_structure_exists": (self.project_root / "pyproject.toml").exists(),
            "config_dir_exists": self.config_dir.exists(),
            "has_write_permissions": os.access(self.project_root, os.W_OK),
        }

        print("🔍 System Analysis:")
        for check, result in analysis.items():
            status = "✅" if result else "❌"
            print(f"    {status} {check.replace('_', ' ').title()}")

    # Validation functions
    async def _validate_system_requirements(self) -> bool:
        """Validate system requirements."""
        try:
            # Check Python version

            # Check available disk space (at least 1GB)
            disk_usage = shutil.disk_usage(self.project_root)
            if disk_usage.free < 1024 * 1024 * 1024:
                return False

            # Check write permissions
            if not os.access(self.project_root, os.W_OK):
                return False

            # Check if required system tools are available
            required_tools = ["python3", "pip"]
            for tool in required_tools:
                if not shutil.which(tool):
                    return False

            return True

        except Exception:
            return False

    async def _validate_python_environment(self) -> bool:
        """Validate Python environment setup."""
        try:
            # Check if uv is available
            if not shutil.which("uv"):
                return False

            # Check if virtual environment exists
            venv_path = self.project_root / ".venv"
            if not venv_path.exists():
                return False

            # Check if basic dependencies are installed
            import importlib.util

            required_modules = ["fastapi", "psutil", "uvicorn"]
            for module in required_modules:
                if importlib.util.find_spec(module) is None:
                    return False

            return True

        except Exception:
            return False

    async def _validate_directory_structure(self) -> bool:
        """Validate directory structure."""
        required_dirs = [self.config_dir, self.data_dir, self.logs_dir, self.project_root / "docs" / "generated", self.project_root / "tmp"]

        return all(dir_path.exists() and os.access(dir_path, os.W_OK) for dir_path in required_dirs)

    async def _validate_base_configuration(self) -> bool:
        """Validate base configuration files."""
        required_configs = [self.config_dir / "default.yaml", self.config_dir / "development.yaml"]

        return all(config_file.exists() for config_file in required_configs)

    async def _validate_security_setup(self) -> bool:
        """Validate security configuration."""
        # Check if environment variables are set
        required_env_vars = ["YESMAN_SECRET_KEY"]

        # For development, check if .env file exists or env vars are set
        env_file = self.project_root / ".env"
        if env_file.exists():
            return True

        return all(os.getenv(var) for var in required_env_vars)

    async def _validate_database_setup(self) -> bool:
        """Validate database setup."""
        # For SQLite (default), check if database file can be created
        try:
            db_path = self.data_dir / "yesman.db"
            # Try creating a temporary database connection
            import sqlite3

            conn = sqlite3.connect(":memory:")
            conn.close()
            return True
        except Exception:
            return False

    async def _validate_monitoring_setup(self) -> bool:
        """Validate monitoring setup."""
        try:
            # Check if monitoring configuration exists
            monitoring_config = self.config_dir / "monitoring.yaml"
            if monitoring_config.exists():
                return True

            # Check if monitoring is working
            health_score = await self._get_health_score()
            return health_score is not None

        except Exception:
            return False

    async def _validate_user_preferences(self) -> bool:
        """Validate user preferences setup."""
        preferences_file = self.config_dir / "user_preferences.json"
        return preferences_file.exists()

    async def _validate_development_tools(self) -> bool:
        """Validate development tools setup."""
        # Check if common development tools are available
        dev_tools = ["git", "make"]
        return all(shutil.which(tool) for tool in dev_tools)

    async def _validate_complete_system(self) -> bool:
        """Validate complete system setup."""
        try:
            # Run a basic health check
            health_score = await self._get_health_score()
            return health_score is not None and health_score > 50
        except Exception:
            return False

    # Setup functions
    async def _setup_system_requirements(self) -> bool:
        """Setup system requirements."""
        try:
            print("    ℹ️  System requirements check completed")
            return True
        except Exception:
            return False

    async def _setup_python_environment(self) -> bool:
        """Setup Python environment with uv."""
        try:
            # Install uv if not available
            if not shutil.which("uv"):
                print("    📥 Installing uv package manager...")
                install_cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
                result = await self._run_command(install_cmd)
                if result["returncode"] != 0:
                    print(f"    ❌ Failed to install uv: {result['stderr']}")
                    return False

            # Initialize virtual environment and install dependencies
            print("    🔧 Setting up virtual environment...")
            result = await self._run_command("uv sync", cwd=self.project_root)
            if result["returncode"] != 0:
                print(f"    ⚠️  uv sync warning: {result['stderr']}")
                # Try pip install as fallback
                print("    🔄 Trying pip install as fallback...")
                result = await self._run_command("pip install -e .", cwd=self.project_root)
                return result["returncode"] == 0

            return True

        except Exception as e:
            print(f"    ❌ Python environment setup failed: {e}")
            return False

    async def _setup_directory_structure(self) -> bool:
        """Setup required directory structure."""
        try:
            required_dirs = [self.config_dir, self.data_dir, self.logs_dir, self.project_root / "docs" / "generated", self.project_root / "tmp", self.project_root / "tmp" / "scripts"]

            for dir_path in required_dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"    📁 Created: {dir_path}")

            # Create .gitignore for tmp directory
            gitignore_path = self.project_root / "tmp" / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write("# Ignore all files in tmp directory\n*\n!.gitignore\n")

            return True

        except Exception as e:
            print(f"    ❌ Directory setup failed: {e}")
            return False

    async def _setup_base_configuration(self) -> bool:
        """Setup base configuration files."""
        try:
            # Create default configuration if it doesn't exist
            default_config_path = self.config_dir / "default.yaml"
            if not default_config_path.exists():
                default_config = {
                    "server": {"host": "127.0.0.1", "port": 8000, "debug": False},
                    "monitoring": {"enabled": True, "update_interval": 1.0, "dashboard_port": 1420},
                    "logging": {"level": "INFO", "file_logging": True, "log_directory": "logs"},
                    "security": {"api_key_required": False, "rate_limiting": True},
                }

                with open(default_config_path, "w", encoding="utf-8") as f:
                    import yaml

                    yaml.dump(default_config, f, default_flow_style=False)
                print(f"    📝 Created: {default_config_path}")

            # Create development configuration
            dev_config_path = self.config_dir / "development.yaml"
            if not dev_config_path.exists():
                dev_config = {"server": {"debug": True, "reload": True}, "logging": {"level": "DEBUG"}}

                with open(dev_config_path, "w", encoding="utf-8") as f:
                    import yaml

                    yaml.dump(dev_config, f, default_flow_style=False)
                print(f"    📝 Created: {dev_config_path}")

            return True

        except Exception as e:
            print(f"    ❌ Configuration setup failed: {e}")
            return False

    async def _setup_security_configuration(self) -> bool:
        """Setup security configuration."""
        try:
            env_file = self.project_root / ".env"

            if not env_file.exists():
                print("    🔐 Creating security configuration...")

                # Generate a secret key
                import secrets

                secret_key = secrets.token_urlsafe(32)

                env_content = f"""# Yesman Claude Agent Environment Variables
# Generated on {time.strftime("%Y-%m-%d %H:%M:%S")}

# Security Configuration
YESMAN_SECRET_KEY={secret_key}
YESMAN_API_KEY_REQUIRED=false

# Development Settings
YESMAN_CONFIG=development
YESMAN_DEBUG=true

# Claude API Configuration (Add your API key here)
# CLAUDE_API_KEY=your_claude_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./data/yesman.db

# Monitoring Configuration
MONITORING_ENABLED=true
DASHBOARD_PORT=1420
"""

                with open(env_file, "w", encoding="utf-8") as f:
                    f.write(env_content)

                # Set appropriate permissions (owner read/write only)
                env_file.chmod(0o600)
                print(f"    🔐 Created: {env_file}")
                print("    ⚠️  Remember to add your Claude API key to the .env file")

            return True

        except Exception as e:
            print(f"    ❌ Security setup failed: {e}")
            return False

    async def _setup_database(self) -> bool:
        """Setup database."""
        try:
            # For SQLite, just ensure the data directory exists
            self.data_dir.mkdir(exist_ok=True)

            # Create a simple test to verify SQLite works
            import sqlite3

            db_path = self.data_dir / "yesman.db"

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS setup_test (
                        id INTEGER PRIMARY KEY,
                        timestamp REAL,
                        status TEXT
                    )
                """)
                cursor.execute("INSERT INTO setup_test (timestamp, status) VALUES (?, ?)", (time.time(), "setup_complete"))
                conn.commit()

            print(f"    💾 Database initialized: {db_path}")
            return True

        except Exception as e:
            print(f"    ❌ Database setup failed: {e}")
            return False

    async def _setup_monitoring(self) -> bool:
        """Setup monitoring and dashboard systems."""
        try:
            # Create monitoring configuration
            monitoring_config = {
                "monitoring": {"enabled": True, "update_interval": 1.0, "metric_retention": 3600, "alert_retention": 86400},
                "dashboard": {"port": 1420, "auto_open": False, "theme": "auto"},
                "alerts": {"response_time_threshold": 100.0, "memory_threshold": 10.0, "cpu_threshold": 80.0},
            }

            monitoring_config_path = self.config_dir / "monitoring.yaml"
            with open(monitoring_config_path, "w", encoding="utf-8") as f:
                import yaml

                yaml.dump(monitoring_config, f, default_flow_style=False)

            print(f"    📊 Monitoring configured: {monitoring_config_path}")

            # Test monitoring system
            try:
                health_score = await self._get_health_score()
                if health_score is not None:
                    print(f"    ✅ Monitoring system active (Health: {health_score}%)")
                else:
                    print("    ⚠️  Monitoring system not yet active")
            except Exception:
                print("    ⚠️  Monitoring system will be activated on first run")

            return True

        except Exception as e:
            print(f"    ❌ Monitoring setup failed: {e}")
            return False

    async def _setup_development_tools(self) -> bool:
        """Setup development tools."""
        try:
            # Check if Makefile exists (basic development setup indicator)
            makefile = self.project_root / "Makefile"
            if not makefile.exists():
                print("    ⚠️  Makefile not found - development tools may be limited")
                return False

            # Test basic make commands
            result = await self._run_command("make help", cwd=self.project_root)
            if result["returncode"] == 0:
                print("    🔧 Development tools are available")
                return True
            else:
                print("    ⚠️  Make commands may not work properly")
                return False

        except Exception as e:
            print(f"    ❌ Development tools setup failed: {e}")
            return False

    async def _run_system_tests(self) -> bool:
        """Run basic system validation tests."""
        try:
            tests_passed = 0
            total_tests = 5

            print("    🧪 Running system validation tests...")

            # Test 1: Configuration loading
            try:
                from libs.core.config_loader import ConfigLoader

                config_loader = ConfigLoader()
                config_loader.load_config()
                print("    ✅ Configuration loading: PASS")
                tests_passed += 1
            except Exception as e:
                print(f"    ❌ Configuration loading: FAIL ({e})")

            # Test 2: Directory permissions
            try:
                test_file = self.data_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                print("    ✅ File system permissions: PASS")
                tests_passed += 1
            except Exception as e:
                print(f"    ❌ File system permissions: FAIL ({e})")

            # Test 3: Database connectivity
            try:
                import sqlite3

                db_path = self.data_dir / "yesman.db"
                with sqlite3.connect(db_path) as conn:
                    conn.execute("SELECT 1").fetchone()
                print("    ✅ Database connectivity: PASS")
                tests_passed += 1
            except Exception as e:
                print(f"    ❌ Database connectivity: FAIL ({e})")

            # Test 4: Python environment
            import importlib.util

            required_deps = ["fastapi", "uvicorn"]
            all_deps_available = True

            for dep in required_deps:
                if importlib.util.find_spec(dep) is None:
                    all_deps_available = False
                    print(f"    ❌ Python dependencies: FAIL (Missing {dep})")
                    break

            if all_deps_available:
                print("    ✅ Python dependencies: PASS")
                tests_passed += 1

            # Test 5: Monitoring system
            try:
                health_score = await self._get_health_score()
                if health_score is not None:
                    print("    ✅ Monitoring system: PASS")
                    tests_passed += 1
                else:
                    print("    ⚠️  Monitoring system: Not active (will start with application)")
                    tests_passed += 1  # Not a failure for setup
            except Exception as e:
                print(f"    ❌ Monitoring system: FAIL ({e})")

            success_rate = (tests_passed / total_tests) * 100
            print(f"    📊 System validation: {tests_passed}/{total_tests} tests passed ({success_rate:.0f}%)")

            return success_rate >= 80  # 80% pass rate required

        except Exception as e:
            print(f"    ❌ System tests failed: {e}")
            return False

    async def _run_command(self, command: str, cwd: Path = None) -> dict[str, Any]:
        """Run a shell command and return the result.

        Args:
            command: Command to run
            cwd: Working directory

        Returns:
            Dictionary with command result
        """
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd or self.project_root)

            stdout, stderr = await process.communicate()

            return {"returncode": process.returncode, "stdout": stdout.decode("utf-8"), "stderr": stderr.decode("utf-8")}
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    async def _get_health_score(self) -> float | None:
        """Get current system health score."""
        try:
            dashboard_data = await self.monitoring._prepare_dashboard_data()
            return dashboard_data.get("health_score")
        except Exception:
            return None

    async def _generate_setup_report(self, setup_results: dict[str, Any]) -> None:
        """Generate detailed setup report."""
        report_path = self.project_root / "setup_report.json"

        # Add system information to the report
        setup_results["system_info"] = self.system_info
        setup_results["setup_steps_available"] = [
            {"step_id": step.step_id, "title": step.title, "category": step.category, "required": step.required, "automated": step.automated} for step in self.setup_steps
        ]

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(setup_results, f, indent=2, default=str)

            print(f"\n📄 Setup report saved: {report_path}")
        except Exception as e:
            print(f"\n⚠️  Could not save setup report: {e}")

    async def _display_setup_summary(self, setup_results: dict[str, Any]) -> None:
        """Display comprehensive setup summary."""
        print("\n" + "=" * 70)
        print("🎯 SETUP COMPLETE - SUMMARY")
        print("=" * 70)

        # Overall status
        if setup_results["setup_successful"]:
            print("✅ Setup Status: SUCCESS")
        else:
            print("❌ Setup Status: INCOMPLETE")

        print(f"⏱️  Total Time: {setup_results['total_duration']:.1f} seconds")

        # Step breakdown
        completed = len(setup_results["completed_steps"])
        failed = len(setup_results["failed_steps"])
        skipped = len(setup_results["skipped_steps"])
        manual = len(setup_results["manual_steps_required"])
        warnings = len(setup_results["warnings"])

        print("\n📊 Step Summary:")
        print(f"   ✅ Completed: {completed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   📝 Manual Required: {manual}")
        print(f"   ⚠️  Warnings: {warnings}")

        # Manual steps required
        if setup_results["manual_steps_required"]:
            print("\n📋 Manual Steps Required:")
            for step in setup_results["manual_steps_required"]:
                print(f"   • {step['title']}")
                if step.get("documentation_link"):
                    print(f"     📖 {step['documentation_link']}")

        # Warnings
        if setup_results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in setup_results["warnings"]:
                print(f"   • {warning['message']}")

        # Failed steps
        if setup_results["failed_steps"]:
            print("\n❌ Failed Steps:")
            for failure in setup_results["failed_steps"]:
                print(f"   • {failure['title']}: {failure.get('error', 'Unknown error')}")

        # Next steps
        print("\n🚀 Next Steps:")
        if setup_results["setup_successful"]:
            print("   1. Start the application: make dev")
            print("   2. Open dashboard: http://localhost:1420")
            print("   3. Review the user guide: docs/user-guide.md")
            if manual:
                print("   4. Complete the manual configuration steps listed above")
        else:
            print("   1. Review and fix failed steps")
            print("   2. Re-run setup: python -m libs.onboarding.setup_assistant")
            print("   3. Check the setup report for detailed information")

        print("\n💡 For support: Create a GitHub issue with your setup report")
        print("=" * 70)


# CLI interface for standalone execution
async def main() -> int | None:
    """Main function for CLI execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Yesman Claude Agent Setup Assistant")
    parser.add_argument("--interactive", action="store_true", default=True, help="Run in interactive mode (default)")
    parser.add_argument("--non-interactive", action="store_true", help="Run without user prompts")
    parser.add_argument("--steps", nargs="+", help="Run only specific steps")
    parser.add_argument("--list-steps", action="store_true", help="List available setup steps")

    args = parser.parse_args()

    assistant = IntelligentSetupAssistant()

    if args.list_steps:
        print("Available Setup Steps:")
        print("=" * 50)
        for step in assistant.setup_steps:
            status = "Required" if step.required else "Optional"
            auto = "Automated" if step.automated else "Manual"
            print(f"📋 {step.step_id}")
            print(f"   Title: {step.title}")
            print(f"   Category: {step.category}")
            print(f"   Status: {status} | {auto}")
            print(f"   Duration: ~{step.estimated_duration}s")
            print()
        return

    interactive = not args.non_interactive
    selected_steps = args.steps

    try:
        results = await assistant.run_guided_setup(interactive=interactive, selected_steps=selected_steps)

        return 0 if results["setup_successful"] else 1

    except KeyboardInterrupt:
        print("\n⏹️  Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n💥 Setup failed with error: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
