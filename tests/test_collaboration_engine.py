"""Tests for CollaborationEngine multi-agent coordination system."""

from collections import deque
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from libs.multi_agent.agent_pool import AgentPool
from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.collaboration_engine import (
    CollaborationEngine,
    CollaborationMessage,
    CollaborationMode,
    CollaborationSession,
    MessagePriority,
    MessageType,
    SharedKnowledge,
)
from libs.multi_agent.conflict_resolution import ConflictResolutionEngine
from libs.multi_agent.semantic_analyzer import SemanticAnalyzer
from libs.multi_agent.types import AgentState


class TestCollaborationMessage:
    """Test cases for CollaborationMessage."""

    def test_init(self):
        """Test CollaborationMessage initialization."""
        message = CollaborationMessage(
            message_id="test-msg-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.HIGH,
            subject="Test subject",
            content={"status": "working"},
            requires_ack=True,
        )

        assert message.message_id == "test-msg-1"
        assert message.sender_id == "agent-1"
        assert message.recipient_id == "agent-2"
        assert message.message_type == MessageType.STATUS_UPDATE
        assert message.priority == MessagePriority.HIGH
        assert message.subject == "Test subject"
        assert message.content == {"status": "working"}
        assert message.requires_ack is True
        assert message.acknowledged is False
        assert isinstance(message.created_at, datetime)

    def test_is_expired(self):
        """Test message expiration check."""
        # Non-expiring message
        message1 = CollaborationMessage(
            message_id="test-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.NORMAL,
            subject="Test",
            content={},
        )
        assert message1.is_expired() is False

        # Expired message
        message2 = CollaborationMessage(
            message_id="test-2",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.NORMAL,
            subject="Test",
            content={},
            expires_at=datetime.now() - timedelta(seconds=1),
        )
        assert message2.is_expired() is True

        # Future expiration
        message3 = CollaborationMessage(
            message_id="test-3",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            priority=MessagePriority.NORMAL,
            subject="Test",
            content={},
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert message3.is_expired() is False


class TestSharedKnowledge:
    """Test cases for SharedKnowledge."""

    def test_init(self):
        """Test SharedKnowledge initialization."""
        knowledge = SharedKnowledge(
            knowledge_id="know-1",
            contributor_id="agent-1",
            knowledge_type="function_signature",
            content={"function": "test_func", "args": ["x", "y"]},
            relevance_score=0.9,
            tags=["api", "function"],
        )

        assert knowledge.knowledge_id == "know-1"
        assert knowledge.contributor_id == "agent-1"
        assert knowledge.knowledge_type == "function_signature"
        assert knowledge.content == {"function": "test_func", "args": ["x", "y"]}
        assert knowledge.relevance_score == 0.9
        assert knowledge.access_count == 0
        assert knowledge.tags == ["api", "function"]
        assert isinstance(knowledge.created_at, datetime)
        assert isinstance(knowledge.last_accessed, datetime)


class TestCollaborationSession:
    """Test cases for CollaborationSession."""

    def test_init(self):
        """Test CollaborationSession initialization."""
        session = CollaborationSession(
            session_id="session-1",
            participant_ids=["agent-1", "agent-2", "agent-3"],
            mode=CollaborationMode.COOPERATIVE,
            purpose="Code review",
            shared_context={"branch": "feature-x"},
        )

        assert session.session_id == "session-1"
        assert session.participant_ids == ["agent-1", "agent-2", "agent-3"]
        assert session.mode == CollaborationMode.COOPERATIVE
        assert session.purpose == "Code review"
        assert session.shared_context == {"branch": "feature-x"}
        assert isinstance(session.started_at, datetime)
        assert session.ended_at is None
        assert session.decisions == []
        assert session.outcomes == []


class TestCollaborationEngine:
    """Test cases for CollaborationEngine."""

    @pytest.fixture
    def mock_agent_pool(self):
        """Create mock agent pool."""
        pool = Mock(spec=AgentPool)
        pool.agents = {
            "agent-1": Mock(id="agent-1", state=AgentState.IDLE),
            "agent-2": Mock(id="agent-2", state=AgentState.WORKING),
            "agent-3": Mock(id="agent-3", state=AgentState.IDLE),
        }
        return pool

    @pytest.fixture
    def mock_branch_manager(self):
        """Create mock branch manager."""
        return Mock(spec=BranchManager)

    @pytest.fixture
    def mock_conflict_engine(self):
        """Create mock conflict resolution engine."""
        return Mock(spec=ConflictResolutionEngine)

    @pytest.fixture
    def mock_semantic_analyzer(self):
        """Create mock semantic analyzer."""
        return Mock(spec=SemanticAnalyzer)

    @pytest.fixture
    def engine(
        self,
        mock_agent_pool,
        mock_branch_manager,
        mock_conflict_engine,
        mock_semantic_analyzer,
    ):
        """Create CollaborationEngine instance."""
        return CollaborationEngine(
            agent_pool=mock_agent_pool,
            branch_manager=mock_branch_manager,
            conflict_engine=mock_conflict_engine,
            semantic_analyzer=mock_semantic_analyzer,
        )

    def test_init(
        self,
        engine,
        mock_agent_pool,
        mock_branch_manager,
        mock_conflict_engine,
        mock_semantic_analyzer,
    ):
        """Test CollaborationEngine initialization."""
        assert engine.agent_pool == mock_agent_pool
        assert engine.branch_manager == mock_branch_manager
        assert engine.conflict_engine == mock_conflict_engine
        assert engine.semantic_analyzer == mock_semantic_analyzer
        assert isinstance(engine.message_queues, dict)
        assert engine.message_history == []
        assert engine.pending_acknowledgments == {}
        assert engine.shared_knowledge == {}
        assert isinstance(engine.knowledge_index, dict)
        assert engine.active_sessions == {}
        assert engine.session_history == []
        assert isinstance(engine.dependency_graph, dict)
        assert isinstance(engine.change_propagation_queue, deque)
        assert engine.enable_auto_sync is True
        assert engine.sync_interval == 60
        assert engine._running is False
        assert engine._tasks == []

    @pytest.mark.asyncio
    async def test_start_stop(self, engine):
        """Test starting and stopping the engine."""
        # Start engine
        await engine.start()
        assert engine._running is True
        assert len(engine._tasks) >= 4  # At least 4 background tasks

        # Stop engine
        await engine.stop()
        assert engine._running is False
        assert len(engine._tasks) == 0

    @pytest.mark.asyncio
    async def test_send_message_unicast(self, engine):
        """Test sending a unicast message."""
        message_id = await engine.send_message(
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            subject="Test message",
            content={"status": "ready"},
            priority=MessagePriority.HIGH,
            requires_ack=True,
        )

        assert message_id.startswith("msg_agent-1_")
        assert len(engine.message_queues["agent-2"]) == 1
        assert len(engine.message_history) == 1
        assert message_id in engine.pending_acknowledgments
        assert engine.collaboration_stats["messages_sent"] == 1

        # Check message content
        queued_message = engine.message_queues["agent-2"][0]
        assert queued_message.sender_id == "agent-1"
        assert queued_message.recipient_id == "agent-2"
        assert queued_message.subject == "Test message"
        assert queued_message.content == {"status": "ready"}
        assert queued_message.priority == MessagePriority.HIGH
        assert queued_message.requires_ack is True

    @pytest.mark.asyncio
    async def test_send_message_broadcast(self, engine):
        """Test sending a broadcast message."""
        message_id = await engine.send_message(
            sender_id="agent-1",
            recipient_id=None,  # Broadcast
            message_type=MessageType.BROADCAST,
            subject="Broadcast message",
            content={"announcement": "sync required"},
            priority=MessagePriority.NORMAL,
        )

        # Should be queued for all agents except sender
        assert len(engine.message_queues["agent-2"]) == 1
        assert len(engine.message_queues["agent-3"]) == 1
        assert "agent-1" not in engine.message_queues or len(engine.message_queues["agent-1"]) == 0

    @pytest.mark.asyncio
    async def test_receive_messages(self, engine):
        """Test receiving messages for an agent."""
        # Queue some messages
        await engine.send_message(
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            subject="Message 1",
            content={"msg": "1"},
        )
        await engine.send_message(
            sender_id="agent-3",
            recipient_id="agent-2",
            message_type=MessageType.HELP_REQUEST,
            subject="Message 2",
            content={"msg": "2"},
        )

        # Receive all messages
        messages = await engine.receive_messages("agent-2")
        assert len(messages) == 2
        assert messages[0].subject == "Message 1"
        assert messages[1].subject == "Message 2"
        assert engine.collaboration_stats["messages_delivered"] == 2

        # Queue should be empty now
        assert len(engine.message_queues["agent-2"]) == 0

        # Test max_messages limit
        await engine.send_message(
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            subject="Message 3",
            content={},
        )
        await engine.send_message(
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            subject="Message 4",
            content={},
        )

        messages = await engine.receive_messages("agent-2", max_messages=1)
        assert len(messages) == 1
        assert len(engine.message_queues["agent-2"]) == 1  # One message left

    @pytest.mark.asyncio
    async def test_acknowledge_message(self, engine):
        """Test message acknowledgment."""
        message_id = await engine.send_message(
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.HELP_REQUEST,
            subject="Need help",
            content={},
            requires_ack=True,
        )

        assert message_id in engine.pending_acknowledgments

        # Acknowledge the message
        await engine.acknowledge_message("agent-2", message_id)
        assert message_id not in engine.pending_acknowledgments

        # Check that the message was marked as acknowledged
        message = engine.message_history[-1]
        assert message.acknowledged is True

    @pytest.mark.asyncio
    async def test_share_knowledge(self, engine):
        """Test knowledge sharing."""
        knowledge_id = await engine.share_knowledge(
            contributor_id="agent-1",
            knowledge_type="function_signature",
            content={
                "function": "process_data",
                "args": ["data", "options"],
                "return_type": "DataFrame",
                "summary": "Processes input data",
            },
            tags=["data_processing", "api"],
            relevance_score=0.8,
        )

        assert knowledge_id.startswith("know_agent-1_")
        assert knowledge_id in engine.shared_knowledge
        assert engine.collaboration_stats["knowledge_shared"] == 1

        # Check knowledge content
        knowledge = engine.shared_knowledge[knowledge_id]
        assert knowledge.contributor_id == "agent-1"
        assert knowledge.knowledge_type == "function_signature"
        assert knowledge.relevance_score == 0.8
        assert "data_processing" in knowledge.tags
        assert "api" in knowledge.tags

        # Check index
        assert knowledge_id in engine.knowledge_index["data_processing"]
        assert knowledge_id in engine.knowledge_index["api"]

        # Check broadcast notification
        assert len(engine.message_queues["agent-2"]) == 1
        assert len(engine.message_queues["agent-3"]) == 1

    @pytest.mark.asyncio
    async def test_access_knowledge_by_id(self, engine):
        """Test accessing specific knowledge by ID."""
        # Share some knowledge
        knowledge_id = await engine.share_knowledge(
            contributor_id="agent-1",
            knowledge_type="pattern",
            content={"pattern": "singleton", "example": "..."},
            tags=["design_pattern"],
        )

        # Access by ID
        results = await engine.access_knowledge("agent-2", knowledge_id=knowledge_id)
        assert len(results) == 1
        assert results[0].knowledge_id == knowledge_id
        assert results[0].access_count == 1
        assert engine.collaboration_stats["knowledge_accessed"] == 1

    @pytest.mark.asyncio
    async def test_access_knowledge_by_tags(self, engine):
        """Test accessing knowledge by tags."""
        # Share multiple knowledge items
        await engine.share_knowledge(
            contributor_id="agent-1",
            knowledge_type="pattern",
            content={"pattern": "singleton"},
            tags=["design_pattern", "creational"],
        )
        await engine.share_knowledge(
            contributor_id="agent-2",
            knowledge_type="pattern",
            content={"pattern": "factory"},
            tags=["design_pattern", "creational"],
        )
        await engine.share_knowledge(
            contributor_id="agent-3",
            knowledge_type="algorithm",
            content={"algorithm": "quicksort"},
            tags=["algorithm", "sorting"],
        )

        # Access by tags
        results = await engine.access_knowledge(
            "agent-1",
            tags=["design_pattern"],
            limit=10,
        )
        assert len(results) == 2
        assert all(k.knowledge_type == "pattern" for k in results)

        # Access by multiple tags
        results = await engine.access_knowledge(
            "agent-1",
            tags=["creational"],
            limit=10,
        )
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_access_knowledge_by_type(self, engine):
        """Test accessing knowledge by type."""
        # Share different types of knowledge
        await engine.share_knowledge(
            contributor_id="agent-1",
            knowledge_type="function_signature",
            content={"function": "func1"},
        )
        await engine.share_knowledge(
            contributor_id="agent-2",
            knowledge_type="function_signature",
            content={"function": "func2"},
        )
        await engine.share_knowledge(
            contributor_id="agent-3",
            knowledge_type="api_change",
            content={"api": "changed"},
        )

        # Access by type
        results = await engine.access_knowledge(
            "agent-1",
            knowledge_type="function_signature",
            limit=10,
        )
        assert len(results) == 2
        assert all(k.knowledge_type == "function_signature" for k in results)

    @pytest.mark.asyncio
    async def test_create_collaboration_session(self, engine):
        """Test creating a collaboration session."""
        session_id = await engine.create_collaboration_session(
            initiator_id="agent-1",
            participant_ids=["agent-1", "agent-2"],
            mode=CollaborationMode.SYNCHRONIZED,
            purpose="Merge coordination",
            initial_context={"branch": "feature-x", "conflicts": 3},
        )

        assert session_id.startswith("collab_agent-1_")
        assert session_id in engine.active_sessions
        assert engine.collaboration_stats["sessions_created"] == 1

        # Check session content
        session = engine.active_sessions[session_id]
        assert "agent-1" in session.participant_ids
        assert "agent-2" in session.participant_ids
        assert session.mode == CollaborationMode.SYNCHRONIZED
        assert session.purpose == "Merge coordination"
        assert session.shared_context["branch"] == "feature-x"
        assert session.shared_context["conflicts"] == 3

        # Check invitation messages
        messages = list(engine.message_queues["agent-2"])
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.SYNC_REQUEST
        assert messages[0].requires_ack is True

    @pytest.mark.asyncio
    async def test_update_session_context(self, engine):
        """Test updating collaboration session context."""
        # Create session
        session_id = await engine.create_collaboration_session(
            initiator_id="agent-1",
            participant_ids=["agent-1", "agent-2", "agent-3"],
            mode=CollaborationMode.COOPERATIVE,
            purpose="Code review",
        )

        # Update context
        await engine.update_session_context(
            session_id,
            "agent-1",
            {"review_status": "in_progress", "issues_found": 2},
        )

        session = engine.active_sessions[session_id]
        assert session.shared_context["review_status"] == "in_progress"
        assert session.shared_context["issues_found"] == 2

        # Check notifications to other participants
        assert len(engine.message_queues["agent-2"]) == 2  # Invitation + update
        assert len(engine.message_queues["agent-3"]) == 2

    @pytest.mark.asyncio
    async def test_add_session_decision(self, engine):
        """Test adding decisions to a session."""
        # Create session
        session_id = await engine.create_collaboration_session(
            initiator_id="agent-1",
            participant_ids=["agent-1", "agent-2"],
            mode=CollaborationMode.COOPERATIVE,
            purpose="API design",
        )

        # Add decision
        decision = {
            "type": "api_change",
            "description": "Add new parameter to function",
            "approved": True,
        }
        await engine.add_session_decision(session_id, "agent-1", decision)

        session = engine.active_sessions[session_id]
        assert len(session.decisions) == 1
        assert session.decisions[0]["agent_id"] == "agent-1"
        assert session.decisions[0]["decision"] == decision
        assert "timestamp" in session.decisions[0]

    @pytest.mark.asyncio
    async def test_end_collaboration_session(self, engine):
        """Test ending a collaboration session."""
        # Create session
        session_id = await engine.create_collaboration_session(
            initiator_id="agent-1",
            participant_ids=["agent-1", "agent-2"],
            mode=CollaborationMode.SYNCHRONIZED,
            purpose="Conflict resolution",
        )

        # End session with outcomes
        outcomes = ["Resolved 3 conflicts", "Merged successfully"]
        await engine.end_collaboration_session(session_id, outcomes)

        assert session_id not in engine.active_sessions
        assert len(engine.session_history) == 1
        assert engine.collaboration_stats["successful_collaborations"] == 1

        # Check session in history
        historical_session = engine.session_history[0]
        assert historical_session.session_id == session_id
        assert historical_session.outcomes == outcomes
        assert historical_session.ended_at is not None

    @pytest.mark.asyncio
    async def test_track_dependency_change(self, engine):
        """Test tracking dependency changes."""
        await engine.track_dependency_change(
            file_path="module/api.py",
            changed_by="agent-1",
            change_type="function_signature",
            change_details={
                "function": "process_data",
                "old_signature": "process_data(data)",
                "new_signature": "process_data(data, options=None)",
            },
            affected_files=["module/client.py", "tests/test_api.py"],
        )

        # Check dependency graph
        assert "module/client.py" in engine.dependency_graph["module/api.py"]
        assert "tests/test_api.py" in engine.dependency_graph["module/api.py"]
        assert engine.collaboration_stats["dependencies_tracked"] == 1

        # Check change propagation queue
        assert len(engine.change_propagation_queue) == 1
        change_info = engine.change_propagation_queue[0]
        assert change_info["file_path"] == "module/api.py"
        assert change_info["changed_by"] == "agent-1"
        assert change_info["change_type"] == "function_signature"

    @pytest.mark.asyncio
    async def test_request_help(self, engine):
        """Test help request functionality."""
        # Setup agent with expertise
        engine.agent_pool.agents["agent-3"].expertise = ["algorithms", "optimization"]

        helper_id = await engine.request_help(
            requester_id="agent-1",
            problem_type="optimization",
            problem_description="Need to optimize sorting algorithm",
            context={"current_complexity": "O(n^2)"},
            expertise_needed=["algorithms", "optimization"],
        )

        assert helper_id == "agent-3"

        # Check help request message
        messages = list(engine.message_queues["agent-3"])
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.HELP_REQUEST
        assert messages[0].priority == MessagePriority.HIGH
        assert messages[0].requires_ack is True

    @pytest.mark.asyncio
    async def test_initiate_code_review(self, engine):
        """Test code review initiation."""
        reviewers = await engine.initiate_code_review(
            author_id="agent-1",
            branch_name="feature-xyz",
            files_changed=["src/main.py", "src/utils.py", "tests/test_main.py"],
            review_type="standard",
            priority=MessagePriority.HIGH,
        )

        assert len(reviewers) <= 2  # Maximum 2 reviewers
        assert "agent-1" not in reviewers  # Author not included

        # Check review request messages
        for reviewer_id in reviewers:
            messages = list(engine.message_queues[reviewer_id])
            assert any(msg.message_type == MessageType.REVIEW_REQUEST for msg in messages)

    @pytest.mark.asyncio
    async def test_prevent_conflict_collaboratively(self, engine):
        """Test collaborative conflict prevention."""
        # Setup agents with branches
        engine.agent_pool.agents["agent-1"].current_branch = "feature-a"
        engine.agent_pool.agents["agent-2"].current_branch = "feature-b"

        # Create mock conflicts
        mock_conflicts = [
            Mock(
                conflict_id="conflict-1",
                file_path="src/main.py",
                conflict_type=Mock(value="function_conflict"),
                __dict__={
                    "conflict_id": "conflict-1",
                    "file_path": "src/main.py",
                    "conflict_type": Mock(value="function_conflict"),
                },
            ),
        ]

        prevented = await engine.prevent_conflict_collaboratively(
            "feature-a",
            "feature-b",
            mock_conflicts,
        )

        assert prevented == 1  # One conflict prevented
        assert engine.collaboration_stats["conflicts_prevented"] == 1
        assert len(engine.shared_knowledge) > 0  # Knowledge was shared

    def test_get_collaboration_summary(self, engine):
        """Test getting collaboration summary."""
        # Add some test data
        engine.collaboration_stats["messages_sent"] = 50
        engine.collaboration_stats["messages_delivered"] = 45
        engine.collaboration_stats["knowledge_shared"] = 10
        engine.collaboration_stats["sessions_created"] = 5

        # Add some messages to queues
        engine.message_queues["agent-1"].append(Mock())
        engine.message_queues["agent-2"].extend([Mock(), Mock()])

        # Add some knowledge
        engine.shared_knowledge["k1"] = Mock(knowledge_type="pattern")
        engine.shared_knowledge["k2"] = Mock(knowledge_type="pattern")
        engine.shared_knowledge["k3"] = Mock(knowledge_type="api_change")

        summary = engine.get_collaboration_summary()

        assert summary["statistics"]["messages_sent"] == 50
        assert summary["statistics"]["messages_delivered"] == 45
        assert summary["active_sessions"] == 0
        assert summary["message_queues"]["agent-1"] == 1
        assert summary["message_queues"]["agent-2"] == 2
        assert summary["shared_knowledge_count"] == 3
        assert summary["knowledge_by_type"]["pattern"] == 2
        assert summary["knowledge_by_type"]["api_change"] == 1

    @pytest.mark.asyncio
    async def test_message_expiration_handling(self, engine):
        """Test that expired messages are not delivered."""
        # Send an already expired message
        await engine.send_message(
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.STATUS_UPDATE,
            subject="Expired message",
            content={},
            expires_in=timedelta(seconds=-1),  # Already expired
        )

        # Try to receive messages
        messages = await engine.receive_messages("agent-2")
        assert len(messages) == 0  # Expired message should not be delivered

    @pytest.mark.asyncio
    async def test_background_tasks_message_processor(self, engine):
        """Test message processor background task."""
        # Add expired acknowledgment
        expired_msg = CollaborationMessage(
            message_id="expired-1",
            sender_id="agent-1",
            recipient_id="agent-2",
            message_type=MessageType.HELP_REQUEST,
            priority=MessagePriority.HIGH,
            subject="Test",
            content={},
            expires_at=datetime.now() - timedelta(seconds=1),
            requires_ack=True,
        )
        engine.pending_acknowledgments["expired-1"] = expired_msg

        # Start engine to run background tasks
        engine._running = True

        # Run message processor once
        await engine._message_processor()

        # Check that expired acknowledgment was removed
        assert "expired-1" not in engine.pending_acknowledgments

    def test_count_knowledge_by_type(self, engine):
        """Test knowledge counting by type."""
        engine.shared_knowledge = {
            "k1": Mock(knowledge_type="pattern"),
            "k2": Mock(knowledge_type="pattern"),
            "k3": Mock(knowledge_type="api_change"),
            "k4": Mock(knowledge_type="algorithm"),
            "k5": Mock(knowledge_type="api_change"),
        }

        counts = engine._count_knowledge_by_type()

        assert counts["pattern"] == 2
        assert counts["api_change"] == 2
        assert counts["algorithm"] == 1
