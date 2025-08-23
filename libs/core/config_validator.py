#!/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Configuration validation service with detailed error reporting."""

import os
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .config_loader import ConfigLoader
from .config_schema import YesmanConfigSchema
from .error_handling import ErrorCategory, ErrorSeverity, YesmanError


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationError:
    """Represents a configuration validation error."""
    
    message: str
    level: ValidationLevel
    category: str
    file_path: str | None = None
    suggestion: str | None = None
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    """Results from configuration validation."""
    
    is_valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    info: list[ValidationError] = field(default_factory=list)
    
    def add_error(self, error: ValidationError) -> None:
        """Add a validation error and update validity status."""
        if error.level == ValidationLevel.ERROR or error.level == ValidationLevel.CRITICAL:
            self.errors.append(error)
            self.is_valid = False
        elif error.level == ValidationLevel.WARNING:
            self.warnings.append(error)
        else:
            self.info.append(error)
    
    @property
    def total_issues(self) -> int:
        """Total number of issues found."""
        return len(self.errors) + len(self.warnings) + len(self.info)


class ConfigValidator:
    """Service for validating Yesman configuration files."""
    
    def __init__(self) -> None:
        self.config_loader = ConfigLoader()
        self.console = Console()
    
    def validate_all(self) -> ValidationResult:
        """Validate all configuration files and dependencies."""
        result = ValidationResult()
        
        # Validate main configuration
        try:
            config = self.config_loader.load_config()
            self._validate_schema(config, result)
        except Exception as e:
            result.add_error(ValidationError(
                message=f"Failed to load configuration: {e}",
                level=ValidationLevel.CRITICAL,
                category="config_loading",
                suggestion="Check configuration file syntax and permissions"
            ))
            return result
        
        # Validate file existence and permissions
        self._validate_file_permissions(result)
        
        # Validate external dependencies
        self._validate_dependencies(result)
        
        # Validate configuration values
        self._validate_configuration_values(result)
        
        return result
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a specific configuration file."""
        result = ValidationResult()
        
        if not file_path.exists():
            result.add_error(ValidationError(
                message=f"Configuration file does not exist: {file_path}",
                level=ValidationLevel.ERROR,
                category="file_existence",
                file_path=str(file_path),
                suggestion="Create the configuration file or check the path"
            ))
            return result
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                result.add_error(ValidationError(
                    message=f"Configuration file is empty: {file_path}",
                    level=ValidationLevel.WARNING,
                    category="file_content",
                    file_path=str(file_path),
                    suggestion="Add configuration settings to the file"
                ))
                return result
            
            # Validate against schema
            YesmanConfigSchema(**config_data)
            
            result.add_error(ValidationError(
                message=f"Configuration file is valid: {file_path}",
                level=ValidationLevel.INFO,
                category="validation_success",
                file_path=str(file_path)
            ))
            
        except yaml.YAMLError as e:
            result.add_error(ValidationError(
                message=f"Invalid YAML syntax in {file_path}: {e}",
                level=ValidationLevel.ERROR,
                category="yaml_syntax",
                file_path=str(file_path),
                suggestion="Check YAML syntax and fix formatting errors"
            ))
        except PydanticValidationError as e:
            for error in e.errors():
                field_path = " → ".join(str(loc) for loc in error["loc"])
                result.add_error(ValidationError(
                    message=f"Invalid configuration in {file_path} at {field_path}: {error['msg']}",
                    level=ValidationLevel.ERROR,
                    category="schema_validation",
                    file_path=str(file_path),
                    suggestion="Check configuration value types and required fields"
                ))
        except Exception as e:
            result.add_error(ValidationError(
                message=f"Unexpected error validating {file_path}: {e}",
                level=ValidationLevel.ERROR,
                category="validation_error",
                file_path=str(file_path),
                suggestion="Check file permissions and content"
            ))
        
        return result
    
    def _validate_schema(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate configuration against Pydantic schema."""
        try:
            YesmanConfigSchema(**config)
            result.add_error(ValidationError(
                message="Configuration schema validation passed",
                level=ValidationLevel.INFO,
                category="schema_validation"
            ))
        except PydanticValidationError as e:
            for error in e.errors():
                field_path = " → ".join(str(loc) for loc in error["loc"])
                result.add_error(ValidationError(
                    message=f"Schema validation failed at {field_path}: {error['msg']}",
                    level=ValidationLevel.ERROR,
                    category="schema_validation",
                    suggestion="Check configuration field types and required values"
                ))
    
    def _validate_file_permissions(self, result: ValidationResult) -> None:
        """Validate file and directory permissions."""
        config_dirs = [
            Path("~/.scripton/yesman").expanduser(),
            Path("./.scripton/yesman").expanduser() if Path("./.scripton").exists() else None
        ]
        
        for config_dir in config_dirs:
            if config_dir is None:
                continue
                
            if config_dir.exists():
                if not config_dir.is_dir():
                    result.add_error(ValidationError(
                        message=f"Configuration path exists but is not a directory: {config_dir}",
                        level=ValidationLevel.ERROR,
                        category="file_permissions",
                        suggestion=f"Remove the file and create directory: rm {config_dir} && mkdir -p {config_dir}"
                    ))
                elif not os.access(config_dir, os.R_OK | os.W_OK):
                    result.add_error(ValidationError(
                        message=f"Insufficient permissions for configuration directory: {config_dir}",
                        level=ValidationLevel.WARNING,
                        category="file_permissions",
                        suggestion=f"Fix permissions: chmod 755 {config_dir}",
                        auto_fixable=True
                    ))
                else:
                    result.add_error(ValidationError(
                        message=f"Configuration directory permissions OK: {config_dir}",
                        level=ValidationLevel.INFO,
                        category="file_permissions"
                    ))
    
    def _validate_dependencies(self, result: ValidationResult) -> None:
        """Validate external tool dependencies."""
        dependencies = {
            "tmux": "brew install tmux (macOS) or apt install tmux (Ubuntu)",
            "git": "install git from https://git-scm.com/downloads",
        }
        
        for tool, install_hint in dependencies.items():
            if shutil.which(tool):
                result.add_error(ValidationError(
                    message=f"Dependency found: {tool}",
                    level=ValidationLevel.INFO,
                    category="dependencies"
                ))
            else:
                level = ValidationLevel.CRITICAL if tool == "tmux" else ValidationLevel.WARNING
                result.add_error(ValidationError(
                    message=f"Required dependency not found: {tool}",
                    level=level,
                    category="dependencies",
                    suggestion=install_hint
                ))
    
    def _validate_configuration_values(self, result: ValidationResult) -> None:
        """Validate configuration value constraints."""
        try:
            config = self.config_loader.load_config()
            
            # Example validations - extend as needed
            if "tmux" in config:
                tmux_config = config["tmux"]
                
                # Check default shell exists
                if "default_shell" in tmux_config:
                    shell_path = Path(tmux_config["default_shell"])
                    if not shell_path.exists():
                        result.add_error(ValidationError(
                            message=f"Default shell not found: {shell_path}",
                            level=ValidationLevel.WARNING,
                            category="configuration_values",
                            suggestion="Use a valid shell path like /bin/bash or /bin/zsh"
                        ))
                    else:
                        result.add_error(ValidationError(
                            message=f"Default shell is valid: {shell_path}",
                            level=ValidationLevel.INFO,
                            category="configuration_values"
                        ))
        except Exception as e:
            result.add_error(ValidationError(
                message=f"Error validating configuration values: {e}",
                level=ValidationLevel.WARNING,
                category="configuration_values"
            ))
    
    def display_results(self, result: ValidationResult, verbose: bool = False) -> None:
        """Display validation results with Rich formatting."""
        if result.is_valid and not result.warnings and not verbose:
            self.console.print("✅ All configuration validation passed", style="green bold")
            return
        
        # Summary
        if result.is_valid:
            self.console.print("✅ Configuration is valid", style="green bold")
        else:
            self.console.print("❌ Configuration has issues", style="red bold")
        
        self.console.print()
        
        # Create summary table
        table = Table(title="Validation Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Count", justify="right", style="magenta")
        
        if result.errors:
            table.add_row("Errors", "❌", str(len(result.errors)), style="red")
        if result.warnings:
            table.add_row("Warnings", "⚠️", str(len(result.warnings)), style="yellow")
        if verbose and result.info:
            table.add_row("Info", "ℹ️", str(len(result.info)), style="blue")
        
        self.console.print(table)
        self.console.print()
        
        # Detailed issues
        for error in result.errors:
            self.console.print(f"❌ {error.message}", style="red")
            if error.suggestion:
                self.console.print(f"   💡 {error.suggestion}", style="yellow")
            self.console.print()
        
        for warning in result.warnings:
            self.console.print(f"⚠️  {warning.message}", style="yellow")
            if warning.suggestion:
                self.console.print(f"   💡 {warning.suggestion}", style="cyan")
            self.console.print()
        
        if verbose:
            for info in result.info:
                self.console.print(f"ℹ️  {info.message}", style="blue")
                self.console.print()
    
    def auto_fix(self, result: ValidationResult) -> int:
        """Attempt to automatically fix fixable issues."""
        fixed_count = 0
        
        for error in result.errors + result.warnings:
            if not error.auto_fixable:
                continue
                
            try:
                if "permissions" in error.category and error.file_path:
                    # Fix directory permissions
                    import os
                    os.chmod(error.file_path, 0o755)
                    fixed_count += 1
                    self.console.print(f"✅ Fixed permissions for: {error.file_path}", style="green")
            except Exception as e:
                self.console.print(f"❌ Failed to fix {error.message}: {e}", style="red")
        
        return fixed_count