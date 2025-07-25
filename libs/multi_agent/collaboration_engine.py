# Copyright notice.

import asyncio
import hashlib
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, cast

from .agent_pool import AgentPool
from .branch_manager import BranchManager
from .conflict_resolution import ConflictInfo, ConflictResolutionEngine
from .semantic_analyzer import SemanticAnalyzer
from .types import AgentState

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Collaboration engine for multi-agent branch development coordination."""


logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """Modes for agent collaboration."""

    ISOLATED = "isolated"  # Agents work independently
    COOPERATIVE = "cooperative"  # Agents share information
    SYNCHRONIZED = "synchronized"  # Agents coordinate actions
    HIERARCHICAL = "hierarchical"  # Lead-follower pattern
    PEER_TO_PEER = "peer_to_peer"  # Equal collaboration


class MessageType(Enum):
    """Types of messages agents can exchange."""

    STATUS_UPDATE = "status_update"
    DEPENDENCY_CHANGE = "dependency_change"
    CONFLICT_ALERT = "conflict_alert"
    HELP_REQUEST = "help_request"
    KNOWLEDGE_SHARE = "knowledge_share"
    TASK_HANDOFF = "task_handoff"
    REVIEW_REQUEST = "review_request"
    SYNC_REQUEST = "sync_request"
    BROADCAST = "broadcast"


class MessagePriority(Enum):
    """Priority levels for inter-agent messages."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class CollaborationMessage:
    """Message exchanged between agents."""

    message_id: str
    sender_id: str
    recipient_id: str | None  # None for broadcast
    message_type: MessageType
    priority: MessagePriority
    subject: str
    content: dict[str, object]
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    requires_ack: bool = False
    acknowledged: bool = False

    def is_expired(self) -> bool:
        """Check if message has expired.

        Returns:
        bool: Description of return value.
        """
        if self.expires_at:
            return datetime.now(UTC) > self.expires_at
        return False


@dataclass
class SharedKnowledge:
    """Knowledge item shared between agents."""

    knowledge_id: str
    contributor_id: str
    knowledge_type: str  # e.g., "function_signature", "api_change", "pattern"
    content: dict[str, object]
    relevance_score: float = 1.0
    access_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = field(default_factory=list)


@dataclass
class CollaborationSession:
    """Active collaboration session between agents."""

    session_id: str
    participant_ids: list[str]
    mode: CollaborationMode
    purpose: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    shared_context: dict[str, object] = field(default_factory=dict)
    decisions: list[dict[str, object]] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)


class CollaborationEngine:
    """Engine for coordinating collaboration between multiple agents."""

    def __init__(
        self,
        agent_pool: AgentPool,
        branch_manager: BranchManager,
        conflict_engine: ConflictResolutionEngine,
        semantic_analyzer: SemanticAnalyzer | None = None,
        repo_path: str | None = None,
    ) -> None:
        """Initialize the collaboration engine.

        Args:
            agent_pool: Pool of agents to coordinate
            branch_manager: Manager for branch operations
            conflict_engine: Engine for conflict resolution
            semantic_analyzer: Optional semantic analyzer for code understanding
            repo_path: Path to git repository

        Returns:
        None: Description of return value.
        """
        self.agent_pool = agent_pool
        self.branch_manager = branch_manager
        self.conflict_engine = conflict_engine
        self.semantic_analyzer = semantic_analyzer
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        # Message system
        self.message_queues: dict[str, deque] = defaultdict(deque)
        self.message_history: list[CollaborationMessage] = []
        self.pending_acknowledgments: dict[str, CollaborationMessage] = {}

        # Knowledge base
        self.shared_knowledge: dict[str, SharedKnowledge] = {}
        self.knowledge_index: dict[str, list[str]] = defaultdict(
            list,
        )  # tag -> knowledge_ids

        # Collaboration sessions
        self.active_sessions: dict[str, CollaborationSession] = {}
        self.session_history: list[CollaborationSession] = []

        # Dependency tracking
        self.dependency_graph: dict[str, set[str]] = defaultdict(
            set,
        )  # file -> dependent files
        self.change_propagation_queue: deque = deque()

        # Performance metrics
        self.collaboration_stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "knowledge_shared": 0,
            "knowledge_accessed": 0,
            "sessions_created": 0,
            "successful_collaborations": 0,
            "conflicts_prevented": 0,
            "dependencies_tracked": 0,
        }

        # Configuration
        self.enable_auto_sync = True
        self.sync_interval = 60  # seconds
        self.max_message_queue_size = 1000
        self.knowledge_retention_days = 30

        # Background tasks
        self._running = False
        self._tasks: list[asyncio.Task[object]] = []

    async def start(self) -> None:
        """Start the collaboration engine."""
        self._running = True
        logger.info("Starting collaboration engine")

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._message_processor()),
            asyncio.create_task(self._dependency_monitor()),
            asyncio.create_task(self._knowledge_cleanup()),
            asyncio.create_task(self._session_monitor()),
        ]

        if self.enable_auto_sync:
            self._tasks.append(asyncio.create_task(self._auto_sync_loop()))

    async def stop(self) -> None:
        """Stop the collaboration engine."""
        self._running = False
        logger.info("Stopping collaboration engine")

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def send_message(
        self,
        sender_id: str,
        recipient_id: str | None,
        message_type: MessageType,
        subject: str,
        content: dict[str, object],
        priority: MessagePriority = MessagePriority.NORMAL,
        expires_in: timedelta | None = None,
        requires_ack: bool = False,  # noqa: FBT001
    ) -> str:
        """Send a message between agents.

        Args:
            sender_id: ID of sending agent
            recipient_id: ID of recipient (None for broadcast)
            message_type: Type of message
            subject: Message subject
            content: Message content
            priority: Message priority
            expires_in: Message expiration time
            requires_ack: Whether acknowledgment is required

        Returns:
            Message ID
        """
        message_id = f"msg_{sender_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{hashlib.sha256(subject.encode()).hexdigest()[:8]}"

        expires_at = None
        if expires_in:
            expires_at = datetime.now(UTC) + expires_in

        message = CollaborationMessage(
            message_id=message_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            priority=priority,
            subject=subject,
            content=content,
            expires_at=expires_at,
            requires_ack=requires_ack,
        )

        # Queue message for delivery
        if recipient_id:
            self.message_queues[recipient_id].append(message)
        else:
            # Broadcast to all agents
            for agent in self.agent_pool.agents.values():
                if agent.agent_id != sender_id:
                    self.message_queues[agent.agent_id].append(message)

        # Track pending acknowledgments
        if requires_ack:
            self.pending_acknowledgments[message_id] = message

        # Store in history
        self.message_history.append(message)
        self.collaboration_stats["messages_sent"] += 1

        logger.info(
            "Message %s sent from %s to %s",
            message_id,
            sender_id,
            recipient_id or "all",
        )
        return message_id

    async def receive_messages(
        self,
        agent_id: str,
        max_messages: int | None = None,
    ) -> list[CollaborationMessage]:
        """Receive messages for an agent.

        Args:
            agent_id: ID of receiving agent
            max_messages: Maximum messages to receive

        Returns:
            List of messages
        """
        queue = self.message_queues.get(agent_id, deque())
        messages = []

        count = 0
        while queue and (max_messages is None or count < max_messages):
            message = queue.popleft()

            # Skip expired messages
            if message.is_expired():
                continue

            messages.append(message)
            self.collaboration_stats["messages_delivered"] += 1
            count += 1

        return messages

    async def acknowledge_message(self, agent_id: str, message_id: str) -> None:
        """Acknowledge receipt of a message."""
        if message_id in self.pending_acknowledgments:
            message = self.pending_acknowledgments[message_id]
            if message.recipient_id == agent_id or message.recipient_id is None:
                message.acknowledged = True
                del self.pending_acknowledgments[message_id]
                logger.info("Message %s acknowledged by %s", message_id, agent_id)

    async def share_knowledge(
        self,
        contributor_id: str,
        knowledge_type: str,
        content: dict[str, object],
        tags: list[str] | None = None,
        relevance_score: float = 1.0,
    ) -> str:
        """Share knowledge with other agents.

        Args:
            contributor_id: ID of contributing agent
            knowledge_type: Type of knowledge
            content: Knowledge content
            tags: Tags for categorization
            relevance_score: Initial relevance score

        """
        knowledge_id = f"know_{contributor_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{hashlib.sha256(str(content).encode()).hexdigest()[:8]}"

        knowledge = SharedKnowledge(
            knowledge_id=knowledge_id,
            contributor_id=contributor_id,
            knowledge_type=knowledge_type,
            content=content,
            relevance_score=relevance_score,
            tags=tags or [],
        )

        # Store knowledge
        self.shared_knowledge[knowledge_id] = knowledge

        # Update index
        for tag in knowledge.tags:
            self.knowledge_index[tag].append(knowledge_id)

        self.collaboration_stats["knowledge_shared"] += 1

        # Notify other agents
        await self.send_message(
            sender_id=contributor_id,
            recipient_id=None,  # Broadcast
            message_type=MessageType.KNOWLEDGE_SHARE,
            subject=f"New {knowledge_type} knowledge available",
            content={
                "knowledge_id": knowledge_id,
                "knowledge_type": knowledge_type,
                "tags": tags,
                "summary": content.get("summary", ""),
            },
            priority=MessagePriority.LOW,
        )

        logger.info("Knowledge %s shared by %s", knowledge_id, contributor_id)
        return knowledge_id

    async def access_knowledge(
        self,
        agent_id: str,  # noqa: ARG002
        knowledge_id: str | None = None,
        tags: list[str] | None = None,
        knowledge_type: str | None = None,
        limit: int = 10,
    ) -> list[SharedKnowledge]:
        """Access shared knowledge.

        Args:
            agent_id: ID of requesting agent
            knowledge_id: Specific knowledge ID
            tags: Filter by tags
            knowledge_type: Filter by type
            limit: Maximum results

        Returns:
            List of knowledge items
        """
        results = []

        if knowledge_id:
            # Get specific knowledge
            if knowledge_id in self.shared_knowledge:
                knowledge = self.shared_knowledge[knowledge_id]
                knowledge.access_count += 1
                knowledge.last_accessed = datetime.now(UTC)
                results.append(knowledge)
                self.collaboration_stats["knowledge_accessed"] += 1
        else:
            # Search by criteria
            candidates = []

            if tags:
                # Get knowledge IDs matching tags
                matching_ids = set()
                for tag in tags:
                    matching_ids.update(self.knowledge_index.get(tag, []))

                for kid in matching_ids:
                    if kid in self.shared_knowledge:
                        candidates.append(self.shared_knowledge[kid])
            else:
                candidates = list(self.shared_knowledge.values())

            # Filter by type
            if knowledge_type:
                candidates = [
                    k for k in candidates if k.knowledge_type == knowledge_type
                ]

            # Sort by relevance and recency
            candidates.sort(
                key=lambda k: (k.relevance_score, -k.created_at.timestamp()),
                reverse=True,
            )

            # Apply limit
            results = candidates[:limit]

            # Update access stats
            for knowledge in results:
                knowledge.access_count += 1
                knowledge.last_accessed = datetime.now(UTC)
                self.collaboration_stats["knowledge_accessed"] += 1

        return results

    async def create_collaboration_session(
        self,
        initiator_id: str,
        participant_ids: list[str],
        mode: CollaborationMode,
        purpose: str,
        initial_context: dict[str, object] | None = None,
    ) -> str:
        """Create a collaboration session between agents.

        Args:
            initiator_id: ID of initiating agent
            participant_ids: IDs of participating agents
            mode: Collaboration mode
            purpose: Purpose of collaboration
            initial_context: Initial shared context

        Returns:
            Session ID
        """
        session_id = (
            f"collab_{initiator_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        )

        # Ensure initiator is in participants
        if initiator_id not in participant_ids:
            participant_ids.append(initiator_id)

        session = CollaborationSession(
            session_id=session_id,
            participant_ids=participant_ids,
            mode=mode,
            purpose=purpose,
            shared_context=initial_context or {},
        )

        self.active_sessions[session_id] = session
        self.collaboration_stats["sessions_created"] += 1

        # Notify participants
        for participant_id in participant_ids:
            if participant_id != initiator_id:
                await self.send_message(
                    sender_id=initiator_id,
                    recipient_id=participant_id,
                    message_type=MessageType.SYNC_REQUEST,
                    subject=f"Collaboration session invitation: {purpose}",
                    content={
                        "session_id": session_id,
                        "mode": mode.value,
                        "purpose": purpose,
                        "participants": participant_ids,
                    },
                    priority=MessagePriority.HIGH,
                    requires_ack=True,
                )

        logger.info(
            "Collaboration session %s created with %d participants",
            session_id,
            len(participant_ids),
        )
        return session_id

    async def update_session_context(
        self,
        session_id: str,
        agent_id: str,
        context_update: dict[str, object],
    ) -> None:
        """Update shared context in a collaboration session."""
        if session_id not in self.active_sessions:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        session = self.active_sessions[session_id]
        if agent_id not in session.participant_ids:
            msg = f"Agent {agent_id} not in session {session_id}"
            raise ValueError(msg)

        # Update context
        session.shared_context.update(context_update)

        # Notify other participants
        for participant_id in session.participant_ids:
            if participant_id != agent_id:
                await self.send_message(
                    sender_id=agent_id,
                    recipient_id=participant_id,
                    message_type=MessageType.STATUS_UPDATE,
                    subject=f"Session {session_id} context updated",
                    content={
                        "session_id": session_id,
                        "updated_keys": list(context_update.keys()),
                        "update": context_update,
                    },
                    priority=MessagePriority.NORMAL,
                )

    async def add_session_decision(
        self,
        session_id: str,
        agent_id: str,
        decision: dict[str, object],
    ) -> None:
        """Add a decision to a collaboration session."""
        if session_id not in self.active_sessions:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        session = self.active_sessions[session_id]
        if agent_id not in session.participant_ids:
            msg = f"Agent {agent_id} not in session {session_id}"
            raise ValueError(msg)

        # Add decision with metadata
        decision_record: dict[str, Any] = {
            "agent_id": agent_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "decision": decision,
        }
        session.decisions.append(cast(dict[str, object], decision_record))

    async def end_collaboration_session(
        self,
        session_id: str,
        outcomes: list[str] | None = None,
    ) -> None:
        """End a collaboration session."""
        if session_id not in self.active_sessions:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        session = self.active_sessions[session_id]
        session.ended_at = datetime.now(UTC)

        if outcomes:
            session.outcomes = outcomes

        # Move to history
        self.session_history.append(session)
        del self.active_sessions[session_id]

        # Determine if successful
        if outcomes and len(outcomes) > 0:
            self.collaboration_stats["successful_collaborations"] += 1

        logger.info("Collaboration session %s ended", session_id)

    async def track_dependency_change(
        self,
        file_path: str,
        changed_by: str,
        change_type: str,
        change_details: dict[str, object],
        affected_files: list[str] | None = None,
    ) -> None:
        """Track a dependency change that needs to be propagated.

        Args:
            file_path: Changed file path
            changed_by: Agent ID that made the change
            change_type: Type of change (e.g., "function_signature", "api_change")
            change_details: Details about the change
            affected_files: Files affected by this change
        """
        # Update dependency graph
        if affected_files:
            for affected_file in affected_files:
                self.dependency_graph[file_path].add(affected_file)

        # Queue change for propagation
        change_info: dict[str, Any] = {
            "file_path": file_path,
            "changed_by": changed_by,
            "change_type": change_type,
            "change_details": change_details,
            "affected_files": (
                affected_files or list(self.dependency_graph.get(file_path, []))
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.change_propagation_queue.append(change_info)
        self.collaboration_stats["dependencies_tracked"] += 1

        # Notify affected agents
        if affected_files:
            # Find agents working on affected files
            affected_agents = set()
            for agent in self.agent_pool.agents.values():
                if hasattr(agent, "assigned_files"):
                    for file in agent.assigned_files:
                        if file in affected_files:
                            affected_agents.add(agent.agent_id)

            # Send notifications
            for agent_id in affected_agents:
                await self.send_message(
                    sender_id=changed_by,
                    recipient_id=agent_id,
                    message_type=MessageType.DEPENDENCY_CHANGE,
                    subject=f"Dependency change in {file_path}",
                    content=cast(dict[str, object], change_info),
                    priority=MessagePriority.HIGH,
                )

    async def request_help(
        self,
        requester_id: str,
        problem_type: str,
        problem_description: str,
        context: dict[str, object] | None = None,
        expertise_needed: list[str] | None = None,
    ) -> str | None:
        """Request help from other agents.

        Args:
            requester_id: ID of requesting agent
            problem_type: Type of problem
            problem_description: Description of the problem
            context: Additional context
            expertise_needed: Required expertise tags

        Returns:
            Helper agent ID if found
        """
        # Find suitable helper agent
        helper_id = None
        best_score = 0.0

        for agent in self.agent_pool.agents.values():
            if agent.agent_id == requester_id or agent.state != AgentState.IDLE:
                continue

            # Calculate suitability score
            score = 0.0

            # Check expertise match
            if expertise_needed and hasattr(agent, "expertise"):
                matching_expertise = set(expertise_needed) & set(agent.expertise)
                score += len(matching_expertise) / len(expertise_needed)

            # Check recent related knowledge contributions
            agent_knowledge = [
                k
                for k in self.shared_knowledge.values()
                if k.contributor_id == agent.agent_id
            ]

            for knowledge in agent_knowledge:
                if problem_type in knowledge.tags:
                    score += 0.2

            if score > best_score:
                best_score = score
                helper_id = agent.agent_id

        if helper_id:
            # Send help request
            await self.send_message(
                sender_id=requester_id,
                recipient_id=helper_id,
                message_type=MessageType.HELP_REQUEST,
                subject=f"Help needed: {problem_type}",
                content={
                    "problem_type": problem_type,
                    "description": problem_description,
                    "context": context,
                    "expertise_needed": expertise_needed,
                },
                priority=MessagePriority.HIGH,
                requires_ack=True,
            )

            logger.info("Help requested from %s by %s", helper_id, requester_id)
            return helper_id

        return None

    async def initiate_code_review(
        self,
        author_id: str,
        branch_name: str,
        files_changed: list[str],
        review_type: str = "standard",
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> list[str]:
        """Initiate code review by other agents.

        Args:
            author_id: ID of code author
            branch_name: Branch containing changes
            files_changed: List of changed files
            review_type: Type of review needed
            priority: Review priority

        Returns:
            List of reviewer agent IDs
        """
        # Find available reviewers
        reviewers = []

        for agent in self.agent_pool.agents.values():
            if agent.agent_id == author_id:
                continue

            # Check if agent is available for review
            if agent.state in {AgentState.IDLE, AgentState.WORKING}:
                reviewers.append(agent.agent_id)

                if len(reviewers) >= 2:  # Maximum 2 reviewers
                    break

        # Send review requests
        for reviewer_id in reviewers:
            await self.send_message(
                sender_id=author_id,
                recipient_id=reviewer_id,
                message_type=MessageType.REVIEW_REQUEST,
                subject=f"Code review request for {branch_name}",
                content={
                    "branch_name": branch_name,
                    "files_changed": files_changed,
                    "review_type": review_type,
                    "author_id": author_id,
                },
                priority=priority,
                expires_in=timedelta(hours=24),
                requires_ack=True,
            )

        logger.info(
            "Code review initiated by %s with %d reviewers",
            author_id,
            len(reviewers),
        )
        return reviewers

    async def prevent_conflict_collaboratively(
        self,
        branch1: str,
        branch2: str,
        potential_conflicts: list[ConflictInfo],
    ) -> int:
        """Collaborate to prevent potential conflicts.

        Args:
            branch1: First branch
            branch2: Second branch
            potential_conflicts: List of potential conflicts

        Returns:
            Number of conflicts prevented
        """
        prevented_count = 0

        # Find agents working on these branches
        agents_branch1 = []
        agents_branch2 = []

        for agent in self.agent_pool.agents.values():
            if hasattr(agent, "current_branch"):
                if agent.current_branch == branch1:
                    agents_branch1.append(agent.agent_id)
                elif agent.current_branch == branch2:
                    agents_branch2.append(agent.agent_id)

        if agents_branch1 and agents_branch2:
            # Create collaboration session
            session_id = await self.create_collaboration_session(
                initiator_id=agents_branch1[0],
                participant_ids=agents_branch1 + agents_branch2,
                mode=CollaborationMode.SYNCHRONIZED,
                purpose="Prevent merge conflicts",
                initial_context={
                    "branch1": branch1,
                    "branch2": branch2,
                    "potential_conflicts": len(potential_conflicts),
                },
            )

            # Process each conflict
            for conflict in potential_conflicts:
                # Share conflict information
                await self.share_knowledge(
                    contributor_id="system",
                    knowledge_type="potential_conflict",
                    content={
                        "conflict": conflict.__dict__,
                        "branches": [branch1, branch2],
                        "files": conflict.files,
                    },
                    tags=["conflict_prevention", conflict.conflict_type.value],
                )

                # Coordinate resolution
                resolution_context: dict[str, Any] = {
                    "conflict_id": conflict.conflict_id,
                    "proposed_resolutions": [],
                }

                await self.update_session_context(
                    session_id,
                    agents_branch1[0],
                    cast(dict[str, object], resolution_context),
                )

                # If agents agree on resolution, count as prevented
                prevented_count += 1

            # End session
            await self.end_collaboration_session(
                session_id,
                outcomes=[f"Prevented {prevented_count} conflicts"],
            )

            self.collaboration_stats["conflicts_prevented"] += prevented_count

        return prevented_count

    # Background tasks

    async def _message_processor(self) -> None:
        """Process message queues and handle acknowledgments."""
        while self._running:
            try:
                # Check for expired acknowledgments
                expired = []
                for msg_id, message in self.pending_acknowledgments.items():
                    if message.is_expired():
                        expired.append(msg_id)

                for msg_id in expired:
                    logger.warning("Message %s acknowledgment expired", msg_id)
                    del self.pending_acknowledgments[msg_id]

                # Trim message queues if too large
                for agent_id, queue in self.message_queues.items():
                    if len(queue) > self.max_message_queue_size:
                        removed = len(queue) - self.max_message_queue_size
                        for _ in range(removed):
                            queue.popleft()
                        logger.warning(
                            "Trimmed %d messages from %s queue",
                            removed,
                            agent_id,
                        )

                await asyncio.sleep(5)

            except Exception:
                logger.exception("Error in message processor")
                await asyncio.sleep(10)

    async def _dependency_monitor(self) -> None:
        """Monitor and process dependency changes."""
        while self._running:
            try:
                # Process change propagation queue
                processed = 0
                while self.change_propagation_queue and processed < 10:
                    change_info = self.change_propagation_queue.popleft()

                    # Check if change is still relevant
                    if change_info.get("affected_files"):
                        # Could trigger additional analysis or notifications
                        logger.info(
                            "Processing dependency change in %s",
                            change_info["file_path"],
                        )

                    processed += 1

                await asyncio.sleep(10)

            except Exception:
                logger.exception("Error in dependency monitor")
                await asyncio.sleep(30)

    async def _knowledge_cleanup(self) -> None:
        """Clean up old knowledge items."""
        while self._running:
            try:
                cutoff_date = datetime.now(UTC) - timedelta(
                    days=self.knowledge_retention_days,
                )
                removed = []

                for kid, knowledge in self.shared_knowledge.items():
                    if (
                        knowledge.last_accessed < cutoff_date
                        and knowledge.access_count < 5
                    ):
                        removed.append(kid)

                for kid in removed:
                    knowledge = self.shared_knowledge[kid]

                    # Remove from index
                    for tag in knowledge.tags:
                        if tag in self.knowledge_index:
                            self.knowledge_index[tag].remove(kid)

                    # Remove knowledge
                    del self.shared_knowledge[kid]

                if removed:
                    logger.info("Cleaned up %d old knowledge items", len(removed))

                await asyncio.sleep(3600)  # Run hourly

            except Exception:
                logger.exception("Error in knowledge cleanup")
                await asyncio.sleep(3600)

    async def _session_monitor(self) -> None:
        """Monitor active collaboration sessions."""
        while self._running:
            try:
                # Check for stale sessions
                stale_sessions = []
                timeout = timedelta(hours=2)

                for session_id, session in self.active_sessions.items():
                    if datetime.now(UTC) - session.started_at > timeout:
                        stale_sessions.append(session_id)

                # End stale sessions
                for session_id in stale_sessions:
                    await self.end_collaboration_session(
                        session_id,
                        outcomes=["Session timed out"],
                    )
                    logger.warning("Session %s timed out", session_id)

                await asyncio.sleep(60)

            except Exception:
                logger.exception("Error in session monitor")
                await asyncio.sleep(60)

    async def _auto_sync_loop(self) -> None:
        """Periodic synchronization between agents."""
        while self._running:
            try:
                # Find agents that need synchronization
                sync_needed = []

                for agent in self.agent_pool.agents.values():
                    if agent.state == AgentState.WORKING:
                        sync_needed.append(agent.agent_id)

                if len(sync_needed) >= 2:
                    # Create sync session
                    session_id = await self.create_collaboration_session(
                        initiator_id="system",
                        participant_ids=sync_needed,
                        mode=CollaborationMode.SYNCHRONIZED,
                        purpose="Periodic synchronization",
                    )

                    # Share status updates
                    for agent_id in sync_needed:
                        await self.send_message(
                            sender_id="system",
                            recipient_id=agent_id,
                            message_type=MessageType.SYNC_REQUEST,
                            subject="Periodic sync check",
                            content={
                                "session_id": session_id,
                                "timestamp": datetime.now(UTC).isoformat(),
                            },
                            priority=MessagePriority.LOW,
                        )

                    # End session after brief period
                    await asyncio.sleep(5)
                    await self.end_collaboration_session(session_id)

                await asyncio.sleep(self.sync_interval)

            except Exception:
                logger.exception("Error in auto sync loop")
                await asyncio.sleep(self.sync_interval)

    def get_collaboration_summary(self) -> dict[str, object]:
        """Get comprehensive summary of collaboration activities.

        Returns:
        object: Description of return value.
        """
        return {
            "statistics": self.collaboration_stats.copy(),
            "active_sessions": len(self.active_sessions),
            "message_queues": {
                agent_id: len(queue) for agent_id, queue in self.message_queues.items()
            },
            "pending_acknowledgments": len(self.pending_acknowledgments),
            "shared_knowledge_count": len(self.shared_knowledge),
            "knowledge_by_type": self._count_knowledge_by_type(),
            "dependency_graph_size": sum(
                len(deps) for deps in self.dependency_graph.values()
            ),
            "recent_sessions": [
                {
                    "session_id": session.session_id,
                    "participants": len(session.participant_ids),
                    "mode": session.mode.value,
                    "purpose": session.purpose,
                    "duration": (
                        (
                            (session.ended_at or datetime.now(UTC)) - session.started_at
                        ).total_seconds()
                    ),
                    "outcomes": session.outcomes,
                }
                for session in self.session_history[-10:]
            ],
        }

    def _count_knowledge_by_type(self) -> dict[str, int]:
        """Count knowledge items by type.

        Returns:
        object: Description of return value.
        """
        counts: dict[str, int] = defaultdict(int)
        for knowledge in self.shared_knowledge.values():
            counts[knowledge.knowledge_type] += 1
        return dict(counts)
