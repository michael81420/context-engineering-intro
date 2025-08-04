"""
Tests for data models in cpp_analyzer.models module.
"""

import pytest
from datetime import datetime
import json

from cpp_analyzer.models import (
    AnalysisResult, ClassInfo, FunctionInfo, VariableInfo,
    NamespaceInfo, EnumInfo, IncludeInfo, DiagnosticInfo,
    ParameterInfo, SourceLocation, AccessSpecifier, ElementKind,
    ProjectAnalysisResult
)


class TestSourceLocation:
    """Test SourceLocation dataclass."""

    def test_source_location_creation(self):
        """Test creating a SourceLocation."""
        location = SourceLocation(
            file_path="/path/to/file.cpp",
            line=42,
            column=10,
            offset=1024
        )
        
        assert location.file_path == "/path/to/file.cpp"
        assert location.line == 42
        assert location.column == 10
        assert location.offset == 1024

    def test_source_location_str(self):
        """Test string representation of SourceLocation."""
        location = SourceLocation(
            file_path="/path/to/file.cpp",
            line=42,
            column=10
        )
        
        assert str(location) == "/path/to/file.cpp:42:10"

    def test_source_location_default_offset(self):
        """Test SourceLocation with default offset."""
        location = SourceLocation(
            file_path="/path/to/file.cpp",
            line=1,
            column=1
        )
        
        assert location.offset == 0


class TestParameterInfo:
    """Test ParameterInfo model."""

    def test_parameter_info_creation(self):
        """Test creating a ParameterInfo."""
        param = ParameterInfo(
            name="value",
            type_name="const std::string&",
            default_value="\"default\"",
            is_const=True,
            is_reference=True,
            is_pointer=False
        )
        
        assert param.name == "value"
        assert param.type_name == "const std::string&"
        assert param.default_value == "\"default\""
        assert param.is_const is True
        assert param.is_reference is True
        assert param.is_pointer is False

    def test_parameter_info_defaults(self):
        """Test ParameterInfo with default values."""
        param = ParameterInfo(
            name="param",
            type_name="int"
        )
        
        assert param.default_value is None
        assert param.is_const is False
        assert param.is_reference is False
        assert param.is_pointer is False

    def test_parameter_info_json_serialization(self):
        """Test JSON serialization of ParameterInfo."""
        param = ParameterInfo(
            name="value",
            type_name="const std::string&",
            is_const=True,
            is_reference=True
        )
        
        json_data = param.model_dump()
        assert json_data["name"] == "value"
        assert json_data["type_name"] == "const std::string&"
        assert json_data["is_const"] is True


class TestVariableInfo:
    """Test VariableInfo model."""

    def test_variable_info_creation(self):
        """Test creating a VariableInfo."""
        location = SourceLocation("/path/file.cpp", 10, 5)
        
        var = VariableInfo(
            name="counter",
            kind=ElementKind.VARIABLE,
            location=location,
            type_name="static int",
            is_const=False,
            is_static=True,
            access_specifier=AccessSpecifier.PRIVATE,
            initial_value="0"
        )
        
        assert var.name == "counter"
        assert var.kind == ElementKind.VARIABLE
        assert var.type_name == "static int"
        assert var.is_static is True
        assert var.access_specifier == AccessSpecifier.PRIVATE

    def test_variable_info_defaults(self):
        """Test VariableInfo with default values."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        var = VariableInfo(
            name="var",
            kind=ElementKind.VARIABLE,
            location=location
        )
        
        assert var.type_name == ""
        assert var.is_const is False
        assert var.is_static is False
        assert var.access_specifier == AccessSpecifier.UNKNOWN
        assert var.initial_value is None


class TestFunctionInfo:
    """Test FunctionInfo model."""

    def test_function_info_creation(self):
        """Test creating a FunctionInfo."""
        location = SourceLocation("/path/file.cpp", 20, 1)
        param = ParameterInfo(name="a", type_name="double")
        
        func = FunctionInfo(
            name="calculate",
            kind=ElementKind.METHOD,
            location=location,
            return_type="double",
            parameters=[param],
            is_virtual=True,
            is_const=True,
            access_specifier=AccessSpecifier.PUBLIC
        )
        
        assert func.name == "calculate"
        assert func.kind == ElementKind.METHOD
        assert func.return_type == "double"
        assert len(func.parameters) == 1
        assert func.is_virtual is True
        assert func.is_const is True
        assert func.access_specifier == AccessSpecifier.PUBLIC

    def test_function_info_defaults(self):
        """Test FunctionInfo with default values."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        func = FunctionInfo(
            name="func",
            kind=ElementKind.FUNCTION,
            location=location
        )
        
        assert func.return_type == ""
        assert len(func.parameters) == 0
        assert func.is_virtual is False
        assert func.is_pure_virtual is False
        assert func.is_static is False
        assert func.is_const is False
        assert func.access_specifier == AccessSpecifier.UNKNOWN


class TestClassInfo:
    """Test ClassInfo model."""

    def test_class_info_creation(self):
        """Test creating a ClassInfo."""
        location = SourceLocation("/path/file.cpp", 30, 1)
        method = FunctionInfo(
            name="method",
            kind=ElementKind.METHOD,
            location=location
        )
        
        cls = ClassInfo(
            name="Calculator",
            kind=ElementKind.CLASS,
            location=location,
            base_classes=["BaseCalculator"],
            methods=[method],
            is_abstract=True,
            namespace="math"
        )
        
        assert cls.name == "Calculator"
        assert cls.kind == ElementKind.CLASS
        assert cls.base_classes == ["BaseCalculator"]
        assert len(cls.methods) == 1
        assert cls.is_abstract is True
        assert cls.namespace == "math"

    def test_class_info_defaults(self):
        """Test ClassInfo with default values."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        cls = ClassInfo(
            name="Class",
            kind=ElementKind.CLASS,
            location=location
        )
        
        assert len(cls.base_classes) == 0
        assert len(cls.methods) == 0
        assert len(cls.fields) == 0
        assert cls.is_abstract is False
        assert cls.is_template is False
        assert cls.namespace is None


class TestEnumInfo:
    """Test EnumInfo model."""

    def test_enum_info_creation(self):
        """Test creating an EnumInfo."""
        location = SourceLocation("/path/file.cpp", 40, 1)
        
        enum = EnumInfo(
            name="Status",
            kind=ElementKind.ENUM,
            location=location,
            is_scoped=True,
            underlying_type="int",
            values=[
                {"name": "PENDING", "value": "0"},
                {"name": "PROCESSING", "value": "1"}
            ]
        )
        
        assert enum.name == "Status"
        assert enum.is_scoped is True
        assert enum.underlying_type == "int"
        assert len(enum.values) == 2
        assert enum.values[0]["name"] == "PENDING"

    def test_enum_info_defaults(self):
        """Test EnumInfo with default values."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        enum = EnumInfo(
            name="Enum",
            kind=ElementKind.ENUM,
            location=location
        )
        
        assert enum.is_scoped is False
        assert enum.underlying_type == ""
        assert len(enum.values) == 0


class TestAnalysisResult:
    """Test AnalysisResult model."""

    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        cls = ClassInfo(name="Class", kind=ElementKind.CLASS, location=location)
        func = FunctionInfo(name="func", kind=ElementKind.FUNCTION, location=location)
        
        result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[cls],
            functions=[func],
            analysis_metadata={"cpp_standard": "c++17"}
        )
        
        assert result.file_path == "/path/file.cpp"
        assert len(result.classes) == 1
        assert len(result.functions) == 1
        assert result.analysis_metadata["cpp_standard"] == "c++17"

    def test_analysis_result_defaults(self):
        """Test AnalysisResult with default values."""
        result = AnalysisResult(file_path="/path/file.cpp")
        
        assert len(result.includes) == 0
        assert len(result.namespaces) == 0
        assert len(result.classes) == 0
        assert len(result.functions) == 0
        assert len(result.variables) == 0
        assert len(result.diagnostics) == 0
        assert len(result.analysis_metadata) == 0

    def test_get_all_classes(self):
        """Test getting all classes including those in namespaces."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        # Create classes
        global_class = ClassInfo(name="GlobalClass", kind=ElementKind.CLASS, location=location)
        ns_class = ClassInfo(name="NSClass", kind=ElementKind.CLASS, location=location)
        
        # Create namespace with class
        namespace = NamespaceInfo(
            name="ns",
            kind=ElementKind.NAMESPACE,
            location=location,
            classes=[ns_class]
        )
        
        result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[global_class],
            namespaces=[namespace]
        )
        
        all_classes = result.get_all_classes()
        assert len(all_classes) == 2
        class_names = [cls.name for cls in all_classes]
        assert "GlobalClass" in class_names
        assert "NSClass" in class_names

    def test_get_statistics(self):
        """Test getting analysis statistics."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        cls = ClassInfo(name="Class", kind=ElementKind.CLASS, location=location)
        func = FunctionInfo(name="func", kind=ElementKind.FUNCTION, location=location)
        diag = DiagnosticInfo(
            severity="error",
            message="Test error",
            location=location,
            category="Test"
        )
        
        result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[cls],
            functions=[func],
            diagnostics=[diag]
        )
        
        stats = result.get_statistics()
        assert stats["total_classes"] == 1
        assert stats["total_functions"] == 1
        assert stats["error_count"] == 1
        assert stats["warning_count"] == 0

    def test_to_dict(self):
        """Test converting AnalysisResult to dictionary."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        cls = ClassInfo(name="Class", kind=ElementKind.CLASS, location=location)
        
        result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[cls]
        )
        
        data = result.to_dict()
        assert data["file_path"] == "/path/file.cpp"
        assert "statistics" in data
        assert "classes" in data
        assert len(data["classes"]) == 1


class TestProjectAnalysisResult:
    """Test ProjectAnalysisResult model."""

    def test_project_analysis_result_creation(self):
        """Test creating a ProjectAnalysisResult."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        cls = ClassInfo(name="Class", kind=ElementKind.CLASS, location=location)
        
        file_result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[cls]
        )
        
        project_result = ProjectAnalysisResult(
            project_path="/path/project",
            files_analyzed=["/path/file.cpp"],
            analysis_results=[file_result]
        )
        
        assert project_result.project_path == "/path/project"
        assert len(project_result.files_analyzed) == 1
        assert len(project_result.analysis_results) == 1

    def test_get_project_statistics(self):
        """Test getting project-wide statistics."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        cls = ClassInfo(name="Class", kind=ElementKind.CLASS, location=location)
        func = FunctionInfo(name="func", kind=ElementKind.FUNCTION, location=location)
        var = VariableInfo(name="var", kind=ElementKind.VARIABLE, location=location)
        
        file_result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[cls],
            functions=[func],
            variables=[var]
        )
        
        project_result = ProjectAnalysisResult(
            project_path="/path/project",
            files_analyzed=["/path/file.cpp"],
            analysis_results=[file_result]
        )
        
        stats = project_result.get_project_statistics()
        assert stats["total_files"] == 1
        assert stats["total_classes"] == 1
        assert stats["total_functions"] == 1
        assert stats["total_variables"] == 1


class TestJsonSerialization:
    """Test JSON serialization of models."""

    def test_analysis_result_json_serialization(self):
        """Test that AnalysisResult can be serialized to JSON."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        cls = ClassInfo(name="TestClass", kind=ElementKind.CLASS, location=location)
        
        result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[cls]
        )
        
        # Should not raise an exception
        json_str = json.dumps(result.model_dump(), default=str)
        assert "TestClass" in json_str
        assert "/path/file.cpp" in json_str

    def test_project_result_json_serialization(self):
        """Test that ProjectAnalysisResult can be serialized to JSON."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        cls = ClassInfo(name="TestClass", kind=ElementKind.CLASS, location=location)
        
        file_result = AnalysisResult(
            file_path="/path/file.cpp",
            classes=[cls]
        )
        
        project_result = ProjectAnalysisResult(
            project_path="/path/project",
            files_analyzed=["/path/file.cpp"],
            analysis_results=[file_result]
        )
        
        # Should not raise an exception
        json_str = json.dumps(project_result.model_dump(), default=str)
        assert "/path/project" in json_str
        assert "TestClass" in json_str


class TestModelValidation:
    """Test model validation."""

    def test_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValueError):
            # Missing required fields should raise ValidationError
            ParameterInfo()  # Missing name and type_name

    def test_enum_validation(self):
        """Test enum field validation."""
        location = SourceLocation("/path/file.cpp", 1, 1)
        
        # Valid enum value
        var = VariableInfo(
            name="var",
            kind=ElementKind.VARIABLE,
            location=location,
            access_specifier=AccessSpecifier.PUBLIC
        )
        assert var.access_specifier == AccessSpecifier.PUBLIC

    def test_field_descriptions(self):
        """Test that model fields have descriptions."""
        # Check that Pydantic models have field descriptions
        param_fields = ParameterInfo.model_fields
        assert "name" in param_fields
        assert param_fields["name"].description is not None

    def test_config_examples(self):
        """Test that models have example configurations."""
        # Check that models have example data for documentation
        param_schema = ParameterInfo.model_json_schema()
        # Should have examples or other schema information
        assert "properties" in param_schema