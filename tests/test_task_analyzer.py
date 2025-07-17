"""Tests for TaskAnalyzer class."""

import json

import pytest

from libs.multi_agent.graph import DirectedGraph
from libs.multi_agent.task_analyzer import TaskAnalyzer, TaskDefinition


class TestTaskAnalyzer:
    """Test cases for TaskAnalyzer."""

    @pytest.fixture
    def test_repo(self, tmp_path):
        """Create a test repository structure."""
        # Create test files
        (tmp_path / "libs").mkdir()
        (tmp_path / "libs" / "__init__.py").write_text("")
        (tmp_path / "libs" / "module_a.py").write_text(
            """
import os
from typing import List
from libs.module_b import helper_function

def main():
    helper_function()
"""
        )

        (tmp_path / "libs" / "module_b.py").write_text(
            """
from libs.module_c import BaseClass

def helper_function():
    return BaseClass()

class HelperClass:
    pass
"""
        )

        (tmp_path / "libs" / "module_c.py").write_text(
            """
class BaseClass:
    def __init__(self):
        self.value = 42
"""
        )

        (tmp_path / "main.py").write_text(
            """
from libs.module_a import main
from libs.module_b import HelperClass

if __name__ == "__main__":
    main()
"""
        )

        return tmp_path

    @pytest.fixture
    def analyzer(self, test_repo):
        """Create TaskAnalyzer instance."""
        return TaskAnalyzer(repo_path=str(test_repo))

    def test_init(self, analyzer, test_repo):
        """Test TaskAnalyzer initialization."""
        assert analyzer.repo_path == test_repo
        assert analyzer.file_dependencies == {}
        assert isinstance(analyzer.task_graph, DirectedGraph)

    def test_analyze_file_dependencies(self, analyzer):
        """Test analyzing file dependencies."""
        deps = analyzer.analyze_file_dependencies("libs/module_a.py")

        assert len(deps) == 3

        # Check standard library import
        os_import = next((d for d in deps if d.imported_module == "os"), None)
        assert os_import is not None
        assert os_import.import_type == "import"
        assert os_import.line_number == 2

        # Check from import
        typing_import = next((d for d in deps if d.imported_module == "typing"), None)
        assert typing_import is not None
        assert typing_import.import_type == "from_import"
        assert "List" in typing_import.symbols

        # Check local import
        local_import = next(
            (d for d in deps if d.imported_module == "libs.module_b"),
            None,
        )
        assert local_import is not None
        assert local_import.import_type == "from_import"
        assert "helper_function" in local_import.symbols

    def test_find_related_files(self, analyzer):
        """Test finding related files."""
        # Find files related to module_b
        related = analyzer.find_related_files("libs/module_b.py", depth=2)

        # Should find module_a (imports module_b) and module_c (imported by module_b)
        assert "libs/module_b.py" in related
        assert "libs/module_c.py" in related  # Direct dependency
        assert "libs/module_a.py" in related  # Imports module_b

        # With depth=2, should also find main.py
        assert "main.py" in related

    def test_file_to_module_conversion(self, analyzer):
        """Test file path to module name conversion."""
        assert analyzer._file_to_module("libs/module_a.py") == "libs.module_a"
        assert analyzer._file_to_module("libs/__init__.py") == "libs"
        assert analyzer._file_to_module("main.py") == "main"

    def test_module_to_file_conversion(self, analyzer):
        """Test module name to file path conversion."""
        assert analyzer._module_to_file("libs.module_a") == "libs/module_a.py"
        assert analyzer._module_to_file("libs") == "libs/__init__.py"
        assert analyzer._module_to_file("main") == "main.py"
        assert analyzer._module_to_file("nonexistent.module") is None

    def test_create_task_from_files(self, analyzer):
        """Test creating task from files."""
        task = analyzer.create_task_from_files(
            task_id="task1",
            title="Refactor module_b",
            file_paths=["libs/module_b.py"],
            description="Refactor helper functions",
            complexity="medium",
            estimated_hours=2.0,
        )

        assert task.task_id == "task1"
        assert task.title == "Refactor module_b"
        assert task.description == "Refactor helper functions"
        assert task.complexity == "medium"
        assert task.estimated_hours == 2.0

        # Should include related files
        assert "libs/module_b.py" in task.file_paths
        assert "libs/module_c.py" in task.file_paths  # Direct dependency

        # Check task was added to graph
        assert "task1" in analyzer.task_graph.nodes_iter()

    def test_analyze_task_dependencies(self, analyzer):
        """Test analyzing dependencies between tasks."""
        tasks = [
            TaskDefinition(
                task_id="task1",
                title="Update module_c",
                file_paths=["libs/module_c.py"],
                complexity="low",
                estimated_hours=1.0,
            ),
            TaskDefinition(
                task_id="task2",
                title="Refactor module_b",
                file_paths=["libs/module_b.py", "libs/module_c.py"],
                complexity="medium",
                estimated_hours=2.0,
            ),
            TaskDefinition(
                task_id="task3",
                title="Update module_a",
                file_paths=["libs/module_a.py"],
                complexity="high",
                estimated_hours=3.0,
                dependencies=["task2"],  # Explicit dependency
            ),
        ]

        graph = analyzer.analyze_task_dependencies(tasks)

        # Check nodes
        assert len(graph.nodes_iter()) == 3
        assert all(task.task_id in graph.nodes_iter() for task in tasks)

        # Check edges
        # task1 -> task2 (file overlap, task2 more complex)
        assert graph.has_edge("task1", "task2")

        # task2 -> task3 (explicit dependency)
        assert graph.has_edge("task2", "task3")

    def test_get_execution_order(self, analyzer):
        """Test getting execution order."""
        tasks = [
            TaskDefinition(task_id="A", title="Task A", file_paths=["a.py"]),
            TaskDefinition(
                task_id="B",
                title="Task B",
                file_paths=["b.py"],
                dependencies=["A"],
            ),
            TaskDefinition(
                task_id="C",
                title="Task C",
                file_paths=["c.py"],
                dependencies=["A"],
            ),
            TaskDefinition(
                task_id="D",
                title="Task D",
                file_paths=["d.py"],
                dependencies=["B", "C"],
            ),
        ]

        layers = analyzer.get_execution_order(tasks)

        # Should have 3 layers
        assert len(layers) == 3

        # First layer: A (no dependencies)
        assert layers[0] == ["A"]

        # Second layer: B and C (both depend on A, can run parallel)
        assert set(layers[1]) == {"B", "C"}

        # Third layer: D (depends on B and C)
        assert layers[2] == ["D"]

    def test_get_execution_order_with_cycle(self, analyzer):
        """Test execution order with dependency cycle."""
        tasks = [
            TaskDefinition(
                task_id="A",
                title="Task A",
                file_paths=["a.py"],
                dependencies=["C"],
            ),
            TaskDefinition(
                task_id="B",
                title="Task B",
                file_paths=["b.py"],
                dependencies=["A"],
            ),
            TaskDefinition(
                task_id="C",
                title="Task C",
                file_paths=["c.py"],
                dependencies=["B"],
            ),
        ]

        # Should handle cycle gracefully
        layers = analyzer.get_execution_order(tasks)

        # All tasks should be scheduled (cycle broken)
        all_tasks = [task for layer in layers for task in layer]
        assert set(all_tasks) == {"A", "B", "C"}

    def test_estimate_parallel_time(self, analyzer):
        """Test estimating parallel execution time."""
        tasks = [
            TaskDefinition(
                task_id="A",
                title="Task A",
                file_paths=["a.py"],
                estimated_hours=2.0,
            ),
            TaskDefinition(
                task_id="B",
                title="Task B",
                file_paths=["b.py"],
                estimated_hours=3.0,
                dependencies=["A"],
            ),
            TaskDefinition(
                task_id="C",
                title="Task C",
                file_paths=["c.py"],
                estimated_hours=1.0,
                dependencies=["A"],
            ),
            TaskDefinition(
                task_id="D",
                title="Task D",
                file_paths=["d.py"],
                estimated_hours=2.0,
                dependencies=["B", "C"],
            ),
        ]

        # With 2 agents
        time_2_agents = analyzer.estimate_parallel_time(tasks, max_agents=2)

        # Expected timeline:
        # Layer 1: A (2h)
        # Layer 2: B (3h) and C (1h) in parallel = 3h
        # Layer 3: D (2h)
        # Total: 2 + 3 + 2 = 7h
        assert time_2_agents == 7.0

        # With 1 agent (sequential)
        time_1_agent = analyzer.estimate_parallel_time(tasks, max_agents=1)
        # All tasks sequential: 2 + 3 + 1 + 2 = 8h
        assert time_1_agent == 8.0

    def test_export_dependency_graph(self, analyzer, tmp_path):
        """Test exporting dependency graph."""
        tasks = [
            TaskDefinition(task_id="task1", title="Task 1", file_paths=["file1.py"]),
            TaskDefinition(
                task_id="task2",
                title="Task 2",
                file_paths=["file2.py"],
                dependencies=["task1"],
            ),
        ]

        analyzer.analyze_task_dependencies(tasks)

        output_file = tmp_path / "graph.json"
        analyzer.export_dependency_graph(str(output_file))

        assert output_file.exists()

        # Load and verify
        with open(output_file) as f:
            data = json.load(f)

        assert "tasks" in data
        assert "dependencies" in data
        assert len(data["tasks"]) == 2
        assert len(data["dependencies"]) == 1

        # Check dependency
        dep = data["dependencies"][0]
        assert dep["source"] == "task1"
        assert dep["target"] == "task2"

    def test_task_definition_serialization(self):
        """Test TaskDefinition to/from dict."""
        task = TaskDefinition(
            task_id="test",
            title="Test Task",
            description="A test task",
            file_paths=["test.py"],
            dependencies=["dep1"],
            estimated_hours=2.5,
            complexity="high",
            metadata={"key": "value"},
        )

        # To dict
        task_dict = task.to_dict()
        assert task_dict["task_id"] == "test"
        assert task_dict["title"] == "Test Task"
        assert task_dict["metadata"]["key"] == "value"

        # From dict
        task2 = TaskDefinition.from_dict(task_dict)
        assert task2.task_id == task.task_id
        assert task2.title == task.title
        assert task2.metadata == task.metadata
