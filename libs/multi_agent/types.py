"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Shared types for multi-agent system."""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentState(Enum):
    """Agent states."""

    IDLE = "idle"
    WORKING = "working"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ERROR = "error"


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task to be executed by an agent."""

    task_id: str
    title: str
    description: str
    command: list[str]
    working_directory: str
    environment: dict[str, str] = field(default_factory=dict)
    timeout: int = 300  # 5 minutes default
    priority: int = 5  # 1-10, higher is more priority
    complexity: int = 5  # 1-10, estimate of task complexity
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Execution tracking
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    output: str = ""
    error: str = ""
    exit_code: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        from dataclasses import asdict

        data = asdict(self)
        # Convert enums to strings
        data["status"] = self.status.value
        # Convert datetime to ISO format
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create from dictionary."""
        # Convert status back to enum
        if "status" in data:
            data["status"] = TaskStatus(data["status"])
        # Convert datetime strings back
        if data.get("start_time"):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        return cls(**data)


@dataclass
class Agent:
    """Represents an agent that can execute tasks."""

    agent_id: str
    state: AgentState = AgentState.IDLE
    current_task: str | None = None
    branch_name: str | None = None
    work_environment: str | None = None
    process: subprocess.Popen | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding process)."""
        from dataclasses import asdict

        data = asdict(self)
        # Remove non-serializable fields
        data.pop("process", None)
        # Convert enums and datetime
        data["state"] = self.state.value
        data["created_at"] = self.created_at.isoformat()
        data["last_heartbeat"] = self.last_heartbeat.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        """Create from dictionary."""
        # Convert state back to enum
        if "state" in data:
            data["state"] = AgentState(data["state"])
        # Convert datetime strings
        if "created_at" in data:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "last_heartbeat" in data:
            data["last_heartbeat"] = datetime.fromisoformat(data["last_heartbeat"])
        return cls(**data)
