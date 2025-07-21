"""Copyright notice."""
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""AST-based semantic conflict analysis engine for multi-agent development."""

import ast
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import object

from .branch_manager import BranchManager
from .conflict_resolution import ConflictSeverity, ResolutionStrategy

logger = logging.getLogger(__name__)


class SemanticConflictType(Enum):
    """Types of semantic conflicts that can be detected."""

    FUNCTION_SIGNATURE_CHANGE = "function_signature_change"
    CLASS_INTERFACE_CHANGE = "class_interface_change"
    API_BREAKING_CHANGE = "api_breaking_change"
    DATA_STRUCTURE_CHANGE = "data_structure_change"
    INHERITANCE_CONFLICT = "inheritance_conflict"
    DECORATOR_CONFLICT = "decorator_conflict"
    IMPORT_SEMANTIC_CONFLICT = "import_semantic_conflict"
    VARIABLE_TYPE_CONFLICT = "variable_type_conflict"
    CONTROL_FLOW_CONFLICT = "control_flow_conflict"
    EXCEPTION_HANDLING_CONFLICT = "exception_handling_conflict"


class SymbolVisibility(Enum):
    """Symbol visibility levels."""

    PUBLIC = "public"  # No leading underscore
    PROTECTED = "protected"  # Single leading underscore
    PRIVATE = "private"  # Double leading underscore
    MAGIC = "magic"  # Double leading and trailing underscore


@dataclass
class FunctionSignature:
    """Detailed function signature information."""

    name: str
    args: list[str]
    varargs: str | None = None
    kwonlyargs: list[str] = field(default_factory=list)
    defaults: list[str] = field(default_factory=list)
    kwdefaults: dict[str, str] = field(default_factory=dict)
    kwarg: str | None = None
    return_type: str | None = None
    decorators: list[str] = field(default_factory=list)
    visibility: SymbolVisibility = SymbolVisibility.PUBLIC
    line_number: int = 0
    docstring: str | None = None


@dataclass
class ClassDefinition:
    """Detailed class definition information."""

    name: str
    bases: list[str] = field(default_factory=list)
    methods: dict[str, FunctionSignature] = field(default_factory=dict)
    attributes: dict[str, str] = field(default_factory=dict)
    decorators: list[str] = field(default_factory=list)
    visibility: SymbolVisibility = SymbolVisibility.PUBLIC
    line_number: int = 0
    docstring: str | None = None
    metaclass: str | None = None


@dataclass
class ImportInfo:
    """Import statement information."""

    module: str
    name: str | None = None  # For from imports
    alias: str | None = None
    line_number: int = 0
    level: int = 0  # Relative import level


@dataclass
class SemanticContext:
    """Complete semantic context of a Python file."""

    file_path: str
    functions: dict[str, FunctionSignature] = field(default_factory=dict)
    classes: dict[str, ClassDefinition] = field(default_factory=dict)
    imports: list[ImportInfo] = field(default_factory=list)
    global_variables: dict[str, str] = field(default_factory=dict)
    constants: dict[str, str] = field(default_factory=dict)
    ast_hash: str = ""
    last_modified: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SemanticConflict:
    """Detected semantic conflict between two code versions."""

    conflict_id: str
    conflict_type: SemanticConflictType
    severity: ConflictSeverity
    symbol_name: str
    file_path: str
    branch1: str
    branch2: str
    description: str
    old_definition: str | None = None
    new_definition: str | None = None
    impact_analysis: dict[str, object] = field(default_factory=dict)
    suggested_resolution: ResolutionStrategy = ResolutionStrategy.HUMAN_REQUIRED
    metadata: dict[str, object] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SemanticAnalyzer:
    """Advanced AST-based semantic conflict analysis engine."""

    def __init__(self, branch_manager: BranchManager, repo_path: str | None = None) -> None:
        """Initialize the semantic analyzer.

        Args:
            branch_manager: BranchManager for branch operations
            repo_path: Path to git repository
        
        Returns:
            Description of return value
        """
        self.branch_manager = branch_manager
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        # Semantic context cache
        self.semantic_contexts: dict[str, SemanticContext] = {}
        self.conflict_cache: dict[str, list[SemanticConflict]] = {}

        # Analysis configuration
        self.enable_deep_analysis = True
        self.check_private_members = False
        self.check_docstring_changes = True
        self.check_type_hints = True

        # Performance tracking
        self.analysis_stats = {
            "files_analyzed": 0,
            "conflicts_detected": 0,
            "analysis_time": 0.0,
            "cache_hits": 0,
        }

    async def analyze_semantic_conflicts(
        self,
        branch1: str,
        branch2: str,
        file_paths: list[str] | None = None,
    ) -> list[SemanticConflict]:
        """Analyze semantic conflicts between two branches.

        Args:
            branch1: First branch name
            branch2: Second branch name
            file_paths: Specific files to analyze (None for all Python files)

        Returns:
            List of detected semantic conflicts
        """
        logger.info("Analyzing semantic conflicts between %s and %s", branch1, branch2)

        start_time = datetime.now(UTC)
        conflicts = []

        try:
            # Get files to analyze
            if file_paths is None:
                file_paths = await self._get_changed_python_files(branch1, branch2)

            # Analyze each file
            for file_path in file_paths:
                file_conflicts = await self._analyze_file_semantic_conflicts(
                    file_path,
                    branch1,
                    branch2,
                )
                conflicts.extend(file_conflicts)

                self.analysis_stats["files_analyzed"] += 1

            # Post-process conflicts
            conflicts = self._rank_conflicts_by_impact(conflicts)
            conflicts = self._merge_related_conflicts(conflicts)

            self.analysis_stats["conflicts_detected"] += len(conflicts)
            self.analysis_stats["analysis_time"] += (datetime.now(UTC) - start_time).total_seconds()

            logger.info("Found %d semantic conflicts", len(conflicts))

        except Exception:
            logger.exception("Error analyzing semantic conflicts")

        return conflicts

    async def _analyze_file_semantic_conflicts(
        self,
        file_path: str,
        branch1: str,
        branch2: str,
    ) -> list[SemanticConflict]:
        """Analyze semantic conflicts in a specific file."""
        conflicts: list[SemanticConflict] = []

        try:
            # Get semantic contexts for both branches
            context1 = await self._get_semantic_context(file_path, branch1)
            context2 = await self._get_semantic_context(file_path, branch2)

            if not context1 or not context2:
                return conflicts

            # Check function conflicts
            func_conflicts = self._detect_function_conflicts(
                context1,
                context2,
                branch1,
                branch2,
            )
            conflicts.extend(func_conflicts)

            # Check class conflicts
            class_conflicts = self._detect_class_conflicts(
                context1,
                context2,
                branch1,
                branch2,
            )
            conflicts.extend(class_conflicts)

            # Check import conflicts
            import_conflicts = self._detect_import_conflicts(
                context1,
                context2,
                branch1,
                branch2,
            )
            conflicts.extend(import_conflicts)

            # Check variable conflicts
            var_conflicts = self._detect_variable_conflicts(
                context1,
                context2,
                branch1,
                branch2,
            )
            conflicts.extend(var_conflicts)

        except Exception:
            logger.exception("Error analyzing file %s")

        return conflicts

    async def _get_semantic_context(
        self,
        file_path: str,
        branch: str,
    ) -> SemanticContext | None:
        """Get or create semantic context for a file in a specific branch."""
        cache_key = f"{branch}:{file_path}"

        # Check cache
        if cache_key in self.semantic_contexts:
            self.analysis_stats["cache_hits"] += 1
            return self.semantic_contexts[cache_key]

        try:
            # Get file content from branch
            content = await self._get_file_content(file_path, branch)
            if not content:
                return None

            # Parse AST and extract semantic information
            context = self._extract_semantic_context(file_path, content)

            # Cache the context
            self.semantic_contexts[cache_key] = context

            return context

        except Exception:
            logger.exception("Error getting semantic context for %s in %s")
            return None

    @staticmethod
    def _extract_semantic_context(
        self,
        file_path: str,
        content: str,
    ) -> SemanticContext:
        """Extract semantic context from Python source code."""
        context = SemanticContext(file_path=file_path)

        try:
            # Parse AST
            tree = ast.parse(content)

            # Calculate AST hash for change detection
            context.ast_hash = hashlib.sha256(content.encode()).hexdigest()

            # Extract semantic information
            visitor = SemanticVisitor()
            visitor.visit(tree)

            context.functions = visitor.functions
            context.classes = visitor.classes
            context.imports = visitor.imports
            context.global_variables = visitor.global_variables
            context.constants = visitor.constants

        except SyntaxError as e:
            logger.warning("Syntax error in %s: %s", file_path, e)
        except Exception:
            logger.exception("Error extracting semantic context")

        return context

    def _detect_function_conflicts(
        self,
        context1: SemanticContext,
        context2: SemanticContext,
        branch1: str,
        branch2: str,
    ) -> list[SemanticConflict]:
        """Detect function-related semantic conflicts."""
        conflicts = []

        # Find common functions
        common_functions = set(context1.functions.keys()) & set(
            context2.functions.keys(),
        )

        for func_name in common_functions:
            func1 = context1.functions[func_name]
            func2 = context2.functions[func_name]

            # Check signature changes
            if self._functions_have_signature_conflict(func1, func2):
                conflict = SemanticConflict(
                    conflict_id=f"func_sig_{branch1}_{branch2}_{func_name}",
                    conflict_type=SemanticConflictType.FUNCTION_SIGNATURE_CHANGE,
                    severity=self._assess_function_conflict_severity(func1, func2),
                    symbol_name=func_name,
                    file_path=context1.file_path,
                    branch1=branch1,
                    branch2=branch2,
                    description=f"Function signature conflict in {func_name}",
                    old_definition=self._signature_to_string(func1),
                    new_definition=self._signature_to_string(func2),
                    impact_analysis=self._analyze_function_impact(func1, func2),
                    suggested_resolution=self._suggest_function_resolution(
                        func1,
                        func2,
                    ),
                    metadata={
                        "old_signature": func1.__dict__,
                        "new_signature": func2.__dict__,
                        "visibility": func1.visibility.value,
                    },
                )
                conflicts.append(conflict)

        # Check for deleted/added functions
        deleted_functions = set(context1.functions.keys()) - set(
            context2.functions.keys(),
        )
        set(context2.functions.keys()) - set(
            context1.functions.keys(),
        )

        for func_name in deleted_functions:
            if not func_name.startswith("_") or self.check_private_members:
                conflict = SemanticConflict(
                    conflict_id=f"func_del_{branch1}_{branch2}_{func_name}",
                    conflict_type=SemanticConflictType.API_BREAKING_CHANGE,
                    severity=ConflictSeverity.HIGH,
                    symbol_name=func_name,
                    file_path=context1.file_path,
                    branch1=branch1,
                    branch2=branch2,
                    description=f"Function {func_name} deleted in {branch2}",
                    old_definition=self._signature_to_string(
                        context1.functions[func_name],
                    ),
                    new_definition=None,
                    suggested_resolution=ResolutionStrategy.HUMAN_REQUIRED,
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_class_conflicts(
        self,
        context1: SemanticContext,
        context2: SemanticContext,
        branch1: str,
        branch2: str,
    ) -> list[SemanticConflict]:
        """Detect class-related semantic conflicts."""
        conflicts = []

        # Find common classes
        common_classes = set(context1.classes.keys()) & set(context2.classes.keys())

        for class_name in common_classes:
            class1 = context1.classes[class_name]
            class2 = context2.classes[class_name]

            # Check inheritance changes
            if class1.bases != class2.bases:
                conflict = SemanticConflict(
                    conflict_id=f"class_inherit_{branch1}_{branch2}_{class_name}",
                    conflict_type=SemanticConflictType.INHERITANCE_CONFLICT,
                    severity=ConflictSeverity.HIGH,
                    symbol_name=class_name,
                    file_path=context1.file_path,
                    branch1=branch1,
                    branch2=branch2,
                    description=f"Class inheritance conflict in {class_name}",
                    old_definition=f"class {class_name}({', '.join(class1.bases)})",
                    new_definition=f"class {class_name}({', '.join(class2.bases)})",
                    metadata={"old_bases": class1.bases, "new_bases": class2.bases},
                )
                conflicts.append(conflict)

            # Check method conflicts
            method_conflicts = self._detect_method_conflicts(
                class1,
                class2,
                class_name,
                branch1,
                branch2,
                context1.file_path,
            )
            conflicts.extend(method_conflicts)

        return conflicts

    @staticmethod
    def _detect_import_conflicts(
        self,
        context1: SemanticContext,
        context2: SemanticContext,
        branch1: str,
        branch2: str,
    ) -> list[SemanticConflict]:
        """Detect import-related semantic conflicts."""
        conflicts = []

        # Compare imports
        {(imp.module, imp.name, imp.alias) for imp in context1.imports}
        {(imp.module, imp.name, imp.alias) for imp in context2.imports}

        # Check for conflicting imports (same name, different module)
        names1 = {imp.alias or imp.name or imp.module.split(".")[-1]: imp for imp in context1.imports}
        names2 = {imp.alias or imp.name or imp.module.split(".")[-1]: imp for imp in context2.imports}

        common_names = set(names1.keys()) & set(names2.keys())

        for name in common_names:
            imp1 = names1[name]
            imp2 = names2[name]

            if imp1.module != imp2.module:
                conflict = SemanticConflict(
                    conflict_id=f"import_conflict_{branch1}_{branch2}_{name}",
                    conflict_type=SemanticConflictType.IMPORT_SEMANTIC_CONFLICT,
                    severity=ConflictSeverity.MEDIUM,
                    symbol_name=name,
                    file_path=context1.file_path,
                    branch1=branch1,
                    branch2=branch2,
                    description=f"Import name conflict for {name}",
                    old_definition=f"from {imp1.module} import {imp1.name or '*'}" + (f" as {imp1.alias}" if imp1.alias else ""),
                    new_definition=f"from {imp2.module} import {imp2.name or '*'}" + (f" as {imp2.alias}" if imp2.alias else ""),
                    suggested_resolution=ResolutionStrategy.CUSTOM_MERGE,
                )
                conflicts.append(conflict)

        return conflicts

    @staticmethod
    def _detect_variable_conflicts(
        self,
        context1: SemanticContext,
        context2: SemanticContext,
        branch1: str,
        branch2: str,
    ) -> list[SemanticConflict]:
        """Detect variable-related semantic conflicts."""
        conflicts = []

        # Check global variables
        common_vars = set(context1.global_variables.keys()) & set(
            context2.global_variables.keys(),
        )

        for var_name in common_vars:
            type1 = context1.global_variables[var_name]
            type2 = context2.global_variables[var_name]

            if type1 != type2:
                conflict = SemanticConflict(
                    conflict_id=f"var_type_{branch1}_{branch2}_{var_name}",
                    conflict_type=SemanticConflictType.VARIABLE_TYPE_CONFLICT,
                    severity=ConflictSeverity.MEDIUM,
                    symbol_name=var_name,
                    file_path=context1.file_path,
                    branch1=branch1,
                    branch2=branch2,
                    description=f"Variable type conflict for {var_name}",
                    old_definition=f"{var_name}: {type1}",
                    new_definition=f"{var_name}: {type2}",
                    suggested_resolution=ResolutionStrategy.SEMANTIC_ANALYSIS,
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_method_conflicts(
        self,
        class1: ClassDefinition,
        class2: ClassDefinition,
        class_name: str,
        branch1: str,
        branch2: str,
        file_path: str,
    ) -> list[SemanticConflict]:
        """Detect method conflicts within a class."""
        conflicts = []

        common_methods = set(class1.methods.keys()) & set(class2.methods.keys())

        for method_name in common_methods:
            method1 = class1.methods[method_name]
            method2 = class2.methods[method_name]

            if self._functions_have_signature_conflict(method1, method2):
                conflict = SemanticConflict(
                    conflict_id=f"method_sig_{branch1}_{branch2}_{class_name}_{method_name}",
                    conflict_type=SemanticConflictType.CLASS_INTERFACE_CHANGE,
                    severity=self._assess_function_conflict_severity(method1, method2),
                    symbol_name=f"{class_name}.{method_name}",
                    file_path=file_path,
                    branch1=branch1,
                    branch2=branch2,
                    description=f"Method signature conflict in {class_name}.{method_name}",
                    old_definition=self._signature_to_string(method1),
                    new_definition=self._signature_to_string(method2),
                    suggested_resolution=self._suggest_function_resolution(
                        method1,
                        method2,
                    ),
                )
                conflicts.append(conflict)

        return conflicts

    def _functions_have_signature_conflict(
        self,
        func1: FunctionSignature,
        func2: FunctionSignature,
    ) -> bool:
        """Check if two function signatures have conflicts."""
        # Check argument changes
        if func1.args != func2.args:
            return True

        # Check default argument changes
        if func1.defaults != func2.defaults:
            return True

        # Check keyword-only arguments
        if func1.kwonlyargs != func2.kwonlyargs:
            return True

        # Check return type changes (if type hints are enabled)
        if self.check_type_hints and func1.return_type != func2.return_type:
            return True

        # Check decorator changes
        return func1.decorators != func2.decorators

    @staticmethod
    def _assess_function_conflict_severity(
        self,
        func1: FunctionSignature,
        func2: FunctionSignature,
    ) -> ConflictSeverity:
        """Assess the severity of a function signature conflict."""
        # Public functions with signature changes are more severe
        if func1.visibility == SymbolVisibility.PUBLIC:
            # Breaking changes (removed parameters, changed types)
            if len(func1.args) > len(func2.args):
                return ConflictSeverity.HIGH

            # Added required parameters
            if len(func1.args) < len(func2.args) and len(func1.defaults) == len(
                func2.defaults,
            ):
                return ConflictSeverity.HIGH

            # Return type changes
            if func1.return_type != func2.return_type:
                return ConflictSeverity.MEDIUM

            # Decorator changes
            if func1.decorators != func2.decorators:
                return ConflictSeverity.MEDIUM

        return ConflictSeverity.LOW

    @staticmethod
    def _analyze_function_impact(
        self,
        func1: FunctionSignature,
        func2: FunctionSignature,
    ) -> dict[str, object]:
        """Analyze the impact of function signature changes."""
        impact: dict[str, object] = {
            "breaking_change": False,
            "parameter_changes": [],
            "return_type_change": func1.return_type != func2.return_type,
            "decorator_changes": func1.decorators != func2.decorators,
        }

        # Analyze parameter changes
        if len(func1.args) > len(func2.args):
            impact["breaking_change"] = True
            removed_params = func1.args[len(func2.args) :]
            impact["parameter_changes"].append(
                f"Removed parameters: {', '.join(removed_params)}",
            )

        if len(func1.args) < len(func2.args):
            added_params = func2.args[len(func1.args) :]
            if len(func2.defaults) < len(added_params):
                impact["breaking_change"] = True
            impact["parameter_changes"].append(
                f"Added parameters: {', '.join(added_params)}",
            )

        return impact

    def _suggest_function_resolution(
        self,
        func1: FunctionSignature,
        func2: FunctionSignature,
    ) -> ResolutionStrategy:
        """Suggest resolution strategy for function conflicts."""
        # If it's a breaking change, require human intervention
        impact = self._analyze_function_impact(func1, func2)
        if impact["breaking_change"]:
            return ResolutionStrategy.HUMAN_REQUIRED

        # If only decorators changed, might be auto-resolvable
        if func1.args == func2.args and func1.decorators != func2.decorators:
            return ResolutionStrategy.SEMANTIC_ANALYSIS

        # Default to semantic analysis
        return ResolutionStrategy.SEMANTIC_ANALYSIS

    @staticmethod
    def _signature_to_string(func: FunctionSignature) -> str:
        """Convert function signature to string representation."""
        args = func.args.copy()

        # Add defaults
        if func.defaults:
            for i, default in enumerate(func.defaults):
                arg_idx = len(args) - len(func.defaults) + i
                args[arg_idx] = f"{args[arg_idx]}={default}"

        # Add varargs
        if func.varargs:
            args.append(f"*{func.varargs}")

        # Add keyword-only args
        for kwarg in func.kwonlyargs:
            if kwarg in func.kwdefaults:
                args.append(f"{kwarg}={func.kwdefaults[kwarg]}")
            else:
                args.append(kwarg)

        # Add kwargs
        if func.kwarg:
            args.append(f"**{func.kwarg}")

        signature = f"def {func.name}({', '.join(args)})"

        if func.return_type:
            signature += f" -> {func.return_type}"

        return signature

    @staticmethod
    def _rank_conflicts_by_impact(
        self,
        conflicts: list[SemanticConflict],
    ) -> list[SemanticConflict]:
        """Rank conflicts by their potential impact."""

        def conflict_priority(conflict: object) -> int:
            priority = 0

            # Severity weight
            severity_weights = {
                ConflictSeverity.CRITICAL: 1000,
                ConflictSeverity.HIGH: 100,
                ConflictSeverity.MEDIUM: 10,
                ConflictSeverity.LOW: 1,
            }
            priority += severity_weights.get(conflict.severity, 0)

            # Type weight
            type_weights = {
                SemanticConflictType.API_BREAKING_CHANGE: 500,
                SemanticConflictType.FUNCTION_SIGNATURE_CHANGE: 100,
                SemanticConflictType.CLASS_INTERFACE_CHANGE: 80,
                SemanticConflictType.INHERITANCE_CONFLICT: 60,
                SemanticConflictType.IMPORT_SEMANTIC_CONFLICT: 40,
                SemanticConflictType.VARIABLE_TYPE_CONFLICT: 20,
            }
            priority += type_weights.get(conflict.conflict_type, 0)

            # Public API weight
            if not conflict.symbol_name.startswith("_"):
                priority += 50

            return priority

        return sorted(conflicts, key=conflict_priority, reverse=True)

    @staticmethod
    def _merge_related_conflicts(
        self,
        conflicts: list[SemanticConflict],
    ) -> list[SemanticConflict]:
        """Merge related conflicts to reduce noise."""
        # Simple implementation - could be enhanced
        return conflicts

    # Helper methods

    @staticmethod
    async def _get_changed_python_files(branch1: str, branch2: str) -> list[str]:  # noqa: ARG002
        """Get list of Python files changed between branches."""
        try:
            # This would use git to find changed files
            # For now, return a placeholder
            return []
        except Exception:
            return []

    async def _get_file_content(self, file_path: str, branch: str) -> str | None:  # noqa: ARG002
        """Get file content from specific branch."""
        try:
            # This would use git to get file content from branch
            # For now, read from current working directory
            full_path = self.repo_path / file_path
            if full_path.exists() and full_path.suffix == ".py":
                with open(full_path, encoding="utf-8") as f:
                    return f.read()
        except Exception:
            logger.exception("Error reading file %s")
        return None

    def get_analysis_summary(self) -> dict[str, object]:
        """Get summary of semantic analysis."""
        return {
            "files_analyzed": self.analysis_stats["files_analyzed"],
            "conflicts_detected": self.analysis_stats["conflicts_detected"],
            "analysis_time": self.analysis_stats["analysis_time"],
            "cache_hits": self.analysis_stats["cache_hits"],
            "cache_size": len(self.semantic_contexts),
        }


class SemanticVisitor(ast.NodeVisitor):
    """AST visitor for extracting semantic information."""

    def __init__(self) -> None:
        self.functions: dict[str, FunctionSignature] = {}
        self.classes: dict[str, ClassDefinition] = {}
        self.imports: list[ImportInfo] = []
        self.global_variables: dict[str, str] = {}
        self.constants: dict[str, str] = {}
        self._current_class: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        signature = self._extract_function_signature(node)

        if self._current_class:
            # It's a method
            if self._current_class not in self.classes:
                self.classes[self._current_class] = ClassDefinition(
                    name=self._current_class,
                )
            self.classes[self._current_class].methods[node.name] = signature
        else:
            # It's a function
            self.functions[node.name] = signature

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        signature = self._extract_function_signature(node)
        signature.name = f"async {signature.name}"

        if self._current_class:
            if self._current_class not in self.classes:
                self.classes[self._current_class] = ClassDefinition(
                    name=self._current_class,
                )
            self.classes[self._current_class].methods[node.name] = signature
        else:
            self.functions[node.name] = signature

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        old_class = self._current_class
        self._current_class = node.name

        # Extract class information
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            else:
                decorators.append(ast.unparse(decorator))

        visibility = self._determine_visibility(node.name)
        docstring = ast.get_docstring(node)

        self.classes[node.name] = ClassDefinition(
            name=node.name,
            bases=bases,
            decorators=decorators,
            visibility=visibility,
            line_number=node.lineno,
            docstring=docstring,
        )

        self.generic_visit(node)
        self._current_class = old_class

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            import_info = ImportInfo(
                module=alias.name,
                alias=alias.asname,
                line_number=node.lineno,
            )
            self.imports.append(import_info)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from import statement."""
        module = node.module or ""
        level = node.level

        for alias in node.names:
            import_info = ImportInfo(
                module=module,
                name=alias.name,
                alias=alias.asname,
                line_number=node.lineno,
                level=level,
            )
            self.imports.append(import_info)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment for global variables."""
        if self._current_class is None:  # Only global assignments
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id

                    # Try to determine type
                    var_type = self._infer_type(node.value)

                    if var_name.isupper():
                        self.constants[var_name] = var_type
                    else:
                        self.global_variables[var_name] = var_type

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignment."""
        if self._current_class is None and isinstance(node.target, ast.Name):
            var_name = node.target.id
            var_type = ast.unparse(node.annotation)

            if var_name.isupper():
                self.constants[var_name] = var_type
            else:
                self.global_variables[var_name] = var_type

        self.generic_visit(node)

    def _extract_function_signature(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionSignature:
        """Extract detailed function signature."""
        args = []
        defaults = []
        kwonlyargs = []
        kwdefaults = {}

        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Default arguments
        if node.args.defaults:
            for default in node.args.defaults:
                defaults.append(ast.unparse(default))

        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            kwonlyargs.append(arg_str)

        # Keyword defaults
        if node.args.kw_defaults:
            for i, default in enumerate(node.args.kw_defaults):
                if default and i < len(kwonlyargs):
                    kwdefaults[kwonlyargs[i]] = ast.unparse(default)

        # Varargs and kwargs
        varargs = node.args.vararg.arg if node.args.vararg else None
        kwarg = node.args.kwarg.arg if node.args.kwarg else None

        # Return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            else:
                decorators.append(ast.unparse(decorator))

        # Visibility
        visibility = self._determine_visibility(node.name)

        # Docstring
        docstring = ast.get_docstring(node)

        return FunctionSignature(
            name=node.name,
            args=args,
            varargs=varargs,
            kwonlyargs=kwonlyargs,
            defaults=defaults,
            kwdefaults=kwdefaults,
            kwarg=kwarg,
            return_type=return_type,
            decorators=decorators,
            visibility=visibility,
            line_number=node.lineno,
            docstring=docstring,
        )

    @staticmethod
    def _determine_visibility(name: str) -> SymbolVisibility:
        """Determine symbol visibility based on naming convention."""
        if name.startswith("__") and name.endswith("__"):
            return SymbolVisibility.MAGIC
        if name.startswith("__"):
            return SymbolVisibility.PRIVATE
        if name.startswith("_"):
            return SymbolVisibility.PROTECTED
        return SymbolVisibility.PUBLIC

    @staticmethod
    def _infer_type(node: ast.expr) -> str:
        """Simple type inference for AST nodes."""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        if isinstance(node, ast.List):
            return "list"
        if isinstance(node, ast.Dict):
            return "dict"
        if isinstance(node, ast.Set):
            return "set"
        if isinstance(node, ast.Tuple):
            return "tuple"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id

        return "unknown"
