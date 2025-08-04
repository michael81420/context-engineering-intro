"""
Tests for CppAnalyzer class.

This module contains comprehensive tests for the main C++ analyzer functionality,
including AST traversal, file parsing, and analysis result generation.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

try:
    from clang.cindex import Index, CursorKind, Diagnostic
except ImportError:
    pytest.skip("libclang not available", allow_module_level=True)

from cpp_analyzer.analyzer import CppAnalyzer
from cpp_analyzer.models import (
    AnalysisResult, ClassInfo, FunctionInfo, VariableInfo,
    NamespaceInfo, EnumInfo, ElementKind
)


@pytest.fixture
def analyzer():
    """Create CppAnalyzer instance for testing."""
    return CppAnalyzer(cpp_standard="c++17")


@pytest.fixture
def sample_cpp_content():
    """Sample C++ code for testing."""
    return '''
#include <iostream>
#include "custom.h"

namespace TestNamespace {
    class TestClass {
    public:
        TestClass();
        ~TestClass();
        void publicMethod();
        int getValue() const;
        
    private:
        int value_;
        static const int MAX_VALUE = 100;
    };
    
    enum class Color {
        RED,
        GREEN,
        BLUE
    };
    
    void freeFunction(int param);
}

int globalVariable = 42;

void globalFunction() {
    std::cout << "Hello World" << std::endl;
}
'''


@pytest.fixture
def temp_cpp_file(sample_cpp_content):
    """Create temporary C++ file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(sample_cpp_content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except OSError:
        pass


class TestCppAnalyzer:
    """Test cases for CppAnalyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization with different parameters."""
        # Default initialization
        analyzer = CppAnalyzer()
        assert analyzer.cpp_standard == "c++17"
        assert analyzer.index is not None
        
        # Custom C++ standard
        analyzer_cpp20 = CppAnalyzer(cpp_standard="c++20")
        assert analyzer_cpp20.cpp_standard == "c++20"
        assert '-std=c++20' in analyzer_cpp20.compiler_args
    
    def test_analyze_nonexistent_file(self, analyzer):
        """Test analysis of non-existent file."""
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file("/path/to/nonexistent/file.cpp")
    
    def test_analyze_file_basic(self, analyzer, temp_cpp_file):
        """Test basic file analysis functionality."""
        result = analyzer.analyze_file(temp_cpp_file)
        
        assert isinstance(result, AnalysisResult)
        assert result.file_path == os.path.abspath(temp_cpp_file)
        assert result.analysis_metadata is not None
        assert result.analysis_metadata["cpp_standard"] == "c++17"
    
    def test_analyze_file_with_includes(self, analyzer, temp_cpp_file):
        """Test file analysis with include paths."""
        include_paths = ["/usr/include", "/usr/local/include"]
        result = analyzer.analyze_file(
            temp_cpp_file, 
            include_paths=include_paths
        )
        
        assert isinstance(result, AnalysisResult)
        # Check that include arguments were added
        expected_args = [f'-I{path}' for path in include_paths]
        for arg in expected_args:
            assert arg in result.analysis_metadata["compiler_args"]
    
    def test_analyze_file_with_macros(self, analyzer, temp_cpp_file):
        """Test file analysis with macro definitions."""
        macros = ["DEBUG=1", "VERSION=2"]
        result = analyzer.analyze_file(
            temp_cpp_file,
            define_macros=macros
        )
        
        assert isinstance(result, AnalysisResult)
        # Check that macro arguments were added
        expected_args = [f'-D{macro}' for macro in macros]
        for arg in expected_args:
            assert arg in result.analysis_metadata["compiler_args"]
    
    def test_extract_namespace_info(self, analyzer, temp_cpp_file):
        """Test namespace extraction."""
        result = analyzer.analyze_file(temp_cpp_file)
        
        # Should find TestNamespace
        namespaces = result.namespaces
        assert len(namespaces) > 0
        
        test_namespace = next(
            (ns for ns in namespaces if ns.name == "TestNamespace"), 
            None
        )
        assert test_namespace is not None
        assert test_namespace.kind == ElementKind.NAMESPACE
    
    def test_extract_class_info(self, analyzer, temp_cpp_file):
        """Test class extraction."""
        result = analyzer.analyze_file(temp_cpp_file)
        
        # Should find TestClass in TestNamespace
        all_classes = result.get_all_classes()
        test_class = next(
            (cls for cls in all_classes if cls.name == "TestClass"),
            None
        )
        
        assert test_class is not None
        assert test_class.kind == ElementKind.CLASS
        assert test_class.namespace == "TestNamespace"
        assert not test_class.is_abstract  # No pure virtual methods
    
    def test_extract_function_info(self, analyzer, temp_cpp_file):
        """Test function extraction."""
        result = analyzer.analyze_file(temp_cpp_file)
        
        # Should find global function
        global_funcs = [f for f in result.functions if f.name == "globalFunction"]
        assert len(global_funcs) > 0
        
        global_func = global_funcs[0]
        assert global_func.kind == ElementKind.FUNCTION
        assert global_func.return_type == "void"
        assert not global_func.is_virtual
    
    def test_extract_variable_info(self, analyzer, temp_cpp_file):
        """Test variable extraction."""
        result = analyzer.analyze_file(temp_cpp_file)
        
        # Should find global variable
        global_vars = [v for v in result.variables if v.name == "globalVariable"]
        assert len(global_vars) > 0
        
        global_var = global_vars[0]
        assert global_var.kind == ElementKind.VARIABLE
        assert global_var.type_name == "int"
    
    def test_extract_enum_info(self, analyzer, temp_cpp_file):
        """Test enum extraction."""
        result = analyzer.analyze_file(temp_cpp_file)
        
        # Should find Color enum in TestNamespace
        all_enums = result.get_all_enums()
        color_enum = next(
            (e for e in all_enums if e.name == "Color"),
            None
        )
        
        assert color_enum is not None
        assert color_enum.kind == ElementKind.ENUM
        assert color_enum.is_scoped  # enum class
        assert len(color_enum.values) == 3
    
    def test_extract_include_info(self, analyzer, temp_cpp_file):
        """Test include extraction."""
        result = analyzer.analyze_file(temp_cpp_file)
        
        # Should find includes
        includes = result.includes
        assert len(includes) >= 2
        
        # Should find both system and local includes
        system_includes = [inc for inc in includes if inc.is_system_include]
        local_includes = [inc for inc in includes if not inc.is_system_include]
        
        assert len(system_includes) > 0  # <iostream>
        assert len(local_includes) > 0   # "custom.h"
    
    def test_statistics_generation(self, analyzer, temp_cpp_file):
        """Test analysis statistics generation."""
        result = analyzer.analyze_file(temp_cpp_file)
        stats = result.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_classes" in stats
        assert "total_functions" in stats
        assert "total_variables" in stats
        assert "total_namespaces" in stats
        assert "total_enums" in stats
        
        # Should have found at least one of each
        assert stats["total_classes"] >= 1
        assert stats["total_functions"] >= 1
        assert stats["total_variables"] >= 1
        assert stats["total_namespaces"] >= 1
        assert stats["total_enums"] >= 1
    
    @patch('cpp_analyzer.analyzer.Index.create')
    def test_libclang_initialization_failure(self, mock_index_create):
        """Test handling of libclang initialization failure."""
        mock_index_create.side_effect = Exception("libclang failed")
        
        with pytest.raises(RuntimeError, match="Failed to initialize libclang Index"):
            CppAnalyzer()
    
    def test_error_result_creation(self, analyzer):
        """Test creation of error results."""
        errors = ["Parse error", "Missing include"]
        result = analyzer._create_error_result("/fake/path.cpp", errors)
        
        assert isinstance(result, AnalysisResult)
        assert result.file_path == "/fake/path.cpp"
        assert len(result.diagnostics) == 2
        assert all(d.severity == "error" for d in result.diagnostics)
        assert result.analysis_metadata["analysis_failed"] is True
    
    def test_header_file_analysis(self, analyzer):
        """Test analysis of header files."""
        header_content = '''
#pragma once

class HeaderClass {
public:
    void method();
private:  
    int field;
};
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hpp', delete=False) as f:
            f.write(header_content)
            temp_header = f.name
        
        try:
            result = analyzer.analyze_file(temp_header)
            assert isinstance(result, AnalysisResult)
            
            # Should detect header file type
            args = result.analysis_metadata["compiler_args"]
            assert '-x' in args
            header_idx = args.index('-x')
            assert args[header_idx + 1] == 'c++-header'
            
        finally:
            try:
                os.unlink(temp_header)
            except OSError:
                pass
    
    def test_source_location_creation(self, analyzer):
        """Test source location creation from cursor."""
        # Create a mock cursor with location info
        mock_cursor = Mock()
        mock_location = Mock()
        mock_location.file = "/test/file.cpp"
        mock_location.line = 42
        mock_location.column = 10
        mock_location.offset = 1000
        mock_cursor.location = mock_location
        
        location = analyzer._create_source_location(mock_cursor)
        
        assert location.file_path == "/test/file.cpp"
        assert location.line == 42
        assert location.column == 10
        assert location.offset == 1000
    
    def test_access_specifier_mapping(self, analyzer):
        """Test access specifier mapping from libclang."""
        try:
            from clang.cindex import AccessSpecifier as ClangAccessSpecifier
            from cpp_analyzer.models import AccessSpecifier
            
            # Test all mappings
            assert analyzer._map_access_specifier(ClangAccessSpecifier.PUBLIC) == AccessSpecifier.PUBLIC
            assert analyzer._map_access_specifier(ClangAccessSpecifier.PRIVATE) == AccessSpecifier.PRIVATE
            assert analyzer._map_access_specifier(ClangAccessSpecifier.PROTECTED) == AccessSpecifier.PROTECTED
            
            # Test unknown mapping
            assert analyzer._map_access_specifier(999) == AccessSpecifier.UNKNOWN
        
        except ImportError:
            pytest.skip("libclang AccessSpecifier not available")


class TestASTTraversal:
    """Test cases for AST traversal functionality."""
    
    def test_ast_traversal_depth_limiting(self, analyzer):
        """Test that AST traversal handles deep nesting."""
        # Create deeply nested content
        nested_content = '''
namespace A {
    namespace B {
        namespace C {
            namespace D {
                namespace E {
                    class DeepClass {
                        void method() {
                            if (true) {
                                for (int i = 0; i < 10; ++i) {
                                    // Deep nesting
                                }
                            }
                        }
                    };
                }
            }
        }
    }
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(nested_content)
            temp_file = f.name
        
        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            
            # Should handle deep nesting without crashing
            all_classes = result.get_all_classes()
            deep_class = next(
                (cls for cls in all_classes if cls.name == "DeepClass"),
                None
            )
            assert deep_class is not None
            
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
    
    def test_empty_file_analysis(self, analyzer):
        """Test analysis of empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write("")  # Empty file
            temp_file = f.name
        
        try:
            result = analyzer.analyze_file(temp_file)
            assert isinstance(result, AnalysisResult)
            
            # Should have empty collections
            assert len(result.classes) == 0
            assert len(result.functions) == 0
            assert len(result.variables) == 0
            assert len(result.namespaces) == 0
            
        finally:
            try:
                os.unlink(temp_file)
            except OSError:
                pass


@pytest.mark.skipif(
    not os.path.exists("examples/sample_cpp/sample.cpp"),
    reason="Sample C++ files not available"
)
class TestRealFileAnalysis:
    """Test analysis with real sample files."""
    
    def test_sample_file_analysis(self, analyzer):
        """Test analysis of the sample C++ file."""
        sample_path = "examples/sample_cpp/sample.cpp"
        result = analyzer.analyze_file(sample_path)
        
        assert isinstance(result, AnalysisResult)
        assert result.file_path.endswith("sample.cpp")
        
        # Should find expected elements
        stats = result.get_statistics()
        assert stats["total_classes"] > 0
        assert stats["total_functions"] > 0
    
    def test_complex_example_analysis(self, analyzer):
        """Test analysis of the complex example file."""
        example_path = "examples/sample_cpp/complex_example.h"
        result = analyzer.analyze_file(example_path)
        
        assert isinstance(result, AnalysisResult)
        assert result.file_path.endswith("complex_example.h")
        
        # Should handle complex C++ features
        stats = result.get_statistics()
        assert stats["total_classes"] > 0