"""Automated code review and quality checking engine for multi-agent collaboration"""

import ast
import asyncio
import hashlib
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .branch_manager import BranchManager
from .collaboration_engine import CollaborationEngine, MessagePriority, MessageType
from .semantic_analyzer import SemanticAnalyzer
from .types import AgentState

logger = logging.getLogger(__name__)


class ReviewType(Enum):
    """Types of code reviews that can be performed"""

    STYLE_QUALITY = "style_quality"  # Code style and formatting
    SECURITY = "security"  # Security vulnerabilities
    PERFORMANCE = "performance"  # Performance issues
    MAINTAINABILITY = "maintainability"  # Code maintainability
    FUNCTIONALITY = "functionality"  # Functional correctness
    DOCUMENTATION = "documentation"  # Documentation quality
    TESTING = "testing"  # Test coverage and quality
    COMPLEXITY = "complexity"  # Code complexity analysis


class ReviewSeverity(Enum):
    """Severity levels for review findings"""

    CRITICAL = "critical"  # Must fix before merge
    HIGH = "high"  # Should fix before merge
    MEDIUM = "medium"  # Should address
    LOW = "low"  # Nice to fix
    INFO = "info"  # Informational only


class ReviewStatus(Enum):
    """Status of a code review"""

    PENDING = "pending"  # Review not started
    IN_PROGRESS = "in_progress"  # Review in progress
    COMPLETED = "completed"  # Review completed
    APPROVED = "approved"  # Changes approved
    REJECTED = "rejected"  # Changes rejected
    REQUIRES_CHANGES = "requires_changes"  # Changes requested


class QualityMetric(Enum):
    """Quality metrics that can be measured"""

    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    MAINTAINABILITY_INDEX = "maintainability_index"
    CODE_COVERAGE = "code_coverage"
    DUPLICATION_RATIO = "duplication_ratio"
    LINES_OF_CODE = "lines_of_code"
    TECHNICAL_DEBT = "technical_debt"
    SECURITY_SCORE = "security_score"
    PERFORMANCE_SCORE = "performance_score"


@dataclass
class ReviewFinding:
    """A single finding from code review"""

    finding_id: str
    review_type: ReviewType
    severity: ReviewSeverity
    file_path: str
    line_number: int | None = None
    column_number: int | None = None
    message: str = ""
    description: str = ""
    suggestion: str | None = None
    rule_id: str | None = None
    tool_name: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QualityMetrics:
    """Quality metrics for a piece of code"""

    file_path: str
    metrics: dict[QualityMetric, float] = field(default_factory=dict)
    thresholds: dict[QualityMetric, float] = field(default_factory=dict)
    violations: list[QualityMetric] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeReview:
    """A comprehensive code review session"""

    review_id: str
    branch_name: str
    agent_id: str
    reviewer_ids: list[str]
    files_changed: list[str]
    review_types: list[ReviewType]
    status: ReviewStatus = ReviewStatus.PENDING
    findings: list[ReviewFinding] = field(default_factory=list)
    quality_metrics: list[QualityMetrics] = field(default_factory=list)
    overall_score: float = 0.0
    approval_required: bool = True
    auto_approved: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewSummary:
    """Summary of multiple reviews"""

    total_reviews: int = 0
    approved_reviews: int = 0
    rejected_reviews: int = 0
    pending_reviews: int = 0
    average_score: float = 0.0
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    most_common_issues: list[tuple[str, int]] = field(default_factory=list)
    review_time_stats: dict[str, float] = field(default_factory=dict)


class CodeReviewEngine:
    """Engine for automated code review and quality checking"""

    def __init__(
        self,
        collaboration_engine: CollaborationEngine,
        semantic_analyzer: SemanticAnalyzer,
        branch_manager: BranchManager,
        repo_path: str | None = None,
        enable_auto_review: bool = True,
    ):
        """
        Initialize the code review engine

        Args:
            collaboration_engine: Engine for agent collaboration
            semantic_analyzer: Analyzer for semantic code analysis
            branch_manager: Manager for branch operations
            repo_path: Path to git repository
            enable_auto_review: Whether to automatically trigger reviews
        """
        self.collaboration_engine = collaboration_engine
        self.semantic_analyzer = semantic_analyzer
        self.branch_manager = branch_manager
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.enable_auto_review = enable_auto_review

        # Review storage and tracking
        self.active_reviews: dict[str, CodeReview] = {}
        self.review_history: list[CodeReview] = []
        self.quality_profiles: dict[str, dict] = {}  # file -> quality profile

        # Review configuration
        self.review_config = {
            "require_approval_for_critical": True,
            "auto_approve_threshold": 8.5,  # Out of 10
            "max_concurrent_reviews": 10,
            "default_reviewers": 2,
            "enable_ai_reviewer": True,
            "quality_thresholds": {
                QualityMetric.CYCLOMATIC_COMPLEXITY: 10.0,
                QualityMetric.MAINTAINABILITY_INDEX: 70.0,
                QualityMetric.CODE_COVERAGE: 80.0,
                QualityMetric.DUPLICATION_RATIO: 5.0,
                QualityMetric.SECURITY_SCORE: 8.0,
                QualityMetric.PERFORMANCE_SCORE: 7.0,
            },
        }

        # Review tools integration
        self.available_tools = {
            "pylint": True,
            "flake8": True,
            "bandit": True,  # Security
            "mypy": True,  # Type checking
            "coverage": True,  # Test coverage
            "radon": True,  # Complexity analysis
        }

        # Statistics
        self.review_stats = {
            "reviews_initiated": 0,
            "reviews_completed": 0,
            "auto_approved": 0,
            "manual_reviews_required": 0,
            "average_review_time": 0.0,
            "total_findings": 0,
            "critical_findings_resolved": 0,
        }

        # Background tasks
        self._running = False
        self._review_monitor_task = None
        self._quality_monitor_task = None

    async def start(self):
        """Start the code review engine"""
        self._running = True
        logger.info("Starting code review engine")

        # Start background monitoring tasks
        self._review_monitor_task = asyncio.create_task(self._review_monitor_loop())
        self._quality_monitor_task = asyncio.create_task(self._quality_monitor_loop())

    async def stop(self):
        """Stop the code review engine"""
        self._running = False
        logger.info("Stopping code review engine")

        # Cancel background tasks
        if self._review_monitor_task:
            self._review_monitor_task.cancel()
        if self._quality_monitor_task:
            self._quality_monitor_task.cancel()

        # Wait for tasks to complete
        tasks = [t for t in [self._review_monitor_task, self._quality_monitor_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def initiate_review(
        self,
        branch_name: str,
        agent_id: str,
        files_changed: list[str],
        review_types: list[ReviewType] | None = None,
        reviewer_ids: list[str] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """
        Initiate a code review for changes in a branch

        Args:
            branch_name: Branch containing changes to review
            agent_id: ID of agent requesting review
            files_changed: List of files that were changed
            review_types: Types of review to perform
            reviewer_ids: Specific reviewers to assign
            priority: Priority of the review

        Returns:
            Review ID
        """
        review_id = f"review_{branch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.sha256(agent_id.encode()).hexdigest()[:8]}"

        # Default review types if not specified
        if review_types is None:
            review_types = [
                ReviewType.STYLE_QUALITY,
                ReviewType.SECURITY,
                ReviewType.MAINTAINABILITY,
                ReviewType.FUNCTIONALITY,
                ReviewType.TESTING,
            ]

        # Find reviewers if not specified
        if reviewer_ids is None:
            reviewer_ids = await self._find_suitable_reviewers(
                agent_id,
                files_changed,
                self.review_config["default_reviewers"],
            )

        # Create review object
        review = CodeReview(
            review_id=review_id,
            branch_name=branch_name,
            agent_id=agent_id,
            reviewer_ids=reviewer_ids,
            files_changed=files_changed,
            review_types=review_types,
            status=ReviewStatus.PENDING,
        )

        self.active_reviews[review_id] = review
        self.review_stats["reviews_initiated"] += 1

        logger.info(
            f"Initiated review {review_id} for branch {branch_name} by {agent_id}",
        )

        # Start automated review process
        asyncio.create_task(self._perform_automated_review(review))

        # Notify reviewers
        for reviewer_id in reviewer_ids:
            await self.collaboration_engine.send_message(
                sender_id=agent_id,
                recipient_id=reviewer_id,
                message_type=MessageType.REVIEW_REQUEST,
                subject=f"Code review requested: {branch_name}",
                content={
                    "review_id": review_id,
                    "branch_name": branch_name,
                    "files_changed": files_changed,
                    "review_types": [rt.value for rt in review_types],
                    "requester": agent_id,
                },
                priority=priority,
                requires_ack=True,
            )

        return review_id

    async def perform_quality_check(
        self,
        file_paths: list[str],
        quality_types: list[QualityMetric] | None = None,
    ) -> list[QualityMetrics]:
        """
        Perform comprehensive quality check on files

        Args:
            file_paths: Files to analyze
            quality_types: Specific quality metrics to calculate

        Returns:
            List of quality metrics for each file
        """
        if quality_types is None:
            quality_types = list(QualityMetric)

        results = []

        for file_path in file_paths:
            metrics = await self._calculate_quality_metrics(file_path, quality_types)
            results.append(metrics)

        return results

    async def get_review_status(self, review_id: str) -> CodeReview | None:
        """Get status of a specific review"""
        review = self.active_reviews.get(review_id)
        if not review:
            # Check review history
            review = next(
                (r for r in self.review_history if r.review_id == review_id),
                None,
            )
        return review

    async def approve_review(
        self,
        review_id: str,
        reviewer_id: str,
        comments: str | None = None,
    ) -> bool:
        """
        Approve a code review

        Args:
            review_id: ID of review to approve
            reviewer_id: ID of reviewer approving
            comments: Optional approval comments

        Returns:
            True if approval was successful
        """
        review = self.active_reviews.get(review_id)
        if not review:
            logger.warning(f"Review {review_id} not found")
            return False

        if reviewer_id not in review.reviewer_ids:
            logger.warning(f"Reviewer {reviewer_id} not assigned to review {review_id}")
            return False

        review.status = ReviewStatus.APPROVED
        review.completed_at = datetime.now()

        # Add approval metadata
        if "approvals" not in review.metadata:
            review.metadata["approvals"] = []

        review.metadata["approvals"].append(
            {
                "reviewer_id": reviewer_id,
                "approved_at": datetime.now().isoformat(),
                "comments": comments,
            },
        )

        # Move to history
        self.review_history.append(review)
        del self.active_reviews[review_id]

        self.review_stats["reviews_completed"] += 1

        # Notify the requester
        await self.collaboration_engine.send_message(
            sender_id=reviewer_id,
            recipient_id=review.agent_id,
            message_type=MessageType.STATUS_UPDATE,
            subject=f"Review approved: {review.branch_name}",
            content={
                "review_id": review_id,
                "status": "approved",
                "reviewer": reviewer_id,
                "comments": comments,
                "overall_score": review.overall_score,
            },
            priority=MessagePriority.NORMAL,
        )

        logger.info(f"Review {review_id} approved by {reviewer_id}")
        return True

    async def reject_review(
        self,
        review_id: str,
        reviewer_id: str,
        reasons: list[str],
        suggestions: list[str] | None = None,
    ) -> bool:
        """
        Reject a code review with reasons

        Args:
            review_id: ID of review to reject
            reviewer_id: ID of reviewer rejecting
            reasons: List of reasons for rejection
            suggestions: Optional suggestions for improvement

        Returns:
            True if rejection was successful
        """
        review = self.active_reviews.get(review_id)
        if not review:
            logger.warning(f"Review {review_id} not found")
            return False

        if reviewer_id not in review.reviewer_ids:
            logger.warning(f"Reviewer {reviewer_id} not assigned to review {review_id}")
            return False

        review.status = ReviewStatus.REJECTED
        review.completed_at = datetime.now()

        # Add rejection metadata
        review.metadata["rejection"] = {
            "reviewer_id": reviewer_id,
            "rejected_at": datetime.now().isoformat(),
            "reasons": reasons,
            "suggestions": suggestions or [],
        }

        # Move to history
        self.review_history.append(review)
        del self.active_reviews[review_id]

        self.review_stats["reviews_completed"] += 1

        # Notify the requester
        await self.collaboration_engine.send_message(
            sender_id=reviewer_id,
            recipient_id=review.agent_id,
            message_type=MessageType.STATUS_UPDATE,
            subject=f"Review rejected: {review.branch_name}",
            content={
                "review_id": review_id,
                "status": "rejected",
                "reviewer": reviewer_id,
                "reasons": reasons,
                "suggestions": suggestions,
                "findings_count": len(review.findings),
            },
            priority=MessagePriority.HIGH,
        )

        logger.info(f"Review {review_id} rejected by {reviewer_id}")
        return True

    # Private methods

    async def _perform_automated_review(self, review: CodeReview):
        """Perform automated review using various tools and analysis"""
        review.status = ReviewStatus.IN_PROGRESS
        review.started_at = datetime.now()

        try:
            logger.info(f"Starting automated review for {review.review_id}")

            # Collect all findings from different review types
            all_findings = []
            all_metrics = []

            for review_type in review.review_types:
                if review_type == ReviewType.STYLE_QUALITY:
                    findings = await self._check_style_quality(review.files_changed)
                    all_findings.extend(findings)

                elif review_type == ReviewType.SECURITY:
                    findings = await self._check_security(review.files_changed)
                    all_findings.extend(findings)

                elif review_type == ReviewType.PERFORMANCE:
                    findings = await self._check_performance(review.files_changed)
                    all_findings.extend(findings)

                elif review_type == ReviewType.MAINTAINABILITY:
                    findings = await self._check_maintainability(review.files_changed)
                    all_findings.extend(findings)

                elif review_type == ReviewType.FUNCTIONALITY:
                    findings = await self._check_functionality(review.files_changed)
                    all_findings.extend(findings)

                elif review_type == ReviewType.DOCUMENTATION:
                    findings = await self._check_documentation(review.files_changed)
                    all_findings.extend(findings)

                elif review_type == ReviewType.TESTING:
                    findings = await self._check_testing(review.files_changed)
                    all_findings.extend(findings)

                elif review_type == ReviewType.COMPLEXITY:
                    findings = await self._check_complexity(review.files_changed)
                    all_findings.extend(findings)

            # Calculate quality metrics
            for file_path in review.files_changed:
                if file_path.endswith(".py"):
                    metrics = await self._calculate_quality_metrics(file_path)
                    all_metrics.append(metrics)

            # Store findings and metrics
            review.findings = all_findings
            review.quality_metrics = all_metrics
            review.overall_score = self._calculate_overall_score(
                all_findings,
                all_metrics,
            )

            # Update statistics
            self.review_stats["total_findings"] += len(all_findings)
            critical_findings = [f for f in all_findings if f.severity == ReviewSeverity.CRITICAL]
            self.review_stats["critical_findings_resolved"] += len(critical_findings)

            # Determine if auto-approval is possible
            can_auto_approve = self._can_auto_approve(review)

            if can_auto_approve and self.review_config["enable_ai_reviewer"]:
                review.status = ReviewStatus.APPROVED
                review.auto_approved = True
                review.completed_at = datetime.now()

                # Move to history
                self.review_history.append(review)
                del self.active_reviews[review.review_id]

                self.review_stats["auto_approved"] += 1
                self.review_stats["reviews_completed"] += 1

                # Notify requester of auto-approval
                await self.collaboration_engine.send_message(
                    sender_id="system",
                    recipient_id=review.agent_id,
                    message_type=MessageType.STATUS_UPDATE,
                    subject=f"Review auto-approved: {review.branch_name}",
                    content={
                        "review_id": review.review_id,
                        "status": "auto_approved",
                        "overall_score": review.overall_score,
                        "findings_count": len(all_findings),
                        "critical_findings": len(critical_findings),
                    },
                    priority=MessagePriority.NORMAL,
                )

                logger.info(
                    f"Review {review.review_id} auto-approved with score {review.overall_score}",
                )

            else:
                review.status = ReviewStatus.COMPLETED
                self.review_stats["manual_reviews_required"] += 1

                # Notify reviewers that automated analysis is complete
                for reviewer_id in review.reviewer_ids:
                    await self.collaboration_engine.send_message(
                        sender_id="system",
                        recipient_id=reviewer_id,
                        message_type=MessageType.STATUS_UPDATE,
                        subject=f"Automated review completed: {review.branch_name}",
                        content={
                            "review_id": review.review_id,
                            "status": "awaiting_manual_review",
                            "overall_score": review.overall_score,
                            "findings_count": len(all_findings),
                            "critical_findings": len(critical_findings),
                            "findings_summary": self._summarize_findings(all_findings),
                        },
                        priority=MessagePriority.NORMAL,
                    )

                logger.info(
                    f"Review {review.review_id} requires manual review - score: {review.overall_score}",
                )

        except Exception as e:
            logger.error(f"Error in automated review for {review.review_id}: {e}")
            review.status = ReviewStatus.COMPLETED
            review.metadata["error"] = str(e)

    async def _check_style_quality(self, file_paths: list[str]) -> list[ReviewFinding]:
        """Check code style and formatting quality"""
        findings = []

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue

            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                # Check with flake8 if available
                if self.available_tools.get("flake8"):
                    result = await self._run_tool_check("flake8", file_path)
                    if result:
                        for issue in result:
                            finding = ReviewFinding(
                                finding_id=f"style_{hashlib.sha256(f'{file_path}_{issue}'.encode()).hexdigest()[:8]}",
                                review_type=ReviewType.STYLE_QUALITY,
                                severity=ReviewSeverity.LOW,
                                file_path=file_path,
                                message=issue,
                                tool_name="flake8",
                            )
                            findings.append(finding)

                # Check line length
                with open(full_path, encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if len(line.rstrip()) > 88:  # Black default
                            finding = ReviewFinding(
                                finding_id=f"style_line_length_{file_path}_{line_num}",
                                review_type=ReviewType.STYLE_QUALITY,
                                severity=ReviewSeverity.LOW,
                                file_path=file_path,
                                line_number=line_num,
                                message=f"Line too long ({len(line.rstrip())} > 88 characters)",
                                description="Consider breaking this line for better readability",
                            )
                            findings.append(finding)

            except Exception as e:
                logger.error(f"Error checking style for {file_path}: {e}")

        return findings

    async def _check_security(self, file_paths: list[str]) -> list[ReviewFinding]:
        """Check for security vulnerabilities"""
        findings = []

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue

            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                # Use bandit for security checking if available
                if self.available_tools.get("bandit"):
                    result = await self._run_tool_check("bandit", file_path)
                    if result:
                        for issue in result:
                            finding = ReviewFinding(
                                finding_id=f"security_{hashlib.sha256(f'{file_path}_{issue}'.encode()).hexdigest()[:8]}",
                                review_type=ReviewType.SECURITY,
                                severity=ReviewSeverity.HIGH,
                                file_path=file_path,
                                message=issue,
                                tool_name="bandit",
                                description="Potential security vulnerability detected",
                            )
                            findings.append(finding)

                # Basic security pattern checks
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                    # Check for hardcoded secrets
                    secret_patterns = [
                        r'password\s*=\s*["\'][^"\']+["\']',
                        r'api_key\s*=\s*["\'][^"\']+["\']',
                        r'secret\s*=\s*["\'][^"\']+["\']',
                        r'token\s*=\s*["\'][^"\']+["\']',
                    ]

                    for pattern in secret_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[: match.start()].count("\n") + 1
                            finding = ReviewFinding(
                                finding_id=f"security_hardcoded_{file_path}_{line_num}",
                                review_type=ReviewType.SECURITY,
                                severity=ReviewSeverity.CRITICAL,
                                file_path=file_path,
                                line_number=line_num,
                                message="Potential hardcoded secret detected",
                                description="Avoid hardcoding secrets in source code",
                                suggestion="Use environment variables or secure secret management",
                            )
                            findings.append(finding)

            except Exception as e:
                logger.error(f"Error checking security for {file_path}: {e}")

        return findings

    async def _check_performance(self, file_paths: list[str]) -> list[ReviewFinding]:
        """Check for performance issues"""
        findings = []

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue

            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                # Parse AST for performance analysis
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    # Check for inefficient loops
                    if isinstance(node, ast.For):
                        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                            # Check for range(len(list)) pattern
                            if len(node.iter.args) == 1 and isinstance(node.iter.args[0], ast.Call) and isinstance(node.iter.args[0].func, ast.Name) and node.iter.args[0].func.id == "len":
                                finding = ReviewFinding(
                                    finding_id=f"perf_range_len_{file_path}_{node.lineno}",
                                    review_type=ReviewType.PERFORMANCE,
                                    severity=ReviewSeverity.MEDIUM,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    message="Consider using enumerate() instead of range(len())",
                                    description="Using enumerate() is more Pythonic and potentially faster",
                                    suggestion="Replace 'for i in range(len(items)):' with 'for i, item in enumerate(items):'",
                                )
                                findings.append(finding)

                    # Check for string concatenation in loops
                    elif (
                        isinstance(node, ast.AugAssign)
                        and isinstance(
                            node.op,
                            ast.Add,
                        )
                        and isinstance(node.target, ast.Name)
                    ):
                        # This is a simplified check - could be more sophisticated
                        finding = ReviewFinding(
                            finding_id=f"perf_string_concat_{file_path}_{node.lineno}",
                            review_type=ReviewType.PERFORMANCE,
                            severity=ReviewSeverity.LOW,
                            file_path=file_path,
                            line_number=node.lineno,
                            message="Consider using join() for string concatenation",
                            description="String concatenation in loops can be inefficient",
                            suggestion="Use ''.join(list) for better performance when concatenating many strings",
                        )
                        findings.append(finding)

            except Exception as e:
                logger.error(f"Error checking performance for {file_path}: {e}")

        return findings

    async def _check_maintainability(
        self,
        file_paths: list[str],
    ) -> list[ReviewFinding]:
        """Check code maintainability"""
        findings = []

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue

            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                # Basic maintainability checks
                lines = content.split("\n")

                # Check for long functions
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                        # Calculate function length
                        func_lines = 0
                        if hasattr(node, "end_lineno") and node.end_lineno:
                            func_lines = node.end_lineno - node.lineno + 1

                        if func_lines > 50:  # Arbitrary threshold
                            finding = ReviewFinding(
                                finding_id=f"maint_long_func_{file_path}_{node.lineno}",
                                review_type=ReviewType.MAINTAINABILITY,
                                severity=ReviewSeverity.MEDIUM,
                                file_path=file_path,
                                line_number=node.lineno,
                                message=f"Function '{node.name}' is too long ({func_lines} lines)",
                                description="Long functions are harder to understand and maintain",
                                suggestion="Consider breaking this function into smaller, more focused functions",
                            )
                            findings.append(finding)

                        # Check for too many parameters
                        if len(node.args.args) > 7:
                            finding = ReviewFinding(
                                finding_id=f"maint_many_params_{file_path}_{node.lineno}",
                                review_type=ReviewType.MAINTAINABILITY,
                                severity=ReviewSeverity.MEDIUM,
                                file_path=file_path,
                                line_number=node.lineno,
                                message=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                                description="Functions with many parameters are hard to use and maintain",
                                suggestion="Consider using a configuration object or breaking the function down",
                            )
                            findings.append(finding)

                # Check for large files
                if len(lines) > 500:
                    finding = ReviewFinding(
                        finding_id=f"maint_large_file_{file_path}",
                        review_type=ReviewType.MAINTAINABILITY,
                        severity=ReviewSeverity.LOW,
                        file_path=file_path,
                        message=f"File is very large ({len(lines)} lines)",
                        description="Large files can be difficult to navigate and maintain",
                        suggestion="Consider splitting this file into smaller, more focused modules",
                    )
                    findings.append(finding)

            except Exception as e:
                logger.error(f"Error checking maintainability for {file_path}: {e}")

        return findings

    async def _check_functionality(self, file_paths: list[str]) -> list[ReviewFinding]:
        """Check functional correctness"""
        findings = []

        # This is a simplified implementation
        # In a real system, this might involve running tests, checking type annotations, etc.

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue

            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                # Use mypy for type checking if available
                if self.available_tools.get("mypy"):
                    result = await self._run_tool_check("mypy", file_path)
                    if result:
                        for issue in result:
                            finding = ReviewFinding(
                                finding_id=f"func_{hashlib.sha256(f'{file_path}_{issue}'.encode()).hexdigest()[:8]}",
                                review_type=ReviewType.FUNCTIONALITY,
                                severity=ReviewSeverity.MEDIUM,
                                file_path=file_path,
                                message=issue,
                                tool_name="mypy",
                                description="Type checking issue detected",
                            )
                            findings.append(finding)

            except Exception as e:
                logger.error(f"Error checking functionality for {file_path}: {e}")

        return findings

    async def _check_documentation(self, file_paths: list[str]) -> list[ReviewFinding]:
        """Check documentation quality"""
        findings = []

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue

            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                # Check for missing docstrings
                for node in ast.walk(tree):
                    if isinstance(
                        node,
                        ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
                    ):
                        # Check if function/class has docstring
                        has_docstring = len(node.body) > 0 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)

                        if not has_docstring:
                            # Skip private methods (start with _) unless they're special methods
                            if node.name.startswith("_") and not (node.name.startswith("__") and node.name.endswith("__")):
                                continue

                            severity = ReviewSeverity.LOW
                            if isinstance(
                                node,
                                ast.ClassDef,
                            ) or not node.name.startswith("_"):
                                severity = ReviewSeverity.MEDIUM

                            finding = ReviewFinding(
                                finding_id=f"doc_missing_{file_path}_{node.lineno}",
                                review_type=ReviewType.DOCUMENTATION,
                                severity=severity,
                                file_path=file_path,
                                line_number=node.lineno,
                                message=f"Missing docstring for {type(node).__name__.lower()} '{node.name}'",
                                description="Public functions and classes should have docstrings",
                                suggestion="Add a docstring describing the purpose, parameters, and return value",
                            )
                            findings.append(finding)

            except Exception as e:
                logger.error(f"Error checking documentation for {file_path}: {e}")

        return findings

    async def _check_testing(self, file_paths: list[str]) -> list[ReviewFinding]:
        """Check testing coverage and quality"""
        findings = []

        # This is a simplified implementation
        # In a real system, this would integrate with coverage tools

        for file_path in file_paths:
            if not file_path.endswith(".py") or file_path.startswith("test_"):
                continue

            # Check if there's a corresponding test file
            test_file_patterns = [
                f"test_{Path(file_path).stem}.py",
                f"tests/test_{Path(file_path).stem}.py",
                f"{Path(file_path).parent}/test_{Path(file_path).stem}.py",
            ]

            has_test_file = any((self.repo_path / pattern).exists() for pattern in test_file_patterns)

            if not has_test_file:
                finding = ReviewFinding(
                    finding_id=f"test_missing_{file_path}",
                    review_type=ReviewType.TESTING,
                    severity=ReviewSeverity.MEDIUM,
                    file_path=file_path,
                    message=f"No test file found for {file_path}",
                    description="Code should have corresponding test files",
                    suggestion=f"Create a test file (e.g., test_{Path(file_path).stem}.py)",
                )
                findings.append(finding)

        return findings

    async def _check_complexity(self, file_paths: list[str]) -> list[ReviewFinding]:
        """Check code complexity"""
        findings = []

        for file_path in file_paths:
            if not file_path.endswith(".py"):
                continue

            full_path = self.repo_path / file_path
            if not full_path.exists():
                continue

            try:
                # Use radon for complexity analysis if available
                if self.available_tools.get("radon"):
                    result = await self._run_tool_check("radon", file_path)
                    if result:
                        for issue in result:
                            finding = ReviewFinding(
                                finding_id=f"complex_{hashlib.sha256(f'{file_path}_{issue}'.encode()).hexdigest()[:8]}",
                                review_type=ReviewType.COMPLEXITY,
                                severity=ReviewSeverity.MEDIUM,
                                file_path=file_path,
                                message=issue,
                                tool_name="radon",
                                description="High complexity detected",
                            )
                            findings.append(finding)

            except Exception as e:
                logger.error(f"Error checking complexity for {file_path}: {e}")

        return findings

    async def _calculate_quality_metrics(
        self,
        file_path: str,
        metric_types: list[QualityMetric] | None = None,
    ) -> QualityMetrics:
        """Calculate quality metrics for a file"""
        if metric_types is None:
            metric_types = list(QualityMetric)

        metrics = QualityMetrics(
            file_path=file_path,
            thresholds=self.review_config["quality_thresholds"].copy(),
        )

        full_path = self.repo_path / file_path
        if not full_path.exists() or not file_path.endswith(".py"):
            return metrics

        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            non_empty_lines = [line for line in lines if line.strip()]

            # Calculate basic metrics
            if QualityMetric.LINES_OF_CODE in metric_types:
                metrics.metrics[QualityMetric.LINES_OF_CODE] = len(non_empty_lines)

            # Simple cyclomatic complexity estimation
            if QualityMetric.CYCLOMATIC_COMPLEXITY in metric_types:
                complexity = self._estimate_cyclomatic_complexity(content)
                metrics.metrics[QualityMetric.CYCLOMATIC_COMPLEXITY] = complexity

                if complexity > metrics.thresholds[QualityMetric.CYCLOMATIC_COMPLEXITY]:
                    metrics.violations.append(QualityMetric.CYCLOMATIC_COMPLEXITY)

            # Maintainability index (simplified)
            if QualityMetric.MAINTAINABILITY_INDEX in metric_types:
                mi = self._calculate_maintainability_index(
                    content,
                    len(non_empty_lines),
                )
                metrics.metrics[QualityMetric.MAINTAINABILITY_INDEX] = mi

                if mi < metrics.thresholds[QualityMetric.MAINTAINABILITY_INDEX]:
                    metrics.violations.append(QualityMetric.MAINTAINABILITY_INDEX)

        except Exception as e:
            logger.error(f"Error calculating quality metrics for {file_path}: {e}")

        return metrics

    def _estimate_cyclomatic_complexity(self, content: str) -> float:
        """Estimate cyclomatic complexity by counting decision points"""
        try:
            tree = ast.parse(content)
            complexity = 1  # Base complexity

            for node in ast.walk(tree):
                if isinstance(node, ast.If | ast.While | ast.For | ast.AsyncFor | ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return float(complexity)
        except:
            return 1.0

    def _calculate_maintainability_index(self, content: str, loc: int) -> float:
        """Calculate a simplified maintainability index"""
        try:
            # Simplified calculation based on lines of code and comments
            comment_ratio = content.count("#") / max(loc, 1)
            docstring_ratio = content.count('"""') / max(loc, 1) * 10

            # Simple heuristic: lower LOC and higher comment ratio = better maintainability
            mi = max(
                0,
                min(
                    100,
                    100 - (loc / 10) + (comment_ratio * 20) + (docstring_ratio * 10),
                ),
            )
            return mi
        except:
            return 50.0  # Default neutral score

    def _calculate_overall_score(
        self,
        findings: list[ReviewFinding],
        metrics: list[QualityMetrics],
    ) -> float:
        """Calculate overall review score from findings and metrics"""
        base_score = 10.0

        # Deduct points for findings based on severity
        severity_weights = {
            ReviewSeverity.CRITICAL: 3.0,
            ReviewSeverity.HIGH: 2.0,
            ReviewSeverity.MEDIUM: 1.0,
            ReviewSeverity.LOW: 0.5,
            ReviewSeverity.INFO: 0.1,
        }

        for finding in findings:
            base_score -= severity_weights.get(finding.severity, 0.5)

        # Factor in quality metrics violations
        for metric in metrics:
            violation_penalty = len(metric.violations) * 0.5
            base_score -= violation_penalty

        return max(0.0, min(10.0, base_score))

    def _can_auto_approve(self, review: CodeReview) -> bool:
        """Determine if a review can be automatically approved"""
        # Check overall score threshold
        if review.overall_score < self.review_config["auto_approve_threshold"]:
            return False

        # Check for critical or high severity findings
        if self.review_config["require_approval_for_critical"]:
            for finding in review.findings:
                if finding.severity in [ReviewSeverity.CRITICAL, ReviewSeverity.HIGH]:
                    return False

        # Check for quality metric violations
        return all(not metrics.violations for metrics in review.quality_metrics)

    def _summarize_findings(self, findings: list[ReviewFinding]) -> dict[str, Any]:
        """Create a summary of review findings"""
        severity_counts = Counter(f.severity.value for f in findings)
        type_counts = Counter(f.review_type.value for f in findings)

        return {
            "total_findings": len(findings),
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "most_common_issues": type_counts.most_common(3),
        }

    async def _find_suitable_reviewers(
        self,
        requester_id: str,
        files_changed: list[str],
        num_reviewers: int,
    ) -> list[str]:
        """Find suitable reviewers for a code review"""
        # This is a simplified implementation
        # In a real system, this would consider expertise, availability, workload, etc.

        # Get all available agents
        available_agents = []
        for agent in self.collaboration_engine.agent_pool.agents.values():
            if agent.id != requester_id and agent.state in [
                AgentState.IDLE,
                AgentState.WORKING,
            ]:
                available_agents.append(agent.id)

        # For now, just return the first available agents
        return available_agents[:num_reviewers]

    async def _run_tool_check(
        self,
        tool_name: str,
        file_path: str,
    ) -> list[str] | None:
        """Run an external tool for code checking"""
        # This is a placeholder implementation
        # In a real system, this would actually run the tools
        logger.debug(f"Would run {tool_name} on {file_path}")
        return None

    async def _review_monitor_loop(self):
        """Background task to monitor review progress"""
        while self._running:
            try:
                # Check for stale reviews
                current_time = datetime.now()
                stale_reviews = []

                for review_id, review in self.active_reviews.items():
                    if review.status == ReviewStatus.IN_PROGRESS and review.started_at and (current_time - review.started_at) > timedelta(hours=24):
                        stale_reviews.append(review_id)

                # Handle stale reviews
                for review_id in stale_reviews:
                    logger.warning(f"Review {review_id} is stale, requiring attention")
                    # Could send notifications or escalate

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in review monitor loop: {e}")
                await asyncio.sleep(300)

    async def _quality_monitor_loop(self):
        """Background task to monitor code quality trends"""
        while self._running:
            try:
                # Collect quality metrics across all recent reviews
                # This could be used for trend analysis, alerts, etc.

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Error in quality monitor loop: {e}")
                await asyncio.sleep(3600)

    def get_review_summary(self) -> ReviewSummary:
        """Get summary of all reviews"""
        all_reviews = list(self.active_reviews.values()) + self.review_history

        if not all_reviews:
            return ReviewSummary()

        # Calculate statistics
        total_reviews = len(all_reviews)
        approved_reviews = len(
            [r for r in all_reviews if r.status == ReviewStatus.APPROVED],
        )
        rejected_reviews = len(
            [r for r in all_reviews if r.status == ReviewStatus.REJECTED],
        )
        pending_reviews = len(
            [r for r in all_reviews if r.status in [ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS]],
        )

        # Calculate average score
        scores = [r.overall_score for r in all_reviews if r.overall_score > 0]
        average_score = sum(scores) / len(scores) if scores else 0.0

        # Count findings
        all_findings = []
        for review in all_reviews:
            all_findings.extend(review.findings)

        total_findings = len(all_findings)
        critical_findings = len(
            [f for f in all_findings if f.severity == ReviewSeverity.CRITICAL],
        )
        high_findings = len(
            [f for f in all_findings if f.severity == ReviewSeverity.HIGH],
        )

        # Most common issues
        issue_counts = Counter(f"{f.review_type.value}: {f.message}" for f in all_findings)
        most_common_issues = issue_counts.most_common(5)

        # Review time statistics
        completed_reviews = [r for r in all_reviews if r.completed_at and r.started_at]
        if completed_reviews:
            review_times = [(r.completed_at - r.started_at).total_seconds() for r in completed_reviews]
            review_time_stats = {
                "average_time": sum(review_times) / len(review_times),
                "min_time": min(review_times),
                "max_time": max(review_times),
            }
        else:
            review_time_stats = {}

        return ReviewSummary(
            total_reviews=total_reviews,
            approved_reviews=approved_reviews,
            rejected_reviews=rejected_reviews,
            pending_reviews=pending_reviews,
            average_score=average_score,
            total_findings=total_findings,
            critical_findings=critical_findings,
            high_findings=high_findings,
            most_common_issues=most_common_issues,
            review_time_stats=review_time_stats,
        )

    def get_engine_summary(self) -> dict[str, Any]:
        """Get comprehensive summary of the review engine"""
        return {
            "statistics": self.review_stats.copy(),
            "active_reviews": len(self.active_reviews),
            "total_reviews": len(self.review_history) + len(self.active_reviews),
            "available_tools": self.available_tools.copy(),
            "review_config": self.review_config.copy(),
            "recent_reviews": [
                {
                    "review_id": review.review_id,
                    "branch_name": review.branch_name,
                    "agent_id": review.agent_id,
                    "status": review.status.value,
                    "overall_score": review.overall_score,
                    "findings_count": len(review.findings),
                    "created_at": review.created_at.isoformat(),
                }
                for review in (list(self.active_reviews.values()) + self.review_history)[-10:]
            ],
        }
