"""Simple directed graph implementation for task dependencies."""

from collections import defaultdict, deque
from typing import Any


class DirectedGraph:
    """Simple directed graph implementation."""

    def __init__(self) -> None:
        """Initialize empty graph."""
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)

    def add_node(self, node_id: str, **attrs) -> None:
        """Add a node with attributes."""
        if node_id not in self.nodes:
            self.nodes[node_id] = attrs
        else:
            self.nodes[node_id].update(attrs)

    def add_edge(self, source: str, target: str, **attrs) -> None:
        """Add an edge with attributes."""
        # Ensure nodes exist
        if source not in self.nodes:
            self.add_node(source)
        if target not in self.nodes:
            self.add_node(target)

        # Add edge
        self.edges[source][target] = attrs
        self.reverse_edges[target].add(source)

    def remove_edge(self, source: str, target: str) -> None:
        """Remove an edge."""
        if source in self.edges and target in self.edges[source]:
            del self.edges[source][target]
            self.reverse_edges[target].discard(source)

    def has_edge(self, source: str, target: str) -> bool:
        """Check if edge exists."""
        return source in self.edges and target in self.edges[source]

    def __contains__(self, node_id: str) -> bool:
        """Check if node exists in the graph."""
        return node_id in self.nodes

    def nodes_iter(self) -> list[str]:
        """Iterate over nodes."""
        return list(self.nodes.keys())

    def edges_iter(self, data: bool = False) -> list[tuple[str, str] | tuple[str, str, dict[str, Any]]]:
        """Iterate over edges."""
        result: list[tuple[str, str] | tuple[str, str, dict[str, Any]]] = []
        for source, targets in self.edges.items():
            for target, attrs in targets.items():
                if data:
                    result.append((source, target, attrs))
                else:
                    result.append((source, target))
        return result

    def predecessors(self, node: str) -> list[str]:
        """Get predecessor nodes."""
        return list(self.reverse_edges.get(node, set()))

    def successors(self, node: str) -> list[str]:
        """Get successor nodes."""
        return list(self.edges.get(node, {}).keys())

    def clear(self) -> None:
        """Clear the graph."""
        self.nodes.clear()
        self.edges.clear()
        self.reverse_edges.clear()

    def is_directed_acyclic_graph(self) -> bool:
        """Check if graph is a DAG."""
        # Use DFS to detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.successors(node):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        return all(not (node not in visited and has_cycle(node)) for node in self.nodes)

    def simple_cycles(self) -> list[list[str]]:
        """Find simple cycles in the graph."""
        cycles = []
        visited = set()
        rec_stack: list[str] = []

        def find_cycles(node: str, start: str) -> None:
            if node in rec_stack:
                # Found a cycle
                idx = rec_stack.index(node)
                cycle = [*rec_stack[idx:], node]
                cycles.append(cycle)
                return

            if node in visited and node != start:
                return

            visited.add(node)
            rec_stack.append(node)

            for neighbor in self.successors(node):
                find_cycles(neighbor, start)

            rec_stack.pop()

        for node in self.nodes:
            visited.clear()
            rec_stack.clear()
            find_cycles(node, node)

        # Remove duplicate cycles
        unique_cycles = []
        seen = set()

        for cycle in cycles:
            # Normalize cycle (start from smallest node)
            min_idx = cycle.index(min(cycle))
            normalized = cycle[min_idx:] + cycle[:min_idx]
            cycle_tuple = tuple(normalized)

            if cycle_tuple not in seen:
                seen.add(cycle_tuple)
                unique_cycles.append(normalized[:-1])  # Remove duplicate last element

        return unique_cycles

    def topological_sort(self) -> list[str]:
        """Return nodes in topological order."""
        if not self.is_directed_acyclic_graph():
            msg = "Graph contains cycles"
            raise ValueError(msg)

        # Kahn's algorithm
        in_degree = {node: len(self.predecessors(node)) for node in self.nodes}
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for successor in self.successors(node):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        return result
