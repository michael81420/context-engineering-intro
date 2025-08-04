"""
C++ Code Analyzer using libclang.

This package provides comprehensive C++ source code analysis capabilities
using the libclang library for AST parsing and structural information extraction.
"""

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"
__license__ = "MIT"

from .analyzer import CppAnalyzer
from .indexer import CppIndexer, FileInfo
from .models import (
    AnalysisResult,
    ProjectAnalysisResult,
    ClassInfo,
    FunctionInfo,
    VariableInfo,
    NamespaceInfo,
    EnumInfo,
    IncludeInfo,
    DiagnosticInfo,
    ParameterInfo,
    SourceLocation,
    AccessSpecifier,
    ElementKind
)
from .parsers import CppParser, NamespaceParser
from .utils import (
    PathUtils,
    ASTUtils,
    TypeUtils,
    DiagnosticUtils,
    OutputUtils,
    SystemUtils,
    setup_logging
)

__all__ = [
    # Core classes
    "CppAnalyzer",
    "CppIndexer",
    "CppParser",
    "NamespaceParser",
    
    # Data models
    "AnalysisResult",
    "ProjectAnalysisResult",
    "ClassInfo",
    "FunctionInfo",
    "VariableInfo",
    "NamespaceInfo", 
    "EnumInfo",
    "IncludeInfo",
    "DiagnosticInfo",
    "ParameterInfo",
    "SourceLocation",
    "FileInfo",
    
    # Enums
    "AccessSpecifier",
    "ElementKind",
    
    # Utilities
    "PathUtils",
    "ASTUtils", 
    "TypeUtils",
    "DiagnosticUtils",
    "OutputUtils",
    "SystemUtils",
    "setup_logging",
    
    # Package metadata
    "__version__",
    "__author__",
    "__license__"
]

# Package-level convenience functions
def analyze_file(
    file_path: str,
    cpp_standard: str = "c++17",
    include_paths: list = None,
    library_path: str = None
) -> AnalysisResult:
    """
    Convenience function to analyze a single C++ file.
    
    Args:
        file_path: Path to the C++ file to analyze
        cpp_standard: C++ standard to use (default: c++17)
        include_paths: List of include directories
        library_path: Path to libclang library
        
    Returns:
        AnalysisResult containing analysis data
    """
    analyzer = CppAnalyzer(cpp_standard=cpp_standard, library_path=library_path)
    return analyzer.analyze_file(file_path, include_paths or [])


def discover_cpp_files(
    root_path: str,
    recursive: bool = True,
    include_headers: bool = True,
    include_sources: bool = True
) -> list:
    """
    Convenience function to discover C++ files in a directory.
    
    Args:
        root_path: Root directory to search
        recursive: Whether to search subdirectories
        include_headers: Whether to include header files
        include_sources: Whether to include source files
        
    Returns:
        List of FileInfo objects for discovered files
    """
    indexer = CppIndexer()
    return indexer.discover_cpp_files(
        root_path=root_path,
        recursive=recursive,
        include_headers=include_headers,
        include_sources=include_sources
    )


def get_version() -> str:
    """Get package version."""
    return __version__


def get_system_info() -> dict:
    """Get system information for debugging."""
    return SystemUtils.get_system_info()