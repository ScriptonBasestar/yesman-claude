#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Security validation script for pre-commit hooks.

This script performs additional security checks that complement
the standard bandit and safety tools.
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class SecurityValidator:
    """Security validation checks for code quality."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Security patterns to detect
        self.dangerous_patterns = {
            'hardcoded_secrets': [
                r'(?i)(password|secret|key|token)\s*=\s*["\'][^"\']{8,}["\']',
                r'(?i)api[_-]?key\s*=\s*["\'][^"\']+["\']',
                r'(?i)secret[_-]?key\s*=\s*["\'][^"\']+["\']',
            ],
            'sql_injection_risk': [
                r'\.execute\s*\(\s*["\'].*%.*["\']',
                r'\.execute\s*\(\s*f["\'].*\{.*\}.*["\']',
                r'cursor\.execute.*%',
            ],
            'path_traversal_risk': [
                r'open\s*\(\s*.*\+.*\)',
                r'os\.path\.join\s*\(.*\+',
                r'["\']\.\.\/["\']',
                r'["\']\.\.\\\\["\']',
            ],
            'command_injection_risk': [
                r'subprocess\.(run|call|check_output).*shell\s*=\s*True',
                r'os\.system\s*\(',
                r'os\.popen\s*\(',
            ],
            'eval_usage': [
                r'\beval\s*\(',
                r'\bexec\s*\(',
            ],
            'weak_crypto': [
                r'hashlib\.md5\(',
                r'hashlib\.sha1\(',
                r'random\.random\(\)',
                r'random\.randint\(',
            ],
        }
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate a single Python file for security issues."""
        if not file_path.suffix == '.py':
            return True
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Pattern-based checks
            self._check_security_patterns(file_path, content)
            
            # AST-based checks for more complex patterns
            try:
                tree = ast.parse(content)
                self._check_ast_security(file_path, tree)
            except SyntaxError:
                # Skip files with syntax errors (will be caught by other tools)
                pass
            
            return len(self.errors) == 0
            
        except Exception as e:
            self.warnings.append(f"Could not analyze {file_path}: {e}")
            return True
    
    def _check_security_patterns(self, file_path: Path, content: str) -> None:
        """Check for dangerous security patterns using regex."""
        lines = content.split('\n')
        
        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue
                    
                    if re.search(pattern, line):
                        self._add_security_issue(
                            file_path, line_num, category, 
                            f"Potential security issue: {pattern}"
                        )
    
    def _check_ast_security(self, file_path: Path, tree: ast.AST) -> None:
        """Check for security issues using AST analysis."""
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                self._check_dangerous_calls(file_path, node)
            
            # Check for dangerous imports
            elif isinstance(node, ast.Import):
                self._check_dangerous_imports(file_path, node)
            
            # Check for dangerous string operations
            elif isinstance(node, ast.BinOp):
                self._check_string_operations(file_path, node)
    
    def _check_dangerous_calls(self, file_path: Path, node: ast.Call) -> None:
        """Check for dangerous function calls."""
        func_name = self._get_function_name(node.func)
        
        dangerous_calls = {
            'eval', 'exec', 'compile', '__import__',
            'os.system', 'os.popen', 'subprocess.call'
        }
        
        if func_name in dangerous_calls:
            self._add_security_issue(
                file_path, node.lineno, 'dangerous_function',
                f"Dangerous function call: {func_name}"
            )
    
    def _check_dangerous_imports(self, file_path: Path, node: ast.Import) -> None:
        """Check for potentially dangerous imports."""
        dangerous_imports = {'pickle', 'dill', 'marshal'}
        
        for alias in node.names:
            if alias.name in dangerous_imports:
                self.warnings.append(
                    f"{file_path}:{node.lineno}: Warning: "
                    f"Potentially unsafe import: {alias.name}"
                )
    
    def _check_string_operations(self, file_path: Path, node: ast.BinOp) -> None:
        """Check for dangerous string operations."""
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str):
            # Check for SQL-like string formatting
            if any(keyword in node.left.s.lower() 
                   for keyword in ['select', 'insert', 'update', 'delete']):
                self.warnings.append(
                    f"{file_path}:{node.lineno}: Warning: "
                    f"Potential SQL injection risk in string formatting"
                )
    
    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_function_name(node.value)}.{node.attr}"
        return ""
    
    def _add_security_issue(self, file_path: Path, line_num: int, 
                          category: str, message: str) -> None:
        """Add a security issue to the error list."""
        severity = 'ERROR' if category in ['hardcoded_secrets', 'sql_injection_risk'] else 'WARNING'
        
        issue = f"{file_path}:{line_num}: {severity}: {category} - {message}"
        
        if severity == 'ERROR':
            self.errors.append(issue)
        else:
            self.warnings.append(issue)
    
    def validate_configuration(self) -> bool:
        """Validate security-related configuration files."""
        config_checks = [
            self._check_env_files(),
            self._check_requirements_security(),
            self._check_config_security(),
        ]
        
        return all(config_checks)
    
    def _check_env_files(self) -> bool:
        """Check for exposed secrets in environment files."""
        env_files = list(self.project_root.glob('**/.env*'))
        
        for env_file in env_files:
            if env_file.name == '.env.example':
                continue
            
            try:
                content = env_file.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        if len(value) > 20 and not value.startswith('$'):
                            self.warnings.append(
                                f"{env_file}:{line_num}: Warning: "
                                f"Potentially exposed secret: {key}"
                            )
            except Exception:
                continue
        
        return True
    
    def _check_requirements_security(self) -> bool:
        """Check for known vulnerable packages in requirements."""
        req_files = list(self.project_root.glob('**/requirements*.txt'))
        req_files.extend(list(self.project_root.glob('**/pyproject.toml')))
        
        # Known vulnerable package patterns
        vulnerable_patterns = [
            r'django\s*==?\s*[12]\.',  # Old Django versions
            r'flask\s*==?\s*0\.',      # Very old Flask
            r'requests\s*==?\s*2\.[0-9]\.',  # Old requests
        ]
        
        for req_file in req_files:
            try:
                content = req_file.read_text()
                
                for pattern in vulnerable_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.warnings.append(
                            f"{req_file}: Warning: Potentially vulnerable dependency"
                        )
            except Exception:
                continue
        
        return True
    
    def _check_config_security(self) -> bool:
        """Check security configuration in config files."""
        config_files = list(self.project_root.glob('**/config/**/*.yaml'))
        config_files.extend(list(self.project_root.glob('**/config/**/*.yml')))
        
        for config_file in config_files:
            try:
                content = config_file.read_text()
                
                # Check for debug mode in production configs
                if 'production' in str(config_file) and 'debug: true' in content.lower():
                    self.errors.append(
                        f"{config_file}: ERROR: Debug mode enabled in production config"
                    )
                
                # Check for insecure protocols
                if re.search(r'http://.*', content) and 'localhost' not in content:
                    self.warnings.append(
                        f"{config_file}: Warning: Insecure HTTP protocol in config"
                    )
            except Exception:
                continue
        
        return True
    
    def run_validation(self) -> bool:
        """Run all security validations."""
        print("🔒 Running security validation checks...")
        
        # Validate Python files
        python_files = []
        for pattern in ['libs/**/*.py', 'commands/**/*.py', 'api/**/*.py']:
            python_files.extend(self.project_root.glob(pattern))
        
        for py_file in python_files:
            self.validate_file(py_file)
        
        # Validate configuration
        self.validate_configuration()
        
        # Report results
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} security warnings:")
            for warning in self.warnings[:10]:  # Limit output
                print(f"  {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
        
        if self.errors:
            print(f"\n❌ {len(self.errors)} security errors:")
            for error in self.errors:
                print(f"  {error}")
            return False
        
        print(f"✅ Security validation passed ({len(python_files)} files checked)")
        return True


def main():
    """Main entry point for security validation."""
    validator = SecurityValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Security validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()