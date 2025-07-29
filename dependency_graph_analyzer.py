#!/usr/bin/env python3
"""
Dependency Graph Analysis Script for Yesman-Claude Project

This script analyzes internal Python dependencies across libs/, commands/, and api/ directories.
It extracts import statements, builds dependency mappings, identifies circular dependencies,
and calculates coupling metrics.

Features:
- Scans all Python files in specified directories
- Extracts both 'import' and 'from...import' statements
- Identifies circular dependencies using graph algorithms
- Calculates coupling metrics (afferent/efferent coupling)
- Finds most depended-upon modules
- Outputs results in JSON format

Copyright (c) 2024 Yesman Claude Project
Licensed under the MIT License
"""

import ast
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ImportInfo:
    """Information about an import statement."""

    imported_module: str
    importing_module: str
    import_type: str  # 'import' or 'from_import'
    imported_names: List[str] = field(default_factory=list)
    line_number: int = 0
    is_internal: bool = False


@dataclass
class ModuleInfo:
    """Information about a module and its dependencies."""

    module_path: str
    imports: List[ImportInfo] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    lines_of_code: int = 0
    is_package: bool = False


@dataclass
class CircularDependency:
    """Information about a circular dependency."""

    cycle: List[str]
    cycle_length: int
    severity: str  # 'low', 'medium', 'high'


@dataclass
class CouplingMetrics:
    """Coupling metrics for a module."""

    module: str
    afferent_coupling: int  # Number of modules that depend on this module
    efferent_coupling: int  # Number of modules this module depends on
    instability: float  # I = Ce / (Ca + Ce)
    abstractness: float  # A = Abstract classes / Total classes
    distance: float  # D = |A + I - 1|


class DependencyGraphAnalyzer:
    """Analyzes Python module dependencies in a project."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.modules: Dict[str, ModuleInfo] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.circular_dependencies: List[CircularDependency] = []
        self.coupling_metrics: Dict[str, CouplingMetrics] = {}

        # Internal module prefixes to track
        self.internal_prefixes = ["libs.", "commands.", "api."]

        # Directories to scan
        self.scan_directories = ["libs", "commands", "api"]

    def normalize_module_path(self, file_path: Path) -> str:
        """Convert file path to module path notation."""
        try:
            # Get relative path from project root
            rel_path = file_path.relative_to(self.project_root)

            # Convert to module notation
            parts = list(rel_path.parts)

            # Remove .py extension
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]

            # Handle __init__.py files
            if parts[-1] == "__init__":
                parts = parts[:-1]

            return ".".join(parts)
        except ValueError:
            # File is outside project root
            return str(file_path)

    def is_internal_module(self, module_name: str) -> bool:
        """Check if a module is internal to the project."""
        return any(module_name.startswith(prefix) for prefix in self.internal_prefixes)

    def extract_imports_from_ast(self, file_path: Path, ast_node: ast.AST) -> List[ImportInfo]:
        """Extract import information using AST analysis."""
        imports = []
        module_path = self.normalize_module_path(file_path)

        for node in ast.walk(ast_node):
            if isinstance(node, ast.Import):
                # Handle 'import module' statements
                for alias in node.names:
                    import_info = ImportInfo(
                        imported_module=alias.name,
                        importing_module=module_path,
                        import_type="import",
                        imported_names=[alias.asname or alias.name],
                        line_number=node.lineno,
                        is_internal=self.is_internal_module(alias.name),
                    )
                    imports.append(import_info)

            elif isinstance(node, ast.ImportFrom):
                # Handle 'from module import ...' statements
                if node.module:
                    imported_names = [alias.name for alias in node.names]
                    import_info = ImportInfo(
                        imported_module=node.module,
                        importing_module=module_path,
                        import_type="from_import",
                        imported_names=imported_names,
                        line_number=node.lineno,
                        is_internal=self.is_internal_module(node.module),
                    )
                    imports.append(import_info)

        return imports

    def extract_imports_from_regex(self, file_path: Path, content: str) -> List[ImportInfo]:
        """Extract imports using regex (fallback method)."""
        imports = []
        module_path = self.normalize_module_path(file_path)
        lines = content.split("\n")

        # Patterns for different import types
        import_patterns = [
            (r"^import\s+([\w\.]+)(?:\s+as\s+\w+)?", "import"),
            (r"^from\s+([\w\.]+)\s+import\s+(.+)", "from_import"),
        ]

        for line_no, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            for pattern, import_type in import_patterns:
                match = re.match(pattern, line)
                if match:
                    if import_type == "import":
                        module_name = match.group(1)
                        import_info = ImportInfo(
                            imported_module=module_name,
                            importing_module=module_path,
                            import_type=import_type,
                            imported_names=[module_name.split(".")[-1]],
                            line_number=line_no,
                            is_internal=self.is_internal_module(module_name),
                        )
                        imports.append(import_info)

                    elif import_type == "from_import":
                        module_name = match.group(1)
                        imported_items = match.group(2)

                        # Parse imported items (handle parentheses, commas, etc.)
                        imported_names = []
                        if imported_items:
                            # Remove parentheses and split by comma
                            items = re.sub(r"[()]", "", imported_items)
                            imported_names = [item.strip().split(" as ")[0] for item in items.split(",")]
                            imported_names = [name.strip() for name in imported_names if name.strip()]

                        import_info = ImportInfo(
                            imported_module=module_name,
                            importing_module=module_path,
                            import_type=import_type,
                            imported_names=imported_names,
                            line_number=line_no,
                            is_internal=self.is_internal_module(module_name),
                        )
                        imports.append(import_info)
                    break

        return imports

    def analyze_file(self, file_path: Path) -> ModuleInfo:
        """Analyze a single Python file for dependencies."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Count lines of code (excluding empty lines and comments)
            lines = content.split("\n")
            loc = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

            module_path = self.normalize_module_path(file_path)
            is_package = file_path.name == "__init__.py"

            # Try AST parsing first
            imports = []
            try:
                tree = ast.parse(content)
                imports = self.extract_imports_from_ast(file_path, tree)
            except SyntaxError:
                logger.warning(f"AST parsing failed for {file_path}, using regex fallback")
                imports = self.extract_imports_from_regex(file_path, content)

            # Filter for internal imports only
            internal_imports = [imp for imp in imports if imp.is_internal]

            # Extract dependencies
            dependencies = set()
            for imp in internal_imports:
                dependencies.add(imp.imported_module)

            module_info = ModuleInfo(module_path=module_path, imports=internal_imports, dependencies=dependencies, lines_of_code=loc, is_package=is_package)

            return module_info

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return ModuleInfo(module_path=self.normalize_module_path(file_path))

    def scan_directory(self, directory: Path) -> None:
        """Recursively scan directory for Python files."""
        if not directory.exists():
            logger.warning(f"Directory {directory} does not exist")
            return

        python_files = directory.rglob("*.py")

        for file_path in python_files:
            # Skip __pycache__ and other generated files
            if "__pycache__" in str(file_path) or file_path.name.startswith("."):
                continue

            logger.debug(f"Analyzing file: {file_path}")
            module_info = self.analyze_file(file_path)
            self.modules[module_info.module_path] = module_info

    def build_dependency_graphs(self) -> None:
        """Build forward and reverse dependency graphs."""
        for module_path, module_info in self.modules.items():
            for dependency in module_info.dependencies:
                # Only include dependencies that exist in our scanned modules
                if dependency in self.modules:
                    self.dependency_graph[module_path].add(dependency)
                    self.reverse_dependency_graph[dependency].add(module_path)
                    self.modules[dependency].dependents.add(module_path)

    def find_circular_dependencies(self) -> List[CircularDependency]:
        """Find circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]

                # Determine severity based on cycle length and module types
                severity = "low"
                if len(cycle) <= 3:
                    severity = "high"
                elif len(cycle) <= 5:
                    severity = "medium"

                cycles.append(CircularDependency(cycle=cycle, cycle_length=len(cycle) - 1, severity=severity))
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.dependency_graph.get(node, set()):
                dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for module in self.modules:
            if module not in visited:
                dfs(module, [])

        # Remove duplicate cycles
        unique_cycles = []
        cycle_signatures = set()

        for cycle in cycles:
            # Create a canonical representation of the cycle
            min_idx = cycle.cycle.index(min(cycle.cycle[:-1]))
            canonical = cycle.cycle[min_idx:-1] + cycle.cycle[:min_idx] + [cycle.cycle[min_idx]]
            signature = tuple(canonical)

            if signature not in cycle_signatures:
                cycle_signatures.add(signature)
                unique_cycles.append(cycle)

        return unique_cycles

    def calculate_coupling_metrics(self) -> Dict[str, CouplingMetrics]:
        """Calculate coupling metrics for all modules."""
        metrics = {}

        for module_path, module_info in self.modules.items():
            # Afferent coupling (Ca) - number of modules that depend on this module
            ca = len(module_info.dependents)

            # Efferent coupling (Ce) - number of modules this module depends on
            ce = len(module_info.dependencies)

            # Instability (I) = Ce / (Ca + Ce)
            instability = ce / (ca + ce) if (ca + ce) > 0 else 0

            # Abstractness (A) - simplified calculation
            # For now, assume 0 (would need more sophisticated analysis)
            abstractness = 0.0

            # Distance from main sequence (D) = |A + I - 1|
            distance = abs(abstractness + instability - 1)

            metrics[module_path] = CouplingMetrics(module=module_path, afferent_coupling=ca, efferent_coupling=ce, instability=instability, abstractness=abstractness, distance=distance)

        return metrics

    def get_most_depended_upon_modules(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get modules with the highest afferent coupling."""
        module_dependents = [(module, len(info.dependents)) for module, info in self.modules.items()]
        return sorted(module_dependents, key=lambda x: x[1], reverse=True)[:limit]

    def get_most_dependent_modules(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get modules with the highest efferent coupling."""
        module_dependencies = [(module, len(info.dependencies)) for module, info in self.modules.items()]
        return sorted(module_dependencies, key=lambda x: x[1], reverse=True)[:limit]

    def analyze(self) -> None:
        """Run complete dependency analysis."""
        logger.info("Starting dependency analysis...")

        # Scan all specified directories
        for directory_name in self.scan_directories:
            directory_path = self.project_root / directory_name
            logger.info(f"Scanning directory: {directory_path}")
            self.scan_directory(directory_path)

        logger.info(f"Found {len(self.modules)} Python modules")

        # Build dependency graphs
        logger.info("Building dependency graphs...")
        self.build_dependency_graphs()

        # Find circular dependencies
        logger.info("Finding circular dependencies...")
        self.circular_dependencies = self.find_circular_dependencies()

        # Calculate coupling metrics
        logger.info("Calculating coupling metrics...")
        self.coupling_metrics = self.calculate_coupling_metrics()

        logger.info("Analysis complete!")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        # Summary statistics
        total_modules = len(self.modules)
        total_dependencies = sum(len(info.dependencies) for info in self.modules.values())
        total_loc = sum(info.lines_of_code for info in self.modules.values())

        # Most depended upon modules
        most_depended_upon = self.get_most_depended_upon_modules()
        most_dependent = self.get_most_dependent_modules()

        # Circular dependency summary
        circular_deps_by_severity = defaultdict(int)
        for cycle in self.circular_dependencies:
            circular_deps_by_severity[cycle.severity] += 1

        # High coupling modules (instability > 0.8 or distance > 0.5)
        high_coupling_modules = []
        for module, metrics in self.coupling_metrics.items():
            if metrics.instability > 0.8 or metrics.distance > 0.5:
                high_coupling_modules.append(
                    {"module": module, "instability": metrics.instability, "distance": metrics.distance, "afferent_coupling": metrics.afferent_coupling, "efferent_coupling": metrics.efferent_coupling}
                )

        # Module details
        module_details = {}
        for module_path, module_info in self.modules.items():
            module_details[module_path] = {
                "dependencies": list(module_info.dependencies),
                "dependents": list(module_info.dependents),
                "lines_of_code": module_info.lines_of_code,
                "is_package": module_info.is_package,
                "import_count": len(module_info.imports),
                "coupling_metrics": {
                    "afferent_coupling": self.coupling_metrics[module_path].afferent_coupling,
                    "efferent_coupling": self.coupling_metrics[module_path].efferent_coupling,
                    "instability": self.coupling_metrics[module_path].instability,
                    "distance": self.coupling_metrics[module_path].distance,
                },
            }

        # Circular dependencies details
        circular_deps_details = []
        for cycle in self.circular_dependencies:
            circular_deps_details.append({"cycle": cycle.cycle, "cycle_length": cycle.cycle_length, "severity": cycle.severity})

        report = {
            "analysis_metadata": {"timestamp": "", "project_root": str(self.project_root), "directories_scanned": self.scan_directories, "total_modules_analyzed": total_modules},
            "summary_statistics": {
                "total_modules": total_modules,
                "total_internal_dependencies": total_dependencies,
                "total_lines_of_code": total_loc,
                "average_dependencies_per_module": total_dependencies / total_modules if total_modules > 0 else 0,
                "circular_dependencies_count": len(self.circular_dependencies),
                "circular_dependencies_by_severity": dict(circular_deps_by_severity),
            },
            "most_depended_upon_modules": [{"module": module, "dependent_count": count} for module, count in most_depended_upon],
            "most_dependent_modules": [{"module": module, "dependency_count": count} for module, count in most_dependent],
            "high_coupling_modules": high_coupling_modules,
            "circular_dependencies": circular_deps_details,
            "modules": module_details,
        }

        return report

    def save_report(self, output_path: Path, report: Dict[str, Any]) -> None:
        """Save analysis report to JSON file."""
        # Add timestamp
        from datetime import datetime

        report["analysis_metadata"]["timestamp"] = datetime.now().isoformat()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)

        logger.info(f"Analysis report saved to: {output_path}")


def main():
    """Main entry point for dependency analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Python module dependencies")
    parser.add_argument("--project-root", "-p", type=Path, default=Path.cwd(), help="Project root directory (default: current directory)")
    parser.add_argument("--output", "-o", type=Path, default=Path("dependency_analysis.json"), help="Output JSON file path (default: dependency_analysis.json)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize analyzer
    analyzer = DependencyGraphAnalyzer(args.project_root)

    try:
        # Run analysis
        analyzer.analyze()

        # Generate and save report
        report = analyzer.generate_report()
        analyzer.save_report(args.output, report)

        # Print summary
        print("\n🔍 Dependency Analysis Complete!")
        print(f"📊 Modules analyzed: {report['summary_statistics']['total_modules']}")
        print(f"🔗 Internal dependencies: {report['summary_statistics']['total_internal_dependencies']}")
        print(f"🔄 Circular dependencies: {len(report['circular_dependencies'])}")
        print(f"📈 High coupling modules: {len(report['high_coupling_modules'])}")
        print(f"📄 Report saved to: {args.output}")

        # Show top dependencies
        if report["most_depended_upon_modules"]:
            print("\n🏆 Most depended-upon modules:")
            for item in report["most_depended_upon_modules"][:5]:
                print(f"  - {item['module']}: {item['dependent_count']} dependents")

        # Show circular dependencies
        if report["circular_dependencies"]:
            print("\n⚠️  Circular dependencies found:")
            for cycle in report["circular_dependencies"][:3]:
                cycle_str = " → ".join(cycle["cycle"])
                print(f"  - [{cycle['severity'].upper()}] {cycle_str}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
