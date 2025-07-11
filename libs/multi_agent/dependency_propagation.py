"""Dependency change propagation system for multi-agent collaboration"""

import asyncio
import logging
import ast
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import hashlib

from .branch_manager import BranchManager
from .collaboration_engine import (
    CollaborationEngine,
    MessageType,
    MessagePriority,
)
from .branch_info_protocol import BranchInfoProtocol, BranchInfoType


logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of dependencies that can be tracked"""

    IMPORT = "import"  # Import statements
    FUNCTION_CALL = "function_call"  # Function calls
    CLASS_INHERITANCE = "class_inheritance"  # Class inheritance
    MODULE_REFERENCE = "module_reference"  # Module references
    API_USAGE = "api_usage"  # API usage
    CONFIGURATION = "configuration"  # Configuration dependencies
    DATA_SCHEMA = "data_schema"  # Data structure dependencies
    EXTERNAL_LIBRARY = "external_library"  # External library usage


class ChangeImpact(Enum):
    """Impact levels of dependency changes"""

    BREAKING = "breaking"  # Breaking changes requiring immediate action
    COMPATIBLE = "compatible"  # Backward compatible changes
    ENHANCEMENT = "enhancement"  # New features/enhancements
    INTERNAL = "internal"  # Internal implementation changes
    DEPRECATION = "deprecation"  # Deprecation warnings
    SECURITY = "security"  # Security-related changes


class PropagationStrategy(Enum):
    """Strategies for propagating dependency changes"""

    IMMEDIATE = "immediate"  # Propagate immediately
    BATCHED = "batched"  # Batch multiple changes
    SCHEDULED = "scheduled"  # Schedule for later propagation
    CONDITIONAL = "conditional"  # Propagate based on conditions
    MANUAL = "manual"  # Require manual approval


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph"""

    file_path: str
    module_name: str
    dependencies: Set[str] = field(default_factory=set)  # What this depends on
    dependents: Set[str] = field(default_factory=set)  # What depends on this
    exports: Dict[str, Any] = field(default_factory=dict)  # What this exports
    imports: Dict[str, Any] = field(default_factory=dict)  # What this imports
    last_analyzed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyChange:
    """Represents a dependency change event"""

    change_id: str
    source_file: str
    changed_by: str
    change_type: DependencyType
    impact_level: ChangeImpact
    change_details: Dict[str, Any]
    affected_files: List[str] = field(default_factory=list)
    affected_branches: List[str] = field(default_factory=list)
    propagation_strategy: PropagationStrategy = PropagationStrategy.IMMEDIATE
    propagated_to: Set[str] = field(default_factory=set)
    propagation_attempts: int = 0
    max_propagation_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    requires_manual_review: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PropagationResult:
    """Result of a propagation operation"""

    change_id: str
    success: bool
    propagated_to: List[str]
    failed_targets: List[str]
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DependencyPropagationSystem:
    """System for tracking and propagating dependency changes across branches"""

    def __init__(
        self,
        collaboration_engine: CollaborationEngine,
        branch_info_protocol: BranchInfoProtocol,
        branch_manager: BranchManager,
        repo_path: Optional[str] = None,
        auto_propagate: bool = True,
    ):
        """
        Initialize the dependency propagation system

        Args:
            collaboration_engine: Engine for agent collaboration
            branch_info_protocol: Protocol for branch information sharing
            branch_manager: Manager for branch operations
            repo_path: Path to git repository
            auto_propagate: Whether to automatically propagate changes
        """
        self.collaboration_engine = collaboration_engine
        self.branch_info_protocol = branch_info_protocol
        self.branch_manager = branch_manager
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.auto_propagate = auto_propagate

        # Dependency graph and tracking
        self.dependency_graph: Dict[str, DependencyNode] = {}
        self.change_queue: deque[DependencyChange] = deque()
        self.processing_queue: deque[DependencyChange] = deque()
        self.change_history: List[DependencyChange] = []

        # Propagation configuration
        self.batch_size = 10
        self.batch_timeout = 300  # 5 minutes
        self.max_concurrent_propagations = 5
        self.enable_impact_analysis = True

        # Statistics
        self.propagation_stats = {
            "changes_tracked": 0,
            "changes_propagated": 0,
            "propagation_success_rate": 0.0,
            "average_propagation_time": 0.0,
            "breaking_changes_detected": 0,
            "manual_reviews_required": 0,
            "affected_branches_total": 0,
        }

        # Background tasks
        self._running = False
        self._propagation_task = None
        self._analysis_task = None

    async def start(self):
        """Start the dependency propagation system"""
        self._running = True
        logger.info("Starting dependency propagation system")

        # Start background tasks
        self._propagation_task = asyncio.create_task(self._propagation_loop())
        self._analysis_task = asyncio.create_task(self._dependency_analysis_loop())

    async def stop(self):
        """Stop the dependency propagation system"""
        self._running = False
        logger.info("Stopping dependency propagation system")

        # Cancel background tasks
        if self._propagation_task:
            self._propagation_task.cancel()
        if self._analysis_task:
            self._analysis_task.cancel()

        # Wait for tasks to complete
        tasks = [t for t in [self._propagation_task, self._analysis_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def track_dependency_change(
        self,
        file_path: str,
        changed_by: str,
        change_type: DependencyType,
        change_details: Dict[str, Any],
        impact_level: Optional[ChangeImpact] = None,
        propagation_strategy: PropagationStrategy = PropagationStrategy.IMMEDIATE,
    ) -> str:
        """
        Track a new dependency change

        Args:
            file_path: Path to the changed file
            changed_by: ID of agent making the change
            change_type: Type of dependency change
            change_details: Details about the change
            impact_level: Impact level (auto-detected if None)
            propagation_strategy: Strategy for propagation

        Returns:
            Change ID
        """
        change_id = f"dep_change_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"

        # Auto-detect impact level if not provided
        if impact_level is None:
            impact_level = await self._analyze_change_impact(
                file_path, change_type, change_details
            )

        # Analyze affected files and branches
        affected_files = await self._find_affected_files(
            file_path, change_type, change_details
        )
        affected_branches = await self._find_affected_branches(affected_files)

        # Create change record
        dependency_change = DependencyChange(
            change_id=change_id,
            source_file=file_path,
            changed_by=changed_by,
            change_type=change_type,
            impact_level=impact_level,
            change_details=change_details,
            affected_files=affected_files,
            affected_branches=affected_branches,
            propagation_strategy=propagation_strategy,
            requires_manual_review=impact_level
            in [ChangeImpact.BREAKING, ChangeImpact.SECURITY],
        )

        # Queue for processing
        self.change_queue.append(dependency_change)
        self.change_history.append(dependency_change)
        self.propagation_stats["changes_tracked"] += 1

        logger.info(
            f"Tracked dependency change {change_id} in {file_path} by {changed_by}"
        )

        # Immediate propagation for critical changes
        if (
            propagation_strategy == PropagationStrategy.IMMEDIATE
            and impact_level in [ChangeImpact.BREAKING, ChangeImpact.SECURITY]
            and self.auto_propagate
        ):
            await self._process_single_change(dependency_change)

        return change_id

    async def build_dependency_graph(
        self, file_paths: Optional[List[str]] = None
    ) -> Dict[str, DependencyNode]:
        """
        Build or rebuild the dependency graph

        Args:
            file_paths: Specific files to analyze (None for all)

        Returns:
            Dependency graph
        """
        logger.info("Building dependency graph")

        if file_paths is None:
            # Find all Python files in the repository
            file_paths = list(self.repo_path.rglob("*.py"))
            file_paths = [str(p.relative_to(self.repo_path)) for p in file_paths]

        # Analyze each file
        for file_path in file_paths:
            await self._analyze_file_dependencies(file_path)

        logger.info(f"Built dependency graph with {len(self.dependency_graph)} nodes")
        return self.dependency_graph

    async def get_dependency_impact_report(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive impact report for a file

        Args:
            file_path: File to analyze

        Returns:
            Impact report
        """
        if file_path not in self.dependency_graph:
            await self._analyze_file_dependencies(file_path)

        node = self.dependency_graph.get(file_path)
        if not node:
            return {"error": "File not found in dependency graph"}

        # Calculate impact metrics
        direct_dependents = len(node.dependents)
        indirect_dependents = await self._calculate_indirect_dependents(file_path)
        total_impact = direct_dependents + indirect_dependents

        # Find affected branches
        affected_files = list(node.dependents)
        affected_branches = await self._find_affected_branches(affected_files)

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(node)

        return {
            "file_path": file_path,
            "module_name": node.module_name,
            "direct_dependents": direct_dependents,
            "indirect_dependents": indirect_dependents,
            "total_impact": total_impact,
            "affected_branches": affected_branches,
            "complexity_score": complexity_score,
            "dependencies": list(node.dependencies),
            "dependents": list(node.dependents),
            "exports": node.exports,
            "last_analyzed": node.last_analyzed.isoformat(),
            "risk_level": self._calculate_risk_level(complexity_score, total_impact),
        }

    async def propagate_changes_to_branches(
        self, change_ids: List[str], target_branches: Optional[List[str]] = None
    ) -> List[PropagationResult]:
        """
        Propagate specific changes to target branches

        Args:
            change_ids: IDs of changes to propagate
            target_branches: Target branches (None for all affected)

        Returns:
            List of propagation results
        """
        results = []

        for change_id in change_ids:
            # Find the change
            change = next(
                (c for c in self.change_history if c.change_id == change_id), None
            )
            if not change:
                logger.warning(f"Change {change_id} not found")
                continue

            # Determine target branches
            branches = target_branches or change.affected_branches

            # Propagate to each branch
            result = await self._propagate_change_to_branches(change, branches)
            results.append(result)

        return results

    async def get_pending_changes(
        self, agent_id: Optional[str] = None, branch_name: Optional[str] = None
    ) -> List[DependencyChange]:
        """
        Get pending changes for review or action

        Args:
            agent_id: Filter by agent (None for all)
            branch_name: Filter by branch (None for all)

        Returns:
            List of pending changes
        """
        pending = []

        for change in self.change_queue:
            # Filter by agent if specified
            if agent_id and change.changed_by != agent_id:
                continue

            # Filter by branch if specified
            if branch_name and branch_name not in change.affected_branches:
                continue

            pending.append(change)

        return pending

    # Private methods

    async def _analyze_file_dependencies(self, file_path: str):
        """Analyze dependencies for a single file"""
        full_path = self.repo_path / file_path

        if not full_path.exists() or not full_path.suffix == ".py":
            return

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Extract dependencies
            dependencies = set()
            imports = {}
            exports = {}

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Import statements
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name
                            dependencies.add(module_name)
                            imports[alias.asname or alias.name] = {
                                "type": "import",
                                "module": module_name,
                                "line": node.lineno,
                            }

                    elif isinstance(node, ast.ImportFrom) and node.module:
                        module_name = node.module
                        dependencies.add(module_name)
                        for alias in node.names:
                            imports[alias.asname or alias.name] = {
                                "type": "from_import",
                                "module": module_name,
                                "name": alias.name,
                                "line": node.lineno,
                            }

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Function definitions (exports)
                    exports[node.name] = {
                        "type": "function",
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                    }

                elif isinstance(node, ast.ClassDef):
                    # Class definitions (exports)
                    base_classes = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_classes.append(base.id)
                            dependencies.add(base.id)  # Inheritance dependency

                    exports[node.name] = {
                        "type": "class",
                        "line": node.lineno,
                        "bases": base_classes,
                    }

            # Create or update dependency node
            module_name = file_path.replace("/", ".").replace(".py", "")
            node = DependencyNode(
                file_path=file_path,
                module_name=module_name,
                dependencies=dependencies,
                imports=imports,
                exports=exports,
                last_analyzed=datetime.now(),
            )

            self.dependency_graph[file_path] = node

            # Update reverse dependencies
            await self._update_reverse_dependencies(file_path, dependencies)

        except Exception as e:
            logger.error(f"Error analyzing dependencies for {file_path}: {e}")

    async def _update_reverse_dependencies(
        self, file_path: str, dependencies: Set[str]
    ):
        """Update reverse dependency relationships"""
        for dep in dependencies:
            # Find files that match this dependency
            matching_files = []

            for dep_file_path, node in self.dependency_graph.items():
                if (
                    node.module_name == dep
                    or dep_file_path == dep
                    or dep_file_path.endswith(f"{dep}.py")
                ):
                    matching_files.append(dep_file_path)

            # Update dependents
            for matching_file in matching_files:
                if matching_file in self.dependency_graph:
                    self.dependency_graph[matching_file].dependents.add(file_path)

    async def _analyze_change_impact(
        self,
        file_path: str,
        change_type: DependencyType,
        change_details: Dict[str, Any],
    ) -> ChangeImpact:
        """Analyze the impact level of a change"""

        # Breaking change indicators
        breaking_keywords = [
            "remove",
            "delete",
            "deprecate",
            "breaking",
            "incompatible",
        ]
        if any(keyword in str(change_details).lower() for keyword in breaking_keywords):
            return ChangeImpact.BREAKING

        # Security change indicators
        security_keywords = ["security", "vulnerability", "auth", "permission", "token"]
        if any(keyword in str(change_details).lower() for keyword in security_keywords):
            return ChangeImpact.SECURITY

        # Check change type for impact
        if change_type in [DependencyType.FUNCTION_CALL, DependencyType.API_USAGE]:
            # Function signature changes are potentially breaking
            if "signature" in change_details or "parameters" in change_details:
                return ChangeImpact.BREAKING

        elif change_type == DependencyType.CLASS_INHERITANCE:
            # Inheritance changes can be breaking
            return ChangeImpact.BREAKING

        elif change_type == DependencyType.IMPORT:
            # Import changes are usually compatible
            return ChangeImpact.COMPATIBLE

        # Default to enhancement for new features
        if "add" in str(change_details).lower() or "new" in str(change_details).lower():
            return ChangeImpact.ENHANCEMENT

        return ChangeImpact.COMPATIBLE

    async def _find_affected_files(
        self,
        file_path: str,
        change_type: DependencyType,
        change_details: Dict[str, Any],
    ) -> List[str]:
        """Find files affected by a dependency change"""
        if file_path not in self.dependency_graph:
            await self._analyze_file_dependencies(file_path)

        node = self.dependency_graph.get(file_path)
        if not node:
            return []

        affected = list(node.dependents)

        # For breaking changes, include indirect dependents
        if (
            await self._analyze_change_impact(file_path, change_type, change_details)
            == ChangeImpact.BREAKING
        ):
            indirect = await self._calculate_indirect_dependents(file_path)
            affected.extend(self._get_indirect_dependent_files(file_path))

        return list(set(affected))

    async def _find_affected_branches(self, affected_files: List[str]) -> List[str]:
        """Find branches that contain the affected files"""
        affected_branches = set()

        # Get all branch info from the protocol
        all_branches = await self.branch_info_protocol.get_all_branches_info()

        for branch_name, branch_info in all_branches.items():
            # Check if any affected files are modified in this branch
            for affected_file in affected_files:
                if affected_file in branch_info.files_modified:
                    affected_branches.add(branch_name)
                    break

        return list(affected_branches)

    async def _calculate_indirect_dependents(self, file_path: str) -> int:
        """Calculate number of indirect dependents"""
        visited = set()
        queue = deque([file_path])
        indirect_count = 0

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)
            node = self.dependency_graph.get(current)

            if node:
                for dependent in node.dependents:
                    if dependent not in visited:
                        queue.append(dependent)
                        indirect_count += 1

        return indirect_count

    def _get_indirect_dependent_files(self, file_path: str) -> List[str]:
        """Get list of indirect dependent files"""
        visited = set()
        queue = deque([file_path])
        indirect_files = []

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)
            node = self.dependency_graph.get(current)

            if node:
                for dependent in node.dependents:
                    if dependent not in visited:
                        queue.append(dependent)
                        indirect_files.append(dependent)

        return indirect_files

    def _calculate_complexity_score(self, node: DependencyNode) -> float:
        """Calculate complexity score for a dependency node"""
        # Factors: number of dependencies, dependents, exports
        dependency_factor = len(node.dependencies) * 0.3
        dependent_factor = len(node.dependents) * 0.5
        export_factor = len(node.exports) * 0.2

        return min(10.0, dependency_factor + dependent_factor + export_factor)

    def _calculate_risk_level(self, complexity_score: float, total_impact: int) -> str:
        """Calculate risk level based on complexity and impact"""
        if complexity_score > 7 or total_impact > 10:
            return "high"
        elif complexity_score > 4 or total_impact > 5:
            return "medium"
        else:
            return "low"

    async def _process_single_change(
        self, change: DependencyChange
    ) -> PropagationResult:
        """Process a single dependency change"""
        start_time = datetime.now()

        try:
            # Update branch info protocol with dependency change
            for branch_name in change.affected_branches:
                await self.branch_info_protocol.update_branch_info(
                    branch_name=branch_name,
                    info_type=BranchInfoType.DEPENDENCY_MAP,
                    update_data={
                        "change_id": change.change_id,
                        "source_file": change.source_file,
                        "change_type": change.change_type.value,
                        "impact_level": change.impact_level.value,
                        "affected_files": change.affected_files,
                    },
                    requires_immediate_sync=change.impact_level
                    in [ChangeImpact.BREAKING, ChangeImpact.SECURITY],
                )

            # Send notifications to affected agents
            await self._notify_affected_agents(change)

            # Mark as processed
            change.processed_at = datetime.now()
            change.propagated_to.update(change.affected_branches)

            processing_time = (datetime.now() - start_time).total_seconds()

            # Update statistics
            self.propagation_stats["changes_propagated"] += 1
            self._update_propagation_stats(processing_time, True)

            return PropagationResult(
                change_id=change.change_id,
                success=True,
                propagated_to=change.affected_branches,
                failed_targets=[],
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Error processing change {change.change_id}: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_propagation_stats(processing_time, False)

            return PropagationResult(
                change_id=change.change_id,
                success=False,
                propagated_to=[],
                failed_targets=change.affected_branches,
                warnings=[str(e)],
                processing_time=processing_time,
            )

    async def _notify_affected_agents(self, change: DependencyChange):
        """Notify agents affected by a dependency change"""
        # Find agents working on affected branches
        affected_agents = set()

        for branch_name in change.affected_branches:
            branch_info = await self.branch_info_protocol.get_branch_info(branch_name)
            if branch_info:
                affected_agents.add(branch_info.agent_id)

        # Send notifications
        for agent_id in affected_agents:
            if agent_id != change.changed_by:  # Don't notify the change author
                await self.collaboration_engine.send_message(
                    sender_id=change.changed_by,
                    recipient_id=agent_id,
                    message_type=MessageType.DEPENDENCY_CHANGE,
                    subject=f"Dependency change affects your branch: {change.impact_level.value}",
                    content={
                        "change_id": change.change_id,
                        "source_file": change.source_file,
                        "change_type": change.change_type.value,
                        "impact_level": change.impact_level.value,
                        "affected_files": change.affected_files,
                        "change_details": change.change_details,
                        "requires_manual_review": change.requires_manual_review,
                    },
                    priority=MessagePriority.HIGH
                    if change.impact_level
                    in [ChangeImpact.BREAKING, ChangeImpact.SECURITY]
                    else MessagePriority.NORMAL,
                    requires_ack=change.requires_manual_review,
                )

    async def _propagate_change_to_branches(
        self, change: DependencyChange, branches: List[str]
    ) -> PropagationResult:
        """Propagate a specific change to target branches"""
        # This is a simplified implementation
        # In a real system, this would apply the actual changes to the branches

        propagated_to = []
        failed_targets = []

        for branch_name in branches:
            try:
                # Simulate propagation (in real implementation, would apply changes)
                logger.info(
                    f"Propagating change {change.change_id} to branch {branch_name}"
                )
                propagated_to.append(branch_name)

            except Exception as e:
                logger.error(f"Failed to propagate to {branch_name}: {e}")
                failed_targets.append(branch_name)

        return PropagationResult(
            change_id=change.change_id,
            success=len(failed_targets) == 0,
            propagated_to=propagated_to,
            failed_targets=failed_targets,
        )

    def _update_propagation_stats(self, processing_time: float, success: bool):
        """Update propagation statistics"""
        # Update average processing time
        total_changes = self.propagation_stats["changes_propagated"]
        current_avg = self.propagation_stats["average_propagation_time"]
        new_avg = (
            (current_avg * (total_changes - 1)) + processing_time
        ) / total_changes
        self.propagation_stats["average_propagation_time"] = new_avg

        # Update success rate
        if success:
            successful = self.propagation_stats["changes_propagated"]
        else:
            successful = self.propagation_stats["changes_propagated"] - 1

        self.propagation_stats["propagation_success_rate"] = successful / total_changes

    async def _propagation_loop(self):
        """Background task for processing dependency changes"""
        while self._running:
            try:
                # Process pending changes
                processed = 0
                while self.change_queue and processed < self.batch_size:
                    change = self.change_queue.popleft()

                    # Check if should be processed
                    if (
                        change.propagation_strategy == PropagationStrategy.IMMEDIATE
                        or change.impact_level
                        in [ChangeImpact.BREAKING, ChangeImpact.SECURITY]
                    ):
                        await self._process_single_change(change)
                        processed += 1

                await asyncio.sleep(5)  # Process every 5 seconds

            except Exception as e:
                logger.error(f"Error in propagation loop: {e}")
                await asyncio.sleep(10)

    async def _dependency_analysis_loop(self):
        """Background task for dependency analysis"""
        while self._running:
            try:
                # Periodically rebuild dependency graph
                await self.build_dependency_graph()
                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error in dependency analysis loop: {e}")
                await asyncio.sleep(3600)

    def get_propagation_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of propagation system"""
        return {
            "statistics": self.propagation_stats.copy(),
            "dependency_graph_size": len(self.dependency_graph),
            "pending_changes": len(self.change_queue),
            "processing_queue_size": len(self.processing_queue),
            "total_changes_tracked": len(self.change_history),
            "recent_changes": [
                {
                    "change_id": change.change_id,
                    "source_file": change.source_file,
                    "changed_by": change.changed_by,
                    "change_type": change.change_type.value,
                    "impact_level": change.impact_level.value,
                    "affected_branches": len(change.affected_branches),
                    "created_at": change.created_at.isoformat(),
                    "processed": change.processed_at is not None,
                }
                for change in self.change_history[-10:]  # Last 10 changes
            ],
        }
