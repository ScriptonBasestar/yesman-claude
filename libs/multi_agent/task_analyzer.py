"""Task analysis and dependency graph generation for multi-agent development."""

import ast
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .graph import DirectedGraph

logger = logging.getLogger(__name__)


@dataclass
class CodeDependency:
    """Represents a code dependency."""

    source_file: str
    imported_module: str
    import_type: str  # 'import', 'from_import', 'dynamic'
    line_number: int
    symbols: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TaskDefinition:
    """Definition of a development task."""

    task_id: str
    title: str
    description: str
    file_paths: list[str]  # Files this task will modify
    dependencies: list[str] = field(default_factory=list)  # Other task IDs
    estimated_hours: float = 1.0
    complexity: str = "medium"  # low, medium, high
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskDefinition":
        """Create from dictionary."""
        return cls(**data)


class TaskAnalyzer:
    """Analyzes tasks and generates dependency graphs."""

    def __init__(self, repo_path: str = ".") -> None:
        """Initialize task analyzer.

        Args:
            repo_path: Path to repository
        """
        self.repo_path = Path(repo_path).resolve()
        self.file_dependencies: dict[str, list[CodeDependency]] = {}
        self.task_graph = DirectedGraph()
        self._python_files_cache: list[Path] | None = None

    def analyze_file_dependencies(self, file_path: str) -> list[CodeDependency]:
        """Analyze dependencies of a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of dependencies
        """
        full_path = self.repo_path / file_path
        if not full_path.exists():
            logger.warning("File not found: %s", file_path)
            return []

        dependencies = []

        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content, filename=str(full_path))

            # Find imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep = CodeDependency(
                            source_file=file_path,
                            imported_module=alias.name,
                            import_type="import",
                            line_number=node.lineno,
                            symbols=[],
                        )
                        dependencies.append(dep)

                elif isinstance(node, ast.ImportFrom) and node.module:
                    symbols = [alias.name for alias in node.names]
                    dep = CodeDependency(
                        source_file=file_path,
                        imported_module=node.module,
                        import_type="from_import",
                        line_number=node.lineno,
                        symbols=symbols,
                    )
                    dependencies.append(dep)

            # Cache results
            self.file_dependencies[file_path] = dependencies

        except Exception as e:
            logger.exception("Failed to analyze %s: %s", file_path, e)

        return dependencies

    def find_related_files(self, file_path: str, depth: int = 2) -> set[str]:
        """Find files related to a given file through dependencies.

        Args:
            file_path: Starting file path
            depth: How many levels of dependencies to follow

        Returns:
            Set of related file paths
        """
        related = {file_path}
        to_check = {file_path}

        for _ in range(depth):
            new_files = set()

            for current_file in to_check:
                # Get dependencies of current file
                deps = self.analyze_file_dependencies(current_file)

                # Find local files that import this module
                module_name = self._file_to_module(current_file)

                for py_file in self._get_python_files():
                    if str(py_file) in related:
                        continue

                    file_deps = self.analyze_file_dependencies(str(py_file))

                    # Check if this file imports our module
                    for dep in file_deps:
                        if self._matches_module(dep.imported_module, module_name):
                            new_files.add(str(py_file))
                            break

                # Find files that current file imports
                for dep in deps:
                    imported_file = self._module_to_file(dep.imported_module)
                    if imported_file and imported_file not in related:
                        new_files.add(imported_file)

            related.update(new_files)
            to_check = new_files

            if not new_files:
                break

        return related

    def _get_python_files(self) -> list[Path]:
        """Get all Python files in repository."""
        if self._python_files_cache is None:
            self._python_files_cache = []

            for py_file in self.repo_path.rglob("*.py"):
                # Skip virtual environments and build directories
                if any(
                    part in py_file.parts
                    for part in [
                        "venv",
                        "env",
                        ".venv",
                        "__pycache__",
                        "build",
                        "dist",
                        ".eggs",
                        "node_modules",
                    ]
                ):
                    continue

                rel_path = py_file.relative_to(self.repo_path)
                self._python_files_cache.append(rel_path)

        return self._python_files_cache

    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        # Remove .py extension and convert path to module
        path = Path(file_path)
        if path.suffix == ".py":
            path = path.with_suffix("")

        # Convert path separators to dots
        module = str(path).replace("/", ".").replace("\\", ".")

        # Handle __init__.py files
        return module.removesuffix(".__init__")  # Remove .__init__

    def _module_to_file(self, module_name: str) -> str | None:
        """Convert module name to file path."""
        # Try different possibilities
        candidates = [
            module_name.replace(".", "/") + ".py",
            module_name.replace(".", "/") + "/__init__.py",
        ]

        for candidate in candidates:
            full_path = self.repo_path / candidate
            if full_path.exists():
                return candidate

        return None

    def _matches_module(self, imported: str, module: str) -> bool:
        """Check if imported module matches target module."""
        # Exact match
        if imported == module:
            return True

        # Parent module match (e.g., 'libs.core' matches 'libs.core.module')
        if module.startswith(imported + "."):
            return True

        # Relative import match
        return bool("." in imported and imported.split(".")[-1] == module.split(".")[-1])

    def create_task_from_files(
        self,
        task_id: str,
        title: str,
        file_paths: list[str],
        description: str = "",
        **kwargs,
    ) -> TaskDefinition:
        """Create a task definition from file paths.

        Args:
            task_id: Unique task identifier
            title: Task title
            file_paths: Files to be modified
            description: Task description
            **kwargs: Additional task properties

        Returns:
            TaskDefinition object
        """
        # Find all related files
        all_files = set()
        for file_path in file_paths:
            related = self.find_related_files(file_path, depth=1)
            all_files.update(related)

        task = TaskDefinition(
            task_id=task_id,
            title=title,
            description=description,
            file_paths=sorted(all_files),
            **kwargs,
        )

        # Add to graph
        self.task_graph.add_node(task_id, task=task)

        return task

    def analyze_task_dependencies(self, tasks: list[TaskDefinition]) -> DirectedGraph:
        """Analyze dependencies between tasks based on file overlaps.

        Args:
            tasks: List of task definitions

        Returns:
            Directed graph of task dependencies
        """
        # Clear and rebuild graph
        self.task_graph.clear()

        # Add all tasks as nodes
        for task in tasks:
            self.task_graph.add_node(task.task_id, task=task)

        # Analyze dependencies based on file overlaps
        for i, task1 in enumerate(tasks):
            for j, task2 in enumerate(tasks):
                if i >= j:  # Skip self and already checked pairs
                    continue

                # Check for file overlaps
                files1 = set(task1.file_paths)
                files2 = set(task2.file_paths)
                overlap = files1.intersection(files2)

                if overlap:
                    # Determine dependency direction based on complexity
                    # More complex tasks should depend on simpler ones
                    complexity_order = {"low": 1, "medium": 2, "high": 3}

                    if complexity_order.get(task1.complexity, 2) > complexity_order.get(
                        task2.complexity,
                        2,
                    ):
                        # task1 depends on task2
                        self.task_graph.add_edge(
                            task2.task_id,
                            task1.task_id,
                            overlap=list(overlap),
                        )
                    else:
                        # task2 depends on task1
                        self.task_graph.add_edge(
                            task1.task_id,
                            task2.task_id,
                            overlap=list(overlap),
                        )

        # Add explicit dependencies
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in self.task_graph:
                    self.task_graph.add_edge(dep_id, task.task_id, explicit=True)

        return self.task_graph

    def get_execution_order(self, tasks: list[TaskDefinition]) -> list[list[str]]:
        """Get optimal execution order for tasks.

        Args:
            tasks: List of task definitions

        Returns:
            List of task groups that can be executed in parallel
        """
        # Analyze dependencies
        graph = self.analyze_task_dependencies(tasks)

        # Check for cycles
        if not graph.is_directed_acyclic_graph():
            cycles = graph.simple_cycles()
            logger.warning("Dependency cycles detected: %s", cycles)

            # Break cycles by removing edges with lowest weight
            while not graph.is_directed_acyclic_graph():
                cycle = graph.simple_cycles()[0]
                # Remove edge from cycle
                graph.remove_edge(cycle[-1], cycle[0])

        # Get topological layers (tasks that can run in parallel)
        layers = []
        remaining = set(graph.nodes_iter())

        while remaining:
            # Find nodes with no dependencies in remaining set
            layer = []
            for node in remaining:
                predecessors = set(graph.predecessors(node))
                if not predecessors.intersection(remaining):
                    layer.append(node)

            if not layer:
                # Shouldn't happen if graph is DAG
                logger.error("No nodes without dependencies found")
                layer = list(remaining)

            layers.append(sorted(layer))
            remaining.difference_update(layer)

        return layers

    def estimate_parallel_time(
        self,
        tasks: list[TaskDefinition],
        max_agents: int = 3,
    ) -> float:
        """Estimate time to complete tasks with parallel execution.

        Args:
            tasks: List of task definitions
            max_agents: Maximum number of parallel agents

        Returns:
            Estimated hours
        """
        layers = self.get_execution_order(tasks)
        total_time = 0.0

        for layer in layers:
            # Get tasks in this layer
            layer_tasks = [t for t in tasks if t.task_id in layer]

            # Sort by estimated time (longest first)
            layer_tasks.sort(key=lambda t: t.estimated_hours, reverse=True)

            # Simulate parallel execution
            agent_times = [0.0] * min(max_agents, len(layer_tasks))

            for task in layer_tasks:
                # Assign to agent with least work
                min_agent = min(range(len(agent_times)), key=lambda i: agent_times[i])
                agent_times[min_agent] += task.estimated_hours

            # Layer time is the maximum agent time
            layer_time = max(agent_times) if agent_times else 0
            total_time += layer_time

        return total_time

    def export_dependency_graph(self, output_path: str) -> None:
        """Export dependency graph to JSON format."""
        data: dict[str, Any] = {"tasks": {}, "dependencies": []}

        # Export tasks
        for node_id in self.task_graph.nodes_iter():
            task = self.task_graph.nodes.get(node_id, {}).get("task")
            if task:
                data["tasks"][node_id] = task.to_dict()

        # Export dependencies
        edges = self.task_graph.edges_iter(data=True)
        for edge in edges:
            # When data=True, edges_iter returns tuples of (source, target, attrs)
            if len(edge) == 3:
                source, target, attrs = edge
                dep = {"source": source, "target": target, "attributes": attrs}
                data["dependencies"].append(dep)

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Exported dependency graph to %s", output_path)
