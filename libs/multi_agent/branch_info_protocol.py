# Copyright notice.

import asyncio
import contextlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

from .branch_manager import BranchManager
from .collaboration_engine import CollaborationEngine, MessagePriority, MessageType

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Branch information sharing protocol for multi-agent collaboration."""


logger = logging.getLogger(__name__)


class BranchInfoType(Enum):
    """Types of branch information that can be shared."""

    BRANCH_STATE = "branch_state"  # Current state of branch
    COMMIT_HISTORY = "commit_history"  # Recent commits
    FILE_CHANGES = "file_changes"  # Files modified in branch
    DEPENDENCY_MAP = "dependency_map"  # Dependencies and imports
    TEST_STATUS = "test_status"  # Test results
    BUILD_STATUS = "build_status"  # Build status
    CONFLICT_INFO = "conflict_info"  # Potential conflicts
    MERGE_READINESS = "merge_readiness"  # Ready to merge status
    WORK_PROGRESS = "work_progress"  # Task completion status
    API_CHANGES = "api_changes"  # API signature changes


class SyncStrategy(Enum):
    """Strategies for synchronizing branch information."""

    IMMEDIATE = "immediate"  # Share immediately on change
    PERIODIC = "periodic"  # Share at regular intervals
    ON_DEMAND = "on_demand"  # Share when requested
    MILESTONE = "milestone"  # Share at key milestones
    SMART = "smart"  # Adaptive based on activity


@dataclass
class BranchInfo:
    """Information about a branch's current state."""

    branch_name: str
    agent_id: str
    base_branch: str
    created_at: datetime
    last_updated: datetime
    commit_count: int = 0
    files_modified: list[str] = field(default_factory=list)
    tests_passed: bool | None = None
    build_status: str | None = None
    merge_ready: bool = False
    conflicts_detected: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    api_signatures: dict[str] = field(default_factory=dict)
    work_items: list[str] = field(default_factory=list)
    metadata: dict[str] = field(default_factory=dict)


@dataclass
class BranchSyncEvent:
    """Event representing a branch synchronization."""

    event_id: str
    branch_name: str
    agent_id: str
    event_type: BranchInfoType
    event_data: dict[str]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL
    requires_action: bool = False
    action_items: list[str] = field(default_factory=list)


class BranchInfoProtocol:
    """Protocol for sharing branch information between agents."""

    def __init__(
        self,
        branch_manager: BranchManager,
        collaboration_engine: CollaborationEngine,
        repo_path: str | None = None,
        sync_strategy: SyncStrategy = SyncStrategy.SMART,
    ) -> None:
        """Initialize the branch info protocol.

        Args:
            branch_manager: Manager for branch operations
            collaboration_engine: Engine for agent collaboration
            repo_path: Path to git repository
            sync_strategy: Strategy for information synchronization

        Returns:
            Description of return value
        """
        self.branch_manager = branch_manager
        self.collaboration_engine = collaboration_engine
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.sync_strategy = sync_strategy

        # Branch information storage
        self.branch_info: dict[str, BranchInfo] = {}
        self.sync_history: list[BranchSyncEvent] = []
        self.branch_subscriptions: dict[str, set[str]] = defaultdict(
            set,
        )  # branch -> interested agents

        # Sync configuration
        self.sync_interval = 300  # 5 minutes for periodic sync
        self.immediate_sync_types = {
            BranchInfoType.CONFLICT_INFO,
            BranchInfoType.API_CHANGES,
            BranchInfoType.BUILD_STATUS,
        }

        # Protocol statistics
        self.protocol_stats = {
            "syncs_performed": 0,
            "info_shared": 0,
            "conflicts_detected": 0,
            "merge_ready_branches": 0,
            "api_changes_tracked": 0,
            "subscriptions_active": 0,
        }

        # Background tasks
        self._running = False
        self._sync_task: asyncio.Task[object] | None = None

    async def start(self) -> None:
        """Start the branch info protocol."""
        self._running = True
        logger.info("Starting branch info protocol")

        # Start sync task based on strategy
        if self.sync_strategy in {SyncStrategy.PERIODIC, SyncStrategy.SMART}:
            self._sync_task = asyncio.create_task(self._periodic_sync_loop())

    async def stop(self) -> None:
        """Stop the branch info protocol."""
        self._running = False
        logger.info("Stopping branch info protocol")

        if self._sync_task:
            self._sync_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sync_task

    async def register_branch(
        self,
        branch_name: str,
        agent_id: str,
        base_branch: str = "main",
        work_items: list[str] | None = None,
    ) -> BranchInfo:
        """Register a new branch with the protocol.

        Args:
            branch_name: Name of the branch
            agent_id: ID of agent working on branch
            base_branch: Base branch name
            work_items: List of work items/tasks for this branch

        """
        branch_info = BranchInfo(
            branch_name=branch_name,
            agent_id=agent_id,
            base_branch=base_branch,
            created_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
            work_items=work_items or [],
        )

        self.branch_info[branch_name] = branch_info

        # Auto-subscribe the agent to their own branch
        self.branch_subscriptions[branch_name].add(agent_id)
        self.protocol_stats["subscriptions_active"] += 1

        # Share initial branch info
        await self._share_branch_info(
            branch_info,
            BranchInfoType.BRANCH_STATE,
            {"action": "branch_created", "work_items": work_items},
        )

        logger.info("Registered branch %s for agent %s", branch_name, agent_id)
        return branch_info

    async def update_branch_info(
        self,
        branch_name: str,
        info_type: BranchInfoType,
        update_data: dict[str],
        requires_immediate_sync: bool = False,  # noqa: FBT001
    ) -> None:
        """Update branch information and potentially trigger sync.

        Args:
            branch_name: Name of the branch
            info_type: Type of information being updated
            update_data: Update data
            requires_immediate_sync: Force immediate synchronization
        """
        if branch_name not in self.branch_info:
            logger.warning("Branch %s not registered", branch_name)
            return

        branch_info = self.branch_info[branch_name]
        branch_info.last_updated = datetime.now(UTC)

        # Apply updates based on type
        if info_type == BranchInfoType.FILE_CHANGES:
            branch_info.files_modified = update_data.get("files", [])

        elif info_type == BranchInfoType.TEST_STATUS:
            branch_info.tests_passed = update_data.get("passed")

        elif info_type == BranchInfoType.BUILD_STATUS:
            branch_info.build_status = update_data.get("status", "unknown")

        elif info_type == BranchInfoType.CONFLICT_INFO:
            branch_info.conflicts_detected = update_data.get("conflicts", [])
            self.protocol_stats["conflicts_detected"] += len(
                branch_info.conflicts_detected,
            )

        elif info_type == BranchInfoType.API_CHANGES:
            branch_info.api_signatures.update(update_data.get("signatures", {}))
            self.protocol_stats["api_changes_tracked"] += 1

        elif info_type == BranchInfoType.DEPENDENCY_MAP:
            branch_info.dependencies = update_data.get("dependencies", {})

        elif info_type == BranchInfoType.MERGE_READINESS:
            branch_info.merge_ready = update_data.get("ready", False)
            if branch_info.merge_ready:
                self.protocol_stats["merge_ready_branches"] += 1

        elif info_type == BranchInfoType.WORK_PROGRESS:
            completed_items = update_data.get("completed", [])
            remaining_items = update_data.get("remaining", [])
            branch_info.work_items = remaining_items
            branch_info.metadata["completed_items"] = completed_items

        # Determine if sync is needed
        should_sync = requires_immediate_sync or info_type in self.immediate_sync_types or self.sync_strategy == SyncStrategy.IMMEDIATE

        if should_sync:
            await self._share_branch_info(branch_info, info_type, update_data)

    async def get_branch_info(self, branch_name: str) -> BranchInfo | None:
        """Get current information about a branch."""
        return self.branch_info.get(branch_name)

    async def get_all_branches_info(self) -> dict[str, BranchInfo]:
        """Get information about all branches."""
        return self.branch_info.copy()

    async def subscribe_to_branch(self, agent_id: str, branch_name: str) -> None:
        """Subscribe an agent to receive updates about a branch."""
        self.branch_subscriptions[branch_name].add(agent_id)
        self.protocol_stats["subscriptions_active"] += 1

        logger.info("Agent %s subscribed to branch %s", agent_id, branch_name)

        # Send current branch info to new subscriber
        if branch_name in self.branch_info:
            await self._send_branch_update_to_agent(
                agent_id,
                self.branch_info[branch_name],
                BranchInfoType.BRANCH_STATE,
                {"subscription": "initial"},
            )

    async def unsubscribe_from_branch(self, agent_id: str, branch_name: str) -> None:
        """Unsubscribe an agent from branch updates."""
        if agent_id in self.branch_subscriptions[branch_name]:
            self.branch_subscriptions[branch_name].remove(agent_id)
            self.protocol_stats["subscriptions_active"] -= 1
            logger.info("Agent %s unsubscribed from branch %s", agent_id, branch_name)

    async def request_branch_sync(
        self,
        requester_id: str,
        branch_names: list[str] | None = None,
    ) -> None:
        """Request synchronization of branch information.

        Args:
            requester_id: ID of requesting agent
            branch_names: Specific branches to sync (None for all)
        """
        branches_to_sync = branch_names or list(self.branch_info.keys())

        for branch_name in branches_to_sync:
            if branch_name in self.branch_info:
                branch_info = self.branch_info[branch_name]
                await self._send_branch_update_to_agent(
                    requester_id,
                    branch_info,
                    BranchInfoType.BRANCH_STATE,
                    {"sync_requested": True},
                )

    async def detect_branch_conflicts(self, branch1: str, branch2: str) -> list[str]:
        """Detect potential conflicts between two branches.

        Args:
            branch1: First branch name
            branch2: Second branch name

        Returns:
            List of potential conflict descriptions
        """
        if branch1 not in self.branch_info or branch2 not in self.branch_info:
            return []

        info1 = self.branch_info[branch1]
        info2 = self.branch_info[branch2]

        conflicts = []

        # Check file overlap
        common_files = set(info1.files_modified) & set(info2.files_modified)
        if common_files:
            conflicts.append(f"Both branches modify: {', '.join(common_files)}")

        # Check API changes
        for api_name in info1.api_signatures:
            if api_name in info2.api_signatures and info1.api_signatures[api_name] != info2.api_signatures[api_name]:
                conflicts.append(f"Conflicting API change: {api_name}")

        # Check dependency conflicts
        for dep_file in info1.dependencies:
            if dep_file in info2.files_modified:
                conflicts.append(
                    f"Branch {branch2} modifies dependency of {branch1}: {dep_file}",
                )

        return conflicts

    async def prepare_merge_report(self, branch_name: str) -> dict[str]:
        """Prepare a comprehensive merge readiness report.

        Args:
            branch_name: Branch to analyze

        Returns:
            Merge report with recommendations
        """
        if branch_name not in self.branch_info:
            return {"error": "Branch not found"}

        branch_info = self.branch_info[branch_name]

        # Check various merge criteria
        merge_criteria = {
            "tests_passed": branch_info.tests_passed is True,
            "build_successful": branch_info.build_status == "success",
            "no_conflicts": len(branch_info.conflicts_detected) == 0,
            "work_completed": len(branch_info.work_items) == 0,
        }

        # Calculate merge score
        merge_score = sum(1 for v in merge_criteria.values() if v) / len(merge_criteria)

        # Generate recommendations
        recommendations = []
        if not merge_criteria["tests_passed"]:
            recommendations.append("Fix failing tests before merge")
        if not merge_criteria["build_successful"]:
            recommendations.append("Ensure build passes")
        if not merge_criteria["no_conflicts"]:
            recommendations.append(
                f"Resolve {len(branch_info.conflicts_detected)} conflicts",
            )
        if not merge_criteria["work_completed"]:
            recommendations.append(
                f"Complete {len(branch_info.work_items)} remaining work items",
            )

        # Check for potential conflicts with other branches
        potential_conflicts = {}
        for other_branch in self.branch_info:
            if other_branch != branch_name:
                conflicts = await self.detect_branch_conflicts(
                    branch_name,
                    other_branch,
                )
                if conflicts:
                    potential_conflicts[other_branch] = conflicts

        return {
            "branch_name": branch_name,
            "agent_id": branch_info.agent_id,
            "merge_ready": merge_score == 1.0,
            "merge_score": merge_score,
            "criteria": merge_criteria,
            "recommendations": recommendations,
            "potential_conflicts": potential_conflicts,
            "last_updated": branch_info.last_updated.isoformat(),
            "files_modified": len(branch_info.files_modified),
            "commit_count": branch_info.commit_count,
        }

    # Private methods

    async def _share_branch_info(
        self,
        branch_info: BranchInfo,
        info_type: BranchInfoType,
        event_data: dict[str],
    ) -> None:
        """Share branch information with subscribed agents."""
        # Create sync event
        event = BranchSyncEvent(
            event_id=f"sync_{branch_info.branch_name}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            branch_name=branch_info.branch_name,
            agent_id=branch_info.agent_id,
            event_type=info_type,
            event_data=event_data,
            priority=self._determine_priority(info_type),
            requires_action=info_type
            in {
                BranchInfoType.CONFLICT_INFO,
                BranchInfoType.API_CHANGES,
            },
        )

        self.sync_history.append(event)
        self.protocol_stats["syncs_performed"] += 1

        # Share as knowledge in collaboration engine
        await self.collaboration_engine.share_knowledge(
            contributor_id=branch_info.agent_id,
            knowledge_type=f"branch_info_{info_type.value}",
            content={
                "branch_name": branch_info.branch_name,
                "info_type": info_type.value,
                "data": event_data,
                "branch_state": {
                    "files_modified": branch_info.files_modified,
                    "tests_passed": branch_info.tests_passed,
                    "build_status": branch_info.build_status,
                    "conflicts": branch_info.conflicts_detected,
                },
            },
            tags=["branch_info", branch_info.branch_name, info_type.value],
            relevance_score=self._calculate_relevance(info_type),
        )

        self.protocol_stats["info_shared"] += 1

        # Send targeted messages to subscribed agents
        for subscriber_id in self.branch_subscriptions[branch_info.branch_name]:
            if subscriber_id != branch_info.agent_id:  # Don't send to self
                await self._send_branch_update_to_agent(
                    subscriber_id,
                    branch_info,
                    info_type,
                    event_data,
                )

        logger.info("Shared %s for branch %s", info_type.value, branch_info.branch_name)

    async def _send_branch_update_to_agent(
        self,
        agent_id: str,
        branch_info: BranchInfo,
        info_type: BranchInfoType,
        event_data: dict[str],
    ) -> None:
        """Send branch update to specific agent."""
        message_type = MessageType.STATUS_UPDATE
        if info_type == BranchInfoType.CONFLICT_INFO:
            message_type = MessageType.CONFLICT_ALERT
        elif info_type == BranchInfoType.API_CHANGES:
            message_type = MessageType.DEPENDENCY_CHANGE

        await self.collaboration_engine.send_message(
            sender_id=branch_info.agent_id,
            recipient_id=agent_id,
            message_type=message_type,
            subject=f"Branch update: {branch_info.branch_name} - {info_type.value}",
            content={
                "branch_name": branch_info.branch_name,
                "info_type": info_type.value,
                "event_data": event_data,
                "branch_summary": {
                    "last_updated": branch_info.last_updated.isoformat(),
                    "merge_ready": branch_info.merge_ready,
                    "has_conflicts": len(branch_info.conflicts_detected) > 0,
                },
            },
            priority=self._determine_priority(info_type),
            requires_ack=info_type
            in {
                BranchInfoType.CONFLICT_INFO,
                BranchInfoType.API_CHANGES,
            },
        )

    @staticmethod
    def _determine_priority(info_type: BranchInfoType) -> MessagePriority:
        """Determine message priority based on info type.

        Returns:
        MessagePriority: Description of return value.
        """
        priority_map = {
            BranchInfoType.CONFLICT_INFO: MessagePriority.HIGH,
            BranchInfoType.API_CHANGES: MessagePriority.HIGH,
            BranchInfoType.BUILD_STATUS: MessagePriority.NORMAL,
            BranchInfoType.TEST_STATUS: MessagePriority.NORMAL,
            BranchInfoType.MERGE_READINESS: MessagePriority.NORMAL,
            BranchInfoType.FILE_CHANGES: MessagePriority.LOW,
            BranchInfoType.COMMIT_HISTORY: MessagePriority.LOW,
        }
        return priority_map.get(info_type, MessagePriority.NORMAL)

    @staticmethod
    def _calculate_relevance(info_type: BranchInfoType) -> float:
        """Calculate relevance score for knowledge sharing.

        Returns:
        float: Description of return value.
        """
        relevance_map = {
            BranchInfoType.CONFLICT_INFO: 1.0,
            BranchInfoType.API_CHANGES: 0.9,
            BranchInfoType.MERGE_READINESS: 0.8,
            BranchInfoType.BUILD_STATUS: 0.7,
            BranchInfoType.TEST_STATUS: 0.7,
            BranchInfoType.DEPENDENCY_MAP: 0.6,
            BranchInfoType.FILE_CHANGES: 0.5,
            BranchInfoType.WORK_PROGRESS: 0.5,
            BranchInfoType.COMMIT_HISTORY: 0.4,
            BranchInfoType.BRANCH_STATE: 0.3,
        }
        return relevance_map.get(info_type, 0.5)

    async def _periodic_sync_loop(self) -> None:
        """Background task for periodic synchronization."""
        while self._running:
            try:
                await asyncio.sleep(self.sync_interval)

                # Sync all active branches
                for branch_info in self.branch_info.values():
                    # Check if branch needs sync
                    time_since_update = datetime.now(UTC) - branch_info.last_updated

                    if self.sync_strategy == SyncStrategy.SMART:
                        # Smart sync based on activity
                        if time_since_update < timedelta(minutes=5):
                            # Recent activity, share summary
                            await self._share_branch_info(
                                branch_info,
                                BranchInfoType.BRANCH_STATE,
                                {
                                    "sync_type": "periodic",
                                    "activity_level": "active",
                                },
                            )
                    else:
                        # Regular periodic sync
                        await self._share_branch_info(
                            branch_info,
                            BranchInfoType.BRANCH_STATE,
                            {"sync_type": "periodic"},
                        )

            except Exception:
                logger.exception("Error in periodic sync")

    def get_protocol_summary(self) -> dict[str]:
        """Get comprehensive summary of protocol activity.

        Returns:
        object: Description of return value.
        """
        active_branches = [
            {
                "branch_name": info.branch_name,
                "agent_id": info.agent_id,
                "last_updated": info.last_updated.isoformat(),
                "merge_ready": info.merge_ready,
                "has_conflicts": len(info.conflicts_detected) > 0,
                "files_modified": len(info.files_modified),
                "subscribers": len(self.branch_subscriptions[info.branch_name]),
            }
            for info in self.branch_info.values()
        ]

        recent_syncs = [
            {
                "event_id": event.event_id,
                "branch_name": event.branch_name,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "priority": event.priority.value,
            }
            for event in self.sync_history[-10:]  # Last 10 syncs
        ]

        return {
            "statistics": self.protocol_stats.copy(),
            "active_branches": len(self.branch_info),
            "total_subscriptions": sum(len(subs) for subs in self.branch_subscriptions.values()),
            "sync_strategy": self.sync_strategy.value,
            "branches": active_branches,
            "recent_syncs": recent_syncs,
        }
