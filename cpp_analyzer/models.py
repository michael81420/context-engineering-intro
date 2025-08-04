"""
Core data models for C++ code analysis results.

This module contains Pydantic models that represent the structured analysis
results extracted from C++ source files using libclang.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class AccessSpecifier(Enum):
    """Access specifier for class members."""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    UNKNOWN = "unknown"


class ElementKind(Enum):
    """Kind of C++ code elements."""
    CLASS = "class"
    STRUCT = "struct"
    FUNCTION = "function"
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    DESTRUCTOR = "destructor"
    VARIABLE = "variable"
    FIELD = "field"
    NAMESPACE = "namespace"
    ENUM = "enum"
    ENUM_CONSTANT = "enum_constant"
    TEMPLATE = "template"
    TYPEDEF = "typedef"
    USING = "using"
    UNKNOWN = "unknown"


@dataclass
class SourceLocation:
    """Represents a location in source code."""
    file_path: str
    line: int
    column: int
    offset: int = 0

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line}:{self.column}"


class CodeElement(BaseModel):
    """Base class for all code elements."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "example_element",
                "kind": "function",
                "location": {
                    "file_path": "/path/to/file.cpp",
                    "line": 42,
                    "column": 10,
                    "offset": 1024
                }
            }
        }
    )

    name: str = Field(..., description="Name of the code element")
    kind: ElementKind = Field(..., description="Kind of the code element")
    location: SourceLocation = Field(..., description="Source location of the element")
    spelling: str = Field("", description="Exact spelling from source code")
    display_name: str = Field("", description="Display name with qualifications")


class ParameterInfo(BaseModel):
    """Information about a function parameter."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "value",
                "type_name": "const std::string&",
                "default_value": "\"default\"",
                "is_const": True,
                "is_reference": True,
                "is_pointer": False
            }
        }
    )

    name: str = Field(..., description="Parameter name")
    type_name: str = Field(..., description="Full type name including qualifiers")
    default_value: Optional[str] = Field(None, description="Default parameter value if any")
    is_const: bool = Field(False, description="Whether parameter type is const")
    is_reference: bool = Field(False, description="Whether parameter is a reference")
    is_pointer: bool = Field(False, description="Whether parameter is a pointer")


class VariableInfo(CodeElement):
    """Information about a variable or field."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "counter",
                "kind": "variable",
                "type_name": "static int",
                "is_const": False,
                "is_static": True,
                "access_specifier": "private",
                "initial_value": "0"
            }
        }
    )

    type_name: str = Field("", description="Full type name including qualifiers")
    is_const: bool = Field(False, description="Whether variable is const")
    is_static: bool = Field(False, description="Whether variable is static")
    is_mutable: bool = Field(False, description="Whether variable is mutable")
    access_specifier: AccessSpecifier = Field(AccessSpecifier.UNKNOWN, description="Access level")
    initial_value: Optional[str] = Field(None, description="Initial value if present")


class FunctionInfo(CodeElement):
    """Information about a function or method."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "calculate",
                "kind": "method",
                "return_type": "double",
                "parameters": [
                    {"name": "a", "type_name": "double", "is_const": False},
                    {"name": "b", "type_name": "double", "default_value": "1.0"}
                ],
                "is_virtual": True,
                "is_pure_virtual": False,
                "is_const": True,
                "access_specifier": "public"
            }
        }
    )

    return_type: str = Field("", description="Function return type")
    parameters: List[ParameterInfo] = Field(default_factory=list, description="Function parameters")
    is_virtual: bool = Field(False, description="Whether function is virtual")
    is_pure_virtual: bool = Field(False, description="Whether function is pure virtual")
    is_static: bool = Field(False, description="Whether function is static")
    is_const: bool = Field(False, description="Whether function is const")
    is_constructor: bool = Field(False, description="Whether function is a constructor")
    is_destructor: bool = Field(False, description="Whether function is a destructor")
    is_template: bool = Field(False, description="Whether function is a template")
    is_inline: bool = Field(False, description="Whether function is inline")
    access_specifier: AccessSpecifier = Field(AccessSpecifier.UNKNOWN, description="Access level")
    parent_class: Optional[str] = Field(None, description="Parent class name if method")
    template_parameters: List[str] = Field(default_factory=list, description="Template parameters")


class EnumInfo(CodeElement):
    """Information about an enumeration."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Status",
                "kind": "enum",
                "is_scoped": True,
                "underlying_type": "int",
                "values": [
                    {"name": "PENDING", "value": "0"},
                    {"name": "PROCESSING", "value": "1"}
                ]
            }
        }
    )

    is_scoped: bool = Field(False, description="Whether enum is scoped (enum class)")
    underlying_type: str = Field("", description="Underlying integer type")
    values: List[Dict[str, str]] = Field(default_factory=list, description="Enum values")
    access_specifier: AccessSpecifier = Field(AccessSpecifier.UNKNOWN, description="Access level")


class ClassInfo(CodeElement):
    """Information about a class or struct."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Calculator",
                "kind": "class",
                "base_classes": ["BaseCalculator", "Printable"],
                "methods": [],
                "fields": [],
                "is_abstract": True,
                "is_template": False,
                "namespace": "math"
            }
        }
    )

    base_classes: List[str] = Field(default_factory=list, description="Base class names")
    methods: List[FunctionInfo] = Field(default_factory=list, description="Class methods")
    fields: List[VariableInfo] = Field(default_factory=list, description="Class fields")
    nested_classes: List[ClassInfo] = Field(default_factory=list, description="Nested classes")
    nested_enums: List[EnumInfo] = Field(default_factory=list, description="Nested enums")
    is_abstract: bool = Field(False, description="Whether class is abstract")
    is_template: bool = Field(False, description="Whether class is a template")
    template_parameters: List[str] = Field(default_factory=list, description="Template parameters")
    access_specifier: AccessSpecifier = Field(AccessSpecifier.UNKNOWN, description="Access level")
    namespace: Optional[str] = Field(None, description="Containing namespace")


class NamespaceInfo(CodeElement):
    """Information about a namespace."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "std",
                "kind": "namespace",
                "classes": [],
                "functions": [],
                "variables": [],
                "nested_namespaces": [],
                "parent_namespace": None
            }
        }
    )

    classes: List[ClassInfo] = Field(default_factory=list, description="Classes in namespace")
    functions: List[FunctionInfo] = Field(default_factory=list, description="Functions in namespace")
    variables: List[VariableInfo] = Field(default_factory=list, description="Variables in namespace")
    enums: List[EnumInfo] = Field(default_factory=list, description="Enums in namespace")
    nested_namespaces: List[NamespaceInfo] = Field(default_factory=list, description="Nested namespaces")
    parent_namespace: Optional[str] = Field(None, description="Parent namespace name")


class IncludeInfo(BaseModel):
    """Information about an include directive."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_path": "iostream",
                "is_system_include": True,
                "is_found": True,
                "location": {
                    "file_path": "/path/to/source.cpp",
                    "line": 1,
                    "column": 1
                }
            }
        }
    )

    file_path: str = Field(..., description="Included file path")
    is_system_include: bool = Field(False, description="Whether it's a system include (<>)")
    is_found: bool = Field(True, description="Whether the include was found")
    location: SourceLocation = Field(..., description="Location of include directive")


class DiagnosticInfo(BaseModel):
    """Information about a compilation diagnostic."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "error",
                "message": "expected ';' after class definition",
                "location": {
                    "file_path": "/path/to/source.cpp",
                    "line": 42,
                    "column": 1
                },
                "category": "Parse Issue"
            }
        }
    )

    severity: str = Field(..., description="Diagnostic severity (error, warning, note)")
    message: str = Field(..., description="Diagnostic message")
    location: SourceLocation = Field(..., description="Location of the diagnostic")
    category: str = Field("", description="Diagnostic category")


class AnalysisResult(BaseModel):
    """Complete analysis result for a C++ file."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_path": "/path/to/source.cpp",
                "classes": [],
                "functions": [],
                "variables": [],
                "namespaces": [],
                "includes": [],
                "diagnostics": [],
                "analysis_metadata": {
                    "cpp_standard": "c++17",
                    "analysis_time": "2024-01-01T12:00:00",
                    "total_elements": 42
                }
            }
        }
    )

    file_path: str = Field(..., description="Path to the analyzed file")
    includes: List[IncludeInfo] = Field(default_factory=list, description="Include directives")
    namespaces: List[NamespaceInfo] = Field(default_factory=list, description="Top-level namespaces")
    classes: List[ClassInfo] = Field(default_factory=list, description="Top-level classes")
    functions: List[FunctionInfo] = Field(default_factory=list, description="Top-level functions")
    variables: List[VariableInfo] = Field(default_factory=list, description="Top-level variables")
    enums: List[EnumInfo] = Field(default_factory=list, description="Top-level enums")
    diagnostics: List[DiagnosticInfo] = Field(default_factory=list, description="Compilation diagnostics")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")

    def get_all_classes(self) -> List[ClassInfo]:
        """Get all classes including those in namespaces."""
        all_classes = list(self.classes)
        for namespace in self.namespaces:
            all_classes.extend(self._get_classes_from_namespace(namespace))
        return all_classes

    def _get_classes_from_namespace(self, namespace: NamespaceInfo) -> List[ClassInfo]:
        """Recursively get all classes from a namespace."""
        classes = list(namespace.classes)
        for nested_ns in namespace.nested_namespaces:
            classes.extend(self._get_classes_from_namespace(nested_ns))
        return classes

    def get_all_functions(self) -> List[FunctionInfo]:
        """Get all functions including methods and namespace functions."""
        all_functions = list(self.functions)
        
        # Add namespace functions
        for namespace in self.namespaces:
            all_functions.extend(self._get_functions_from_namespace(namespace))
        
        # Add class methods
        for class_info in self.get_all_classes():
            all_functions.extend(class_info.methods)
        
        return all_functions

    def _get_functions_from_namespace(self, namespace: NamespaceInfo) -> List[FunctionInfo]:
        """Recursively get all functions from a namespace."""
        functions = list(namespace.functions)
        for nested_ns in namespace.nested_namespaces:
            functions.extend(self._get_functions_from_namespace(nested_ns))
        return functions

    def get_statistics(self) -> Dict[str, int]:
        """Get analysis statistics."""
        return {
            "total_classes": len(self.get_all_classes()),
            "total_functions": len(self.get_all_functions()),
            "total_variables": len(self.variables),
            "total_namespaces": len(self.namespaces),
            "total_includes": len(self.includes),
            "total_diagnostics": len(self.diagnostics),
            "error_count": len([d for d in self.diagnostics if d.severity == "error"]),
            "warning_count": len([d for d in self.diagnostics if d.severity == "warning"])
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary."""
        return {
            "file_path": self.file_path,
            "statistics": self.get_statistics(),
            "includes": [
                {
                    "file_path": inc.file_path,
                    "is_system": inc.is_system_include,
                    "location": str(inc.location)
                } for inc in self.includes
            ],
            "namespaces": [ns.name for ns in self.namespaces],
            "classes": [cls.name for cls in self.get_all_classes()],
            "functions": [func.name for func in self.get_all_functions()],
            "variables": [var.name for var in self.variables],
            "diagnostics": [
                {
                    "severity": d.severity,
                    "message": d.message,
                    "location": str(d.location)
                } for d in self.diagnostics
            ],
            "metadata": self.analysis_metadata
        }


class ProjectAnalysisResult(BaseModel):
    """Analysis result for an entire project."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_path": "/path/to/project",
                "files_analyzed": ["/path/to/file1.cpp", "/path/to/file2.h"],
                "analysis_results": [],
                "summary_statistics": {
                    "total_files": 2,
                    "total_classes": 5,
                    "total_functions": 20
                }
            }
        }
    )

    project_path: str = Field(..., description="Path to the analyzed project")
    files_analyzed: List[str] = Field(default_factory=list, description="List of analyzed files")
    analysis_results: List[AnalysisResult] = Field(default_factory=list, description="Individual file results")
    summary_statistics: Dict[str, Any] = Field(default_factory=dict, description="Project-wide statistics")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

    def get_project_statistics(self) -> Dict[str, Any]:
        """Calculate project-wide statistics."""
        total_classes = sum(len(result.get_all_classes()) for result in self.analysis_results)
        total_functions = sum(len(result.get_all_functions()) for result in self.analysis_results)
        total_variables = sum(len(result.variables) for result in self.analysis_results)
        total_errors = sum(len([d for d in result.diagnostics if d.severity == "error"]) 
                          for result in self.analysis_results)
        total_warnings = sum(len([d for d in result.diagnostics if d.severity == "warning"]) 
                           for result in self.analysis_results)

        return {
            "total_files": len(self.files_analyzed),
            "total_classes": total_classes,
            "total_functions": total_functions,
            "total_variables": total_variables,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "files_with_errors": len([r for r in self.analysis_results 
                                    if any(d.severity == "error" for d in r.diagnostics)])
        }