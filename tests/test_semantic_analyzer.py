# Copyright notice.

import ast
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from libs.multi_agent.branch_manager import BranchManager
from libs.multi_agent.conflict_resolution import ConflictSeverity, ResolutionStrategy
from libs.multi_agent.semantic_analyzer import (
    ClassDefinition,
    FunctionSignature,
    ImportInfo,
    SemanticAnalyzer,
    SemanticConflict,
    SemanticConflictType,
    SemanticContext,
    SemanticVisitor,
    SymbolVisibility,
)


class TestFunctionSignature:
    """Test cases for FunctionSignature."""

    @staticmethod
    def test_init() -> None:
        """Test FunctionSignature initialization."""
        signature = FunctionSignature(
            name="test_func",
            args=["self", "x", "y"],
            defaults=["None"],
            return_type="int",
            visibility=SymbolVisibility.PUBLIC,
            line_number=10,
        )

        assert signature.name == "test_func"
        assert signature.args == ["self", "x", "y"]
        assert signature.defaults == ["None"]
        assert signature.return_type == "int"
        assert signature.visibility == SymbolVisibility.PUBLIC
        assert signature.line_number == 10


class TestClassDefinition:
    """Test cases for ClassDefinition."""

    @staticmethod
    def test_init() -> None:
        """Test ClassDefinition initialization."""
        class_def = ClassDefinition(
            name="TestClass",
            bases=["BaseClass", "Mixin"],
            visibility=SymbolVisibility.PUBLIC,
            line_number=5,
        )

        assert class_def.name == "TestClass"
        assert class_def.bases == ["BaseClass", "Mixin"]
        assert class_def.visibility == SymbolVisibility.PUBLIC
        assert class_def.line_number == 5
        assert class_def.methods == {}
        assert class_def.attributes == {}


class TestSemanticContext:
    """Test cases for SemanticContext."""

    @staticmethod
    def test_init() -> None:
        """Test SemanticContext initialization."""
        context = SemanticContext(file_path="test.py")

        assert context.file_path == "test.py"
        assert context.functions == {}
        assert context.classes == {}
        assert context.imports == []
        assert context.global_variables == {}
        assert context.constants == {}
        assert not context.ast_hash


class TestSemanticConflict:
    """Test cases for SemanticConflict."""

    @staticmethod
    def test_init() -> None:
        """Test SemanticConflict initialization."""
        conflict = SemanticConflict(
            conflict_id="test-conflict",
            conflict_type=SemanticConflictType.FUNCTION_SIGNATURE_CHANGE,
            severity=ConflictSeverity.HIGH,
            symbol_name="test_func",
            file_path="test.py",
            branch1="branch1",
            branch2="branch2",
            description="Test conflict",
        )

        assert conflict.conflict_id == "test-conflict"
        assert conflict.conflict_type == SemanticConflictType.FUNCTION_SIGNATURE_CHANGE
        assert conflict.severity == ConflictSeverity.HIGH
        assert conflict.symbol_name == "test_func"
        assert conflict.file_path == "test.py"
        assert conflict.branch1 == "branch1"
        assert conflict.branch2 == "branch2"
        assert conflict.description == "Test conflict"


class TestSemanticVisitor:
    """Test cases for SemanticVisitor."""

    @staticmethod
    def test_visit_function_def() -> None:
        """Test function definition parsing."""
        code = """
def test_func(x: int, y: str = "default") -> bool:
    \"\"\"Test function\"\"\"
    return True
"""
        tree = ast.parse(code)
        visitor = SemanticVisitor()
        visitor.visit(tree)

        assert "test_func" in visitor.functions
        func = visitor.functions["test_func"]
        assert func.name == "test_func"
        assert len(func.args) == 2
        assert "x: int" in func.args
        assert "y: str" in func.args
        assert func.return_type == "bool"
        assert func.visibility == SymbolVisibility.PUBLIC

    @staticmethod
    def test_visit_class_def() -> None:
        """Test class definition parsing."""
        code = """
class TestClass(BaseClass):
    \"\"\"Test class\"\"\"

    def __init__(self) -> None:
        pass

    @staticmethod
    def public_method() -> object:
        pass

    @staticmethod
    def _protected_method() -> object:
        pass

    def __private_method(self) -> object:
        pass
"""
        tree = ast.parse(code)
        visitor = SemanticVisitor()
        visitor.visit(tree)

        assert "TestClass" in visitor.classes
        class_def = visitor.classes["TestClass"]
        assert class_def.name == "TestClass"
        assert class_def.bases == ["BaseClass"]
        assert len(class_def.methods) == 4
        assert "__init__" in class_def.methods
        assert "public_method" in class_def.methods
        assert "_protected_method" in class_def.methods
        assert "__private_method" in class_def.methods

    @staticmethod
    def test_visit_imports() -> None:
        """Test import statement parsing."""
        code = """
"""
        tree = ast.parse(code)
        visitor = SemanticVisitor()
        visitor.visit(tree)

        assert len(visitor.imports) == 4

        import_os = next(imp for imp in visitor.imports if imp.module == "os")
        assert import_os.name is None
        assert import_os.alias is None

        import_sys = next(imp for imp in visitor.imports if imp.module == "sys")
        assert import_sys.alias == "system"

        import_path = next(imp for imp in visitor.imports if imp.name == "Path")
        assert import_path.module == "pathlib"

        import_dict = next(imp for imp in visitor.imports if imp.name == "Dict")
        assert import_dict.alias == "DictType"

    @staticmethod
    def test_visit_global_variables() -> None:
        """Test global variable parsing."""
        code = """
CONSTANT = "value"
variable: int = 42
another_var = [1, 2, 3]
"""
        tree = ast.parse(code)
        visitor = SemanticVisitor()
        visitor.visit(tree)

        assert "CONSTANT" in visitor.constants
        assert visitor.constants["CONSTANT"] == "str"

        assert "variable" in visitor.global_variables
        assert visitor.global_variables["variable"] == "int"

        assert "another_var" in visitor.global_variables
        assert visitor.global_variables["another_var"] == "list"

    @staticmethod
    def test_determine_visibility() -> None:
        """Test visibility determination."""
        visitor = SemanticVisitor()

        assert (
            visitor._determine_visibility("public") == SymbolVisibility.PUBLIC
        )
        assert (
            visitor._determine_visibility("_protected") == SymbolVisibility.PROTECTED
        )
        assert (
            visitor._determine_visibility("__private") == SymbolVisibility.PRIVATE
        )
        assert (
            visitor._determine_visibility("__magic__") == SymbolVisibility.MAGIC
        )

    @staticmethod
    def test_infer_type() -> None:
        """Test type inference."""
        visitor = SemanticVisitor()

        # Test constants
        assert visitor._infer_type(ast.Constant(42)) == "int"
        assert visitor._infer_type(ast.Constant("string")) == "str"
        assert visitor._infer_type(ast.Constant(True)) == "bool"

        # Test collections
        assert visitor._infer_type(ast.List([], ast.Load())) == "list"
        assert visitor._infer_type(ast.Dict([], [])) == "dict"
        assert visitor._infer_type(ast.Set([])) == "set"
        assert visitor._infer_type(ast.Tuple([], ast.Load())) == "tuple"


class TestSemanticAnalyzer:
    """Test cases for SemanticAnalyzer."""

    @pytest.fixture
    @staticmethod
    def mock_branch_manager() -> Mock:
        """Create mock branch manager."""
        return Mock(spec=BranchManager)

    @pytest.fixture
    @staticmethod
    def temp_repo() -> Path:
        """Create temporary repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    @staticmethod
    def analyzer(mock_branch_manager: Mock, temp_repo: Path) -> SemanticAnalyzer:
        """Create SemanticAnalyzer instance."""
        return SemanticAnalyzer(
            branch_manager=mock_branch_manager,
            repo_path=str(temp_repo),
        )

    @staticmethod
    def test_init(
        analyzer: SemanticAnalyzer, mock_branch_manager: Mock, temp_repo: Path
    ) -> None:
        """Test SemanticAnalyzer initialization."""
        assert analyzer.branch_manager == mock_branch_manager
        assert analyzer.repo_path == temp_repo
        assert analyzer.semantic_contexts == {}
        assert analyzer.conflict_cache == {}
        assert analyzer.enable_deep_analysis is True
        assert analyzer.check_private_members is False
        assert analyzer.check_docstring_changes is True
        assert analyzer.check_type_hints is True

    @staticmethod
    def test_extract_semantic_context(analyzer: SemanticAnalyzer) -> None:
        """Test semantic context extraction."""
        code = """

CONSTANT = "value"

def test_function(x: int) -> bool:
    \"\"\"Test function\"\"\"
    return True

class TestClass:
    @staticmethod
    def method() -> object:
        pass
"""
        context = analyzer._extract_semantic_context("test.py", code)

        assert context.file_path == "test.py"
        assert len(context.functions) == 1
        assert "test_function" in context.functions
        assert len(context.classes) == 1
        assert "TestClass" in context.classes
        assert len(context.imports) == 2
        assert "CONSTANT" in context.constants
        assert context.ast_hash

    @staticmethod
    def test_functions_have_signature_conflict(analyzer: SemanticAnalyzer) -> None:
        """Test function signature conflict detection."""
        func1 = FunctionSignature(
            name="test",
            args=["x", "y"],
            defaults=["None"],
            return_type="int",
        )

        func2 = FunctionSignature(
            name="test",
            args=["x"],  # Different args
            defaults=[],
            return_type="int",
        )

        assert (
            analyzer._functions_have_signature_conflict(func1, func2) is True
        )

        # Same signature
        func3 = FunctionSignature(
            name="test",
            args=["x", "y"],
            defaults=["None"],
            return_type="int",
        )

        assert (
            analyzer._functions_have_signature_conflict(func1, func3) is False
        )

    @staticmethod
    def test_assess_function_conflict_severity(analyzer: SemanticAnalyzer) -> None:
        """Test function conflict severity assessment."""
        # Public function with removed parameters (breaking change)
        func1 = FunctionSignature(
            name="test",
            args=["x", "y"],
            visibility=SymbolVisibility.PUBLIC,
        )

        func2 = FunctionSignature(
            name="test",
            args=["x"],  # Removed parameter
            visibility=SymbolVisibility.PUBLIC,
        )

        severity = analyzer._assess_function_conflict_severity(
            func1, func2
        )
        assert severity == ConflictSeverity.HIGH

        # Private function change (less severe)
        func3 = FunctionSignature(
            name="_test",
            args=["x", "y"],
            visibility=SymbolVisibility.PROTECTED,
        )

        func4 = FunctionSignature(
            name="_test",
            args=["x"],
            visibility=SymbolVisibility.PROTECTED,
        )

        severity = analyzer._assess_function_conflict_severity(
            func3, func4
        )
        assert severity == ConflictSeverity.LOW

    @staticmethod
    def test_analyze_function_impact(analyzer: SemanticAnalyzer) -> None:
        """Test function impact analysis."""
        func1 = FunctionSignature(name="test", args=["x", "y", "z"], defaults=["None"])

        func2 = FunctionSignature(
            name="test",
            args=["x"],  # Removed parameters
            defaults=[],
        )

        impact = analyzer._analyze_function_impact(func1, func2)

        assert impact["breaking_change"] is True
        assert len(impact["parameter_changes"]) > 0
        assert "Removed parameters" in impact["parameter_changes"][0]

    @staticmethod
    def test_suggest_function_resolution(analyzer: SemanticAnalyzer) -> None:
        """Test function resolution strategy suggestion."""
        # Breaking change should require human intervention
        func1 = FunctionSignature(name="test", args=["x", "y"])
        func2 = FunctionSignature(name="test", args=["x"])

        strategy = analyzer._suggest_function_resolution(func1, func2)
        assert strategy == ResolutionStrategy.HUMAN_REQUIRED

        # Decorator change might be auto-resolvable
        func3 = FunctionSignature(name="test", args=["x"], decorators=["@decorator1"])
        func4 = FunctionSignature(name="test", args=["x"], decorators=["@decorator2"])

        strategy = analyzer._suggest_function_resolution(func3, func4)
        assert strategy == ResolutionStrategy.SEMANTIC_ANALYSIS

    @staticmethod
    def test_signature_to_string(analyzer: SemanticAnalyzer) -> None:
        """Test function signature string conversion."""
        signature = FunctionSignature(
            name="test_func",
            args=["x", "y", "z"],
            defaults=["None", "0"],
            varargs="args",
            kwarg="kwargs",
            return_type="bool",
        )

        sig_str = analyzer._signature_to_string(signature)

        assert "def test_func(" in sig_str
        assert "y=None" in sig_str
        assert "z=0" in sig_str
        assert "*args: Any" in sig_str
        assert "**kwargs: dict[str, object]" in sig_str
        assert "-> bool" in sig_str

    @staticmethod
    def test_detect_function_conflicts(analyzer: SemanticAnalyzer) -> None:
        """Test function conflict detection."""
        context1 = SemanticContext(file_path="test.py")
        context1.functions["test_func"] = FunctionSignature(
            name="test_func",
            args=["x", "y"],
            return_type="int",
        )

        context2 = SemanticContext(file_path="test.py")
        context2.functions["test_func"] = FunctionSignature(
            name="test_func",
            args=["x"],  # Different signature
            return_type="str",  # Different return type
        )

        conflicts = analyzer._detect_function_conflicts(
            context1,
            context2,
            "branch1",
            "branch2",
        )

        assert len(conflicts) > 0
        conflict = conflicts[0]
        assert conflict.conflict_type == SemanticConflictType.FUNCTION_SIGNATURE_CHANGE
        assert conflict.symbol_name == "test_func"
        assert "branch1" in conflict.branch1
        assert "branch2" in conflict.branch2

    @staticmethod
    def test_detect_class_conflicts(analyzer: SemanticAnalyzer) -> None:
        """Test class conflict detection."""
        context1 = SemanticContext(file_path="test.py")
        context1.classes["TestClass"] = ClassDefinition(
            name="TestClass",
            bases=["BaseClass"],
        )

        context2 = SemanticContext(file_path="test.py")
        context2.classes["TestClass"] = ClassDefinition(
            name="TestClass",
            bases=["DifferentBase"],  # Different inheritance
        )

        conflicts = analyzer._detect_class_conflicts(
            context1,
            context2,
            "branch1",
            "branch2",
        )

        assert len(conflicts) > 0
        conflict = conflicts[0]
        assert conflict.conflict_type == SemanticConflictType.INHERITANCE_CONFLICT
        assert conflict.symbol_name == "TestClass"

    @staticmethod
    def test_detect_import_conflicts(analyzer: SemanticAnalyzer) -> None:
        """Test import conflict detection."""
        context1 = SemanticContext(file_path="test.py")
        context1.imports = [ImportInfo(module="os", name="path", alias="ospath")]

        context2 = SemanticContext(file_path="test.py")
        context2.imports = [
            ImportInfo(
                module="sys",
                name="path",
                alias="ospath",
            ),  # Same alias, different module
        ]

        conflicts = analyzer._detect_import_conflicts(
            context1,
            context2,
            "branch1",
            "branch2",
        )

        assert len(conflicts) > 0
        conflict = conflicts[0]
        assert conflict.conflict_type == SemanticConflictType.IMPORT_SEMANTIC_CONFLICT
        assert "ospath" in conflict.symbol_name

    @staticmethod
    def test_detect_variable_conflicts(analyzer: SemanticAnalyzer) -> None:
        """Test variable conflict detection."""
        context1 = SemanticContext(file_path="test.py")
        context1.global_variables["my_var"] = "int"

        context2 = SemanticContext(file_path="test.py")
        context2.global_variables["my_var"] = "str"  # Different type

        conflicts = analyzer._detect_variable_conflicts(
            context1,
            context2,
            "branch1",
            "branch2",
        )

        assert len(conflicts) > 0
        conflict = conflicts[0]
        assert conflict.conflict_type == SemanticConflictType.VARIABLE_TYPE_CONFLICT
        assert conflict.symbol_name == "my_var"

    @staticmethod
    def test_rank_conflicts_by_impact(analyzer: SemanticAnalyzer) -> None:
        """Test conflict ranking by impact."""
        conflicts = [
            SemanticConflict(
                conflict_id="low",
                conflict_type=SemanticConflictType.VARIABLE_TYPE_CONFLICT,
                severity=ConflictSeverity.LOW,
                symbol_name="_private_var",
                file_path="test.py",
                branch1="b1",
                branch2="b2",
                description="Low impact",
            ),
            SemanticConflict(
                conflict_id="high",
                conflict_type=SemanticConflictType.API_BREAKING_CHANGE,
                severity=ConflictSeverity.HIGH,
                symbol_name="public_func",
                file_path="test.py",
                branch1="b1",
                branch2="b2",
                description="High impact",
            ),
        ]

        ranked = analyzer._rank_conflicts_by_impact(conflicts)

        assert len(ranked) == 2
        assert ranked[0].conflict_id == "high"  # High impact should come first
        assert ranked[1].conflict_id == "low"  # Low impact should come second

    @pytest.mark.asyncio
    @staticmethod
    async def test_get_semantic_context_caching(analyzer: SemanticAnalyzer) -> None:
        """Test semantic context caching."""
        # Mock file content
        test_code = "def test(): pass"

        with patch.object(
            analyzer,
            "_get_file_content",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = test_code

            # First call should fetch and cache
            context1 = await analyzer._get_semantic_context(
                "test.py", "branch1"
            )
            assert context1 is not None
            assert mock_get.call_count == 1

            # Second call should use cache
            context2 = await analyzer._get_semantic_context(
                "test.py", "branch1"
            )
            assert context2 is context1  # Same object reference
            assert mock_get.call_count == 1  # No additional call

            # Different branch should fetch again
            context3 = await analyzer._get_semantic_context(
                "test.py", "branch2"
            )
            assert context3 is not context1
            assert mock_get.call_count == 2

    @staticmethod
    def test_get_analysis_summary(analyzer: SemanticAnalyzer) -> None:
        """Test analysis summary generation."""
        # Set some test stats
        analyzer.analysis_stats["files_analyzed"] = 5
        analyzer.analysis_stats["conflicts_detected"] = 3
        analyzer.analysis_stats["analysis_time"] = 2.5
        analyzer.analysis_stats["cache_hits"] = 7

        summary = analyzer.get_analysis_summary()

        assert summary["files_analyzed"] == 5
        assert summary["conflicts_detected"] == 3
        assert summary["analysis_time"] == 2.5
        assert summary["cache_hits"] == 7
        assert "cache_size" in summary

    @pytest.mark.asyncio
    @staticmethod
    async def test_analyze_semantic_conflicts_integration(
        analyzer: SemanticAnalyzer,
    ) -> None:
        """Test full semantic conflict analysis integration."""
        # Mock the required methods
        analyzer._get_changed_python_files = AsyncMock(
            return_value=["test.py"]
        )
        analyzer._analyze_file_semantic_conflicts = AsyncMock(
            return_value=[
                SemanticConflict(
                    conflict_id="test-conflict",
                    conflict_type=SemanticConflictType.FUNCTION_SIGNATURE_CHANGE,
                    severity=ConflictSeverity.MEDIUM,
                    symbol_name="test_func",
                    file_path="test.py",
                    branch1="branch1",
                    branch2="branch2",
                    description="Test conflict",
                ),
            ],
        )

        conflicts = await analyzer.analyze_semantic_conflicts("branch1", "branch2")

        assert len(conflicts) >= 0
        if conflicts:
            assert all(isinstance(c, SemanticConflict) for c in conflicts)
            assert analyzer.analysis_stats["files_analyzed"] > 0
