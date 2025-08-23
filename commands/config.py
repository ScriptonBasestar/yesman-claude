#!/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Configuration management commands."""

from pathlib import Path

import click

from libs.core.base_command import BaseCommand
from libs.core.config_validator import ConfigValidator


class ConfigCommand(BaseCommand):
    """Configuration management command."""
    
    def __init__(self) -> None:
        super().__init__()
        self.config_validator = ConfigValidator()
    
    def execute(
        self,
        action: str,
        file: str | None = None,
        verbose: bool = False,
        fix: bool = False,
        **kwargs
    ) -> None:
        """Execute configuration command.
        
        Args:
            action: The config action to perform ('validate')
            file: Specific configuration file to validate
            verbose: Show detailed information
            fix: Attempt to automatically fix issues
            **kwargs: Additional command arguments
        """
        if action == "validate":
            self._validate_config(file, verbose, fix)
        else:
            self.logger.error(f"Unknown config action: {action}")
            raise click.UsageError(f"Unknown action: {action}")
    
    def _validate_config(self, file: str | None, verbose: bool, fix: bool) -> None:
        """Validate configuration files."""
        self.logger.info("Starting configuration validation")
        
        try:
            if file:
                # Validate specific file
                file_path = Path(file).expanduser()
                result = self.config_validator.validate_file(file_path)
                click.echo(f"🔍 Validating configuration file: {file_path}")
            else:
                # Validate all configuration
                result = self.config_validator.validate_all()
                click.echo("🔍 Validating all Yesman configuration...")
            
            # Display results
            self.config_validator.display_results(result, verbose)
            
            # Auto-fix if requested
            if fix and (result.errors or result.warnings):
                click.echo("\n🔧 Attempting automatic fixes...")
                fixed_count = self.config_validator.auto_fix(result)
                
                if fixed_count > 0:
                    click.echo(f"✅ Automatically fixed {fixed_count} issues")
                    # Re-validate after fixes
                    if file:
                        file_path = Path(file).expanduser()
                        result = self.config_validator.validate_file(file_path)
                    else:
                        result = self.config_validator.validate_all()
                    
                    click.echo("\n📋 Post-fix validation results:")
                    self.config_validator.display_results(result, verbose)
                else:
                    click.echo("ℹ️  No issues could be automatically fixed")
            
            # Summary
            if result.is_valid:
                click.echo("\n✅ Configuration validation completed successfully!")
                self.logger.info("Configuration validation passed")
            else:
                click.echo(f"\n❌ Configuration validation found {len(result.errors)} errors")
                if not fix:
                    click.echo("💡 Use --fix to attempt automatic repairs")
                self.logger.warning(f"Configuration validation failed with {len(result.errors)} errors")
        
        except Exception as e:
            self.logger.exception("Configuration validation failed")
            click.echo(f"❌ Validation failed: {e}")
            raise click.ClickException(f"Configuration validation error: {e}")


@click.command()
@click.argument('action', type=click.Choice(['validate']))
@click.option('--file', '-f', help='Specific configuration file to validate')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation information')
@click.option('--fix', is_flag=True, help='Attempt to automatically fix issues')
def config_cli(action: str, file: str | None, verbose: bool, fix: bool) -> None:
    """Configuration management commands.
    
    Examples:
        yesman config validate                    # Validate all configuration
        yesman config validate --file config.yaml  # Validate specific file  
        yesman config validate --verbose           # Detailed validation output
        yesman config validate --fix               # Auto-fix issues
    """
    command = ConfigCommand()
    command.run(action=action, file=file, verbose=verbose, fix=fix)