import asyncio
import tempfile
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.code_review_engine import (
    CodeReview,
    CodeReviewEngine,
    QualityMetric,
    QualityMetrics,
    ReviewFinding,
    ReviewSeverity,
    ReviewStatus,
    ReviewType,
)


@pytest.fixture
def temp_repo() -> object:
    """Create a temporary repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)

        # Create some test files
        (repo_path / "src").mkdir()
        (repo_path / "tests").mkdir()

        # Create a Python file with various issues
        test_file = repo_path / "src" / "test_module.py"
        test_file.write_text(
            '''
"""Test module for code review testing"""



def long_function_with_many_issues(param1, param2, param3, param4, param5, param6, param7, param8) -> object:
    """This function has many issues that should be detected"""
    password = "hardcoded_secret_123"  # Security issue
    result = ""

    # Performance issue: range(len())
    for i in range(len(param1)):
        # Performance issue: string concatenation
        result += str(param1[i])

    # Long function body to trigger maintainability warning
    if param2:
        if param3:
            if param4:
                if param5:
                    if param6:
                        if param7:
                            if param8:
                                print("Deep nesting")
                                print("Line 1")
                                print("Line 2")
                                print("Line 3")
                                print("Line 4")
                                print("Line 5")
                                print("Line 6")
                                print("Line 7")
                                print("Line 8")
                                print("Line 9")
                                print("Line 10")
                                print("Line 11")
                                print("Line 12")
                                print("Line 13")
                                print("Line 14")
                                print("Line 15")
                                print("Line 16")
                                print("Line 17")
                                print("Line 18")
                                print("Line 19")
                                print("Line 20")
                                print("Line 21")
                                print("Line 22")
                                print("Line 23")
                                print("Line 24")
                                print("Line 25")

    return result


class TestClassWithoutDocstring:
    @staticmethod
    def public_method_without_docstring() -> object:
        pass

    @staticmethod
    def _private_method() -> object:
        pass


def function_without_docstring() -> object:
    pass
'''
        )

        # Create a simple good file
        good_file = repo_path / "src" / "good_module.py"
        good_file.write_text(
            '''
"""A well-written module for testing"""


def well_written_function(data: list) -> str:
    """
    A well-documented function with good practices

    Args:
        data: Input data to process

    Returns:
        Processed result as string
    """
    return "".join(str(item) for item in data)


class WellWrittenClass:
    """A well-documented class"""

    def __init__(self, value: str) -> None:
        """Initialize with a value"""
        self.value = value

    def process(self) -> str:
        """Process the value"""
        return self.value.upper()
'''
        )

        yield repo_path


@pytest.fixture
def mock_collaboration_engine() -> object:
    """Create a mock collaboration engine."""
    engine = Mock(spec=CollaborationEngine)
    engine.send_message = AsyncMock()
    engine.agent_pool = Mock()
    engine.agent_pool.agents = {
        "agent-1": Mock(id="agent-1", state="idle"),
        "agent-2": Mock(id="agent-2", state="working"),
        "agent-3": Mock(id="agent-3", state="idle"),
    }
    return engine


@pytest.fixture
def mock_semantic_analyzer() -> object:
    """Create a mock semantic analyzer."""
    return Mock(spec=SemanticAnalyzer)


@pytest.fixture
def mock_branch_manager() -> object:
    """Create a mock branch manager."""
    return Mock(spec=BranchManager)


@pytest.fixture
async def code_review_engine(
    temp_repo: Path,
    mock_collaboration_engine: Mock,
    mock_semantic_analyzer: Mock,
    mock_branch_manager: Mock,
) -> AsyncGenerator[CodeReviewEngine, None]:
    """Create a CodeReviewEngine instance for testing."""
    engine = CodeReviewEngine(
        collaboration_engine=mock_collaboration_engine,
        semantic_analyzer=mock_semantic_analyzer,
        branch_manager=mock_branch_manager,
        repo_path=str(temp_repo),
        enable_auto_review=True,
    )

    await engine.start()
    yield engine
    await engine.stop()


class TestCodeReviewEngine:
    """Test cases for CodeReviewEngine."""

    @pytest.mark.asyncio
    @staticmethod
    async def test_initiate_review(code_review_engine: CodeReviewEngine, mock_collaboration_engine: Mock) -> None:
        """Test initiating a code review."""
        review_id = await code_review_engine.initiate_review(
            branch_name="feature/test-branch",
            agent_id="agent-1",
            files_changed=["src/test_module.py"],
            review_types=[ReviewType.STYLE_QUALITY, ReviewType.SECURITY],
        )

        assert review_id.startswith("review_feature/test-branch_")
        assert review_id in code_review_engine.active_reviews

        review = code_review_engine.active_reviews[review_id]
        assert review.branch_name == "feature/test-branch"
        assert review.agent_id == "agent-1"
        assert review.files_changed == ["src/test_module.py"]
        assert ReviewType.STYLE_QUALITY in review.review_types
        assert ReviewType.SECURITY in review.review_types

        # Check that messages were sent to reviewers
        assert mock_collaboration_engine.send_message.called

    @pytest.mark.asyncio
    @staticmethod
    async def test_automated_review_style_quality(code_review_engine: CodeReviewEngine) -> None:
        """Test automated style and quality review."""
        findings = await code_review_engine._check_style_quality(["src/test_module.py"])  # noqa: SLF001

        # Should detect line length issues
        line_length_findings = [f for f in findings if "Line too long" in f.message]
        assert len(line_length_findings) > 0

        for finding in line_length_findings:
            assert finding.review_type == ReviewType.STYLE_QUALITY
            assert finding.severity == ReviewSeverity.LOW
            assert finding.file_path == "src/test_module.py"

    @pytest.mark.asyncio
    @staticmethod
    async def test_automated_review_security(code_review_engine: CodeReviewEngine) -> None:
        """Test automated security review."""
        findings = await code_review_engine._check_security(["src/test_module.py"])  # noqa: SLF001

        # Should detect hardcoded password
        security_findings = [f for f in findings if "hardcoded secret" in f.message.lower()]
        assert len(security_findings) > 0

        for finding in security_findings:
            assert finding.review_type == ReviewType.SECURITY
            assert finding.severity == ReviewSeverity.CRITICAL
            assert finding.file_path == "src/test_module.py"

    @pytest.mark.asyncio
    @staticmethod
    async def test_automated_review_performance(code_review_engine: CodeReviewEngine) -> None:
        """Test automated performance review."""
        findings = await code_review_engine._check_performance(["src/test_module.py"])  # noqa: SLF001

        # Should detect range(len()) pattern
        range_len_findings = [f for f in findings if "enumerate" in f.message]
        assert len(range_len_findings) > 0

        # Should detect string concatenation
        concat_findings = [f for f in findings if "join" in f.message]
        assert len(concat_findings) > 0

        for finding in findings:
            assert finding.review_type == ReviewType.PERFORMANCE
            assert finding.file_path == "src/test_module.py"

    @pytest.mark.asyncio
    @staticmethod
    async def test_automated_review_maintainability(code_review_engine: CodeReviewEngine) -> None:
        """Test automated maintainability review."""
        findings = await code_review_engine._check_maintainability(  # noqa: SLF001
            ["src/test_module.py"],
        )

        # Should detect long function
        long_func_findings = [f for f in findings if "too long" in f.message]
        assert len(long_func_findings) > 0

        # Should detect too many parameters
        param_findings = [f for f in findings if "too many parameters" in f.message]
        assert len(param_findings) > 0

        for finding in findings:
            assert finding.review_type == ReviewType.MAINTAINABILITY
            assert finding.file_path == "src/test_module.py"

    @pytest.mark.asyncio
    @staticmethod
    async def test_automated_review_documentation(code_review_engine: CodeReviewEngine) -> None:
        """Test automated documentation review."""
        findings = await code_review_engine._check_documentation(["src/test_module.py"])  # noqa: SLF001

        # Should detect missing docstrings
        docstring_findings = [f for f in findings if "Missing docstring" in f.message]
        assert len(docstring_findings) > 0

        # Should not complain about private methods
        private_findings = [f for f in findings if "_private_method" in f.message]
        assert len(private_findings) == 0

        for finding in findings:
            assert finding.review_type == ReviewType.DOCUMENTATION
            assert finding.file_path == "src/test_module.py"

    @pytest.mark.asyncio
    @staticmethod
    async def test_automated_review_testing(code_review_engine: CodeReviewEngine) -> None:
        """Test automated testing review."""
        findings = await code_review_engine._check_testing(["src/test_module.py"])  # noqa: SLF001

        # Should detect missing test file
        test_findings = [f for f in findings if "No test file found" in f.message]
        assert len(test_findings) > 0

        for finding in findings:
            assert finding.review_type == ReviewType.TESTING
            assert finding.file_path == "src/test_module.py"

    @pytest.mark.asyncio
    @staticmethod
    async def test_quality_metrics_calculation(code_review_engine: CodeReviewEngine) -> None:
        """Test quality metrics calculation."""
        metrics = await code_review_engine._calculate_quality_metrics(  # noqa: SLF001
            "src/test_module.py",
        )

        assert metrics.file_path == "src/test_module.py"
        assert QualityMetric.LINES_OF_CODE in metrics.metrics
        assert QualityMetric.CYCLOMATIC_COMPLEXITY in metrics.metrics
        assert QualityMetric.MAINTAINABILITY_INDEX in metrics.metrics

        # The test file has high complexity, so it should violate thresholds
        assert QualityMetric.CYCLOMATIC_COMPLEXITY in metrics.violations

    @pytest.mark.asyncio
    @staticmethod
    async def test_quality_check_multiple_files(code_review_engine: CodeReviewEngine) -> None:
        """Test quality check on multiple files."""
        metrics_list = await code_review_engine.perform_quality_check(
            ["src/test_module.py", "src/good_module.py"],
        )

        assert len(metrics_list) == 2

        # Test module should have violations
        test_metrics = next(m for m in metrics_list if m.file_path == "src/test_module.py")
        assert len(test_metrics.violations) > 0

        # Good module should have fewer or no violations
        good_metrics = next(m for m in metrics_list if m.file_path == "src/good_module.py")
        assert len(good_metrics.violations) <= len(test_metrics.violations)

    @pytest.mark.asyncio
    @staticmethod
    async def test_overall_score_calculation(code_review_engine: CodeReviewEngine) -> None:
        """Test overall score calculation."""
        # Create some test findings
        findings = [
            ReviewFinding(
                finding_id="test1",
                review_type=ReviewType.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                file_path="test.py",
                message="Critical security issue",
            ),
            ReviewFinding(
                finding_id="test2",
                review_type=ReviewType.STYLE_QUALITY,
                severity=ReviewSeverity.LOW,
                file_path="test.py",
                message="Style issue",
            ),
        ]

        # Create test metrics with violations
        metrics = [
            QualityMetrics(
                file_path="test.py",
                violations=[QualityMetric.CYCLOMATIC_COMPLEXITY],
            ),
        ]

        score = code_review_engine._calculate_overall_score(findings, metrics)  # noqa: SLF001

        # Score should be reduced due to critical finding and violations
        assert score < 10.0
        assert score >= 0.0

    @pytest.mark.asyncio
    @staticmethod
    async def test_auto_approval_logic(code_review_engine: CodeReviewEngine) -> None:
        """Test auto-approval logic."""
        # Create a review with high score and no critical issues
        review = CodeReview(
            review_id="test_review",
            branch_name="test_branch",
            agent_id="agent-1",
            reviewer_ids=["agent-2"],
            files_changed=["src/good_module.py"],
            review_types=[ReviewType.STYLE_QUALITY],
            findings=[
                ReviewFinding(
                    finding_id="test1",
                    review_type=ReviewType.STYLE_QUALITY,
                    severity=ReviewSeverity.LOW,
                    file_path="test.py",
                    message="Minor style issue",
                ),
            ],
            overall_score=9.0,
        )

        # Should be auto-approvable with high score and no critical issues
        can_approve = code_review_engine._can_auto_approve(review)  # noqa: SLF001
        assert can_approve

        # Add a critical finding
        review.findings.append(
            ReviewFinding(
                finding_id="test2",
                review_type=ReviewType.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                file_path="test.py",
                message="Critical security issue",
            ),
        )

        # Should not be auto-approvable with critical issues
        can_approve = code_review_engine._can_auto_approve(review)  # noqa: SLF001
        assert not can_approve

    @pytest.mark.asyncio
    @staticmethod
    async def test_approve_review(code_review_engine: CodeReviewEngine, mock_collaboration_engine: Mock) -> None:
        """Test review approval."""
        # Create a test review
        review_id = await code_review_engine.initiate_review(
            branch_name="test_branch",
            agent_id="agent-1",
            files_changed=["src/good_module.py"],
            reviewer_ids=["agent-2"],
        )

        # Approve the review
        success = await code_review_engine.approve_review(
            review_id=review_id,
            reviewer_id="agent-2",
            comments="Looks good!",
        )

        assert success
        assert review_id not in code_review_engine.active_reviews
        assert any(r.review_id == review_id for r in code_review_engine.review_history)

        # Check that approval message was sent
        approval_messages = [call for call in mock_collaboration_engine.send_message.call_args_list if "approved" in str(call)]
        assert len(approval_messages) > 0

    @pytest.mark.asyncio
    @staticmethod
    async def test_reject_review(code_review_engine: CodeReviewEngine, mock_collaboration_engine: Mock) -> None:
        """Test review rejection."""
        # Create a test review
        review_id = await code_review_engine.initiate_review(
            branch_name="test_branch",
            agent_id="agent-1",
            files_changed=["src/test_module.py"],
            reviewer_ids=["agent-2"],
        )

        # Reject the review
        success = await code_review_engine.reject_review(
            review_id=review_id,
            reviewer_id="agent-2",
            reasons=["Security issues found", "Code quality issues"],
            suggestions=["Fix hardcoded secrets", "Improve documentation"],
        )

        assert success
        assert review_id not in code_review_engine.active_reviews
        assert any(r.review_id == review_id for r in code_review_engine.review_history)

        # Check that rejection message was sent
        rejection_messages = [call for call in mock_collaboration_engine.send_message.call_args_list if "rejected" in str(call)]
        assert len(rejection_messages) > 0

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_review_status(code_review_engine: CodeReviewEngine) -> None:
        """Test getting review status."""
        # Create a test review
        review_id = await code_review_engine.initiate_review(
            branch_name="test_branch",
            agent_id="agent-1",
            files_changed=["src/good_module.py"],
        )

        # Get active review status
        review = await code_review_engine.get_review_status(review_id)
        assert review is not None
        assert review.review_id == review_id
        assert review.status in {ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS}

        # Approve and move to history
        await code_review_engine.approve_review(
            review_id=review_id,
            reviewer_id=review.reviewer_ids[0],
        )

        # Get historical review status
        review = await code_review_engine.get_review_status(review_id)
        assert review is not None
        assert review.status == ReviewStatus.APPROVED

    @staticmethod
    def test_review_summary(code_review_engine: CodeReviewEngine) -> None:
        """Test review summary generation."""
        # Add some test reviews to history
        test_reviews = [
            CodeReview(
                review_id="review1",
                branch_name="branch1",
                agent_id="agent-1",
                reviewer_ids=["agent-2"],
                files_changed=["file1.py"],
                review_types=[ReviewType.STYLE_QUALITY],
                status=ReviewStatus.APPROVED,
                overall_score=8.5,
                findings=[
                    ReviewFinding(
                        finding_id="f1",
                        review_type=ReviewType.STYLE_QUALITY,
                        severity=ReviewSeverity.LOW,
                        file_path="file1.py",
                        message="Style issue",
                    ),
                ],
            ),
            CodeReview(
                review_id="review2",
                branch_name="branch2",
                agent_id="agent-1",
                reviewer_ids=["agent-3"],
                files_changed=["file2.py"],
                review_types=[ReviewType.SECURITY],
                status=ReviewStatus.REJECTED,
                overall_score=4.0,
                findings=[
                    ReviewFinding(
                        finding_id="f2",
                        review_type=ReviewType.SECURITY,
                        severity=ReviewSeverity.CRITICAL,
                        file_path="file2.py",
                        message="Security issue",
                    ),
                ],
            ),
        ]

        code_review_engine.review_history.extend(test_reviews)

        summary = code_review_engine.get_review_summary()

        assert summary.total_reviews == 2
        assert summary.approved_reviews == 1
        assert summary.rejected_reviews == 1
        assert summary.total_findings == 2
        assert summary.critical_findings == 1
        assert len(summary.most_common_issues) > 0

    @staticmethod
    def test_engine_summary(code_review_engine: CodeReviewEngine) -> None:
        """Test engine summary generation."""
        summary = code_review_engine.get_engine_summary()

        assert "statistics" in summary
        assert "active_reviews" in summary
        assert "total_reviews" in summary
        assert "available_tools" in summary
        assert "review_config" in summary
        assert "recent_reviews" in summary

        assert isinstance(summary["statistics"], dict)
        assert isinstance(summary["available_tools"], dict)
        assert isinstance(summary["review_config"], dict)

    @pytest.mark.asyncio
    @staticmethod
    async def test_find_suitable_reviewers(code_review_engine: CodeReviewEngine) -> None:
        """Test finding suitable reviewers."""
        reviewers = await code_review_engine._find_suitable_reviewers(  # noqa: SLF001
            requester_id="agent-1",
            files_changed=["test.py"],
            num_reviewers=2,
        )

        assert len(reviewers) <= 2
        assert "agent-1" not in reviewers  # Requester should not be a reviewer

        # All returned reviewers should be available agents
        available_agent_ids = {"agent-2", "agent-3"}
        for reviewer in reviewers:
            assert reviewer in available_agent_ids

    @staticmethod
    def test_cyclomatic_complexity_estimation(code_review_engine: CodeReviewEngine) -> None:
        """Test cyclomatic complexity estimation."""
        simple_code = """
def simple_function() -> object:
    return True
"""
        complexity = code_review_engine._estimate_cyclomatic_complexity(simple_code)  # noqa: SLF001
        assert complexity == 1.0

        complex_code = """
def complex_function(x, y) -> object:
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x < 0:
        return -x
    else:
        for i in range(10):
            if i % 2 == 0:
                print(i)
        return 0
"""
        complexity = code_review_engine._estimate_cyclomatic_complexity(complex_code)  # noqa: SLF001
        assert complexity > 5.0

    @staticmethod
    def test_maintainability_index_calculation(code_review_engine: CodeReviewEngine) -> None:
        """Test maintainability index calculation."""
        well_documented_code = '''
"""Well documented module"""

def function() -> object:
    """Function with docstring"""
    # Comment explaining logic
    return True
'''

        mi = code_review_engine._calculate_maintainability_index(  # noqa: SLF001
            well_documented_code,
            10,
        )
        assert mi > 50.0

        # Poor code with no comments
        poor_code = "def f(): return True"
        mi = code_review_engine._calculate_maintainability_index(poor_code, 1)  # noqa: SLF001
        assert mi < 100.0

    @pytest.mark.asyncio
    async def test_full_automated_review_flow(
        self,
        code_review_engine: CodeReviewEngine,
        mock_collaboration_engine: Mock,  # noqa: ARG002
    ) -> None:
        """Test full automated review flow."""
        # Initiate review
        review_id = await code_review_engine.initiate_review(
            branch_name="feature/full-test",
            agent_id="agent-1",
            files_changed=["src/test_module.py"],
        )

        # Wait a bit for automated review to complete
        await asyncio.sleep(0.1)

        review = code_review_engine.active_reviews.get(review_id)
        if not review:
            # Review might have been auto-approved and moved to history
            review = next(
                (r for r in code_review_engine.review_history if r.review_id == review_id),
                None,
            )

        assert review is not None
        assert len(review.findings) > 0  # Should have found issues in test_module.py
        assert len(review.quality_metrics) > 0
        assert review.overall_score >= 0.0

        # Review should not be auto-approved due to security issues
        assert not review.auto_approved or review.overall_score < code_review_engine.review_config["auto_approve_threshold"]


class TestReviewDataClasses:
    """Test the review data classes."""

    @staticmethod
    def test_review_finding_creation() -> None:
        """Test ReviewFinding creation."""
        finding = ReviewFinding(
            finding_id="test_finding",
            review_type=ReviewType.SECURITY,
            severity=ReviewSeverity.HIGH,
            file_path="test.py",
            line_number=10,
            message="Security issue found",
            description="Detailed description",
            suggestion="Fix suggestion",
        )

        assert finding.finding_id == "test_finding"
        assert finding.review_type == ReviewType.SECURITY
        assert finding.severity == ReviewSeverity.HIGH
        assert finding.file_path == "test.py"
        assert finding.line_number == 10
        assert finding.message == "Security issue found"
        assert isinstance(finding.created_at, datetime)

    @staticmethod
    def test_quality_metrics_creation() -> None:
        """Test QualityMetrics creation."""
        metrics = QualityMetrics(
            file_path="test.py",
            metrics={
                QualityMetric.CYCLOMATIC_COMPLEXITY: 15.0,
                QualityMetric.LINES_OF_CODE: 100,
            },
            thresholds={
                QualityMetric.CYCLOMATIC_COMPLEXITY: 10.0,
            },
            violations=[QualityMetric.CYCLOMATIC_COMPLEXITY],
        )

        assert metrics.file_path == "test.py"
        assert metrics.metrics[QualityMetric.CYCLOMATIC_COMPLEXITY] == 15.0
        assert QualityMetric.CYCLOMATIC_COMPLEXITY in metrics.violations
        assert isinstance(metrics.calculated_at, datetime)

    @staticmethod
    def test_code_review_creation() -> None:
        """Test CodeReview creation."""
        review = CodeReview(
            review_id="test_review",
            branch_name="test_branch",
            agent_id="agent-1",
            reviewer_ids=["agent-2", "agent-3"],
            files_changed=["file1.py", "file2.py"],
            review_types=[ReviewType.STYLE_QUALITY, ReviewType.SECURITY],
        )

        assert review.review_id == "test_review"
        assert review.branch_name == "test_branch"
        assert review.agent_id == "agent-1"
        assert len(review.reviewer_ids) == 2
        assert len(review.files_changed) == 2
        assert review.status == ReviewStatus.PENDING
        assert isinstance(review.created_at, datetime)
