"""
Utility functions for C++ code analysis.

This module provides utility functions for path handling, AST traversal,
type information extraction, and other common operations.
"""

import os
import sys
import platform
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Any, Union, Callable
import re
import json

try:
    from clang.cindex import (
        Cursor, CursorKind, Type, TypeKind, 
        Diagnostic
    )
except ImportError:
    raise ImportError(
        "libclang not found. Please install with: pip install libclang"
    )


# Set up logging
logger = logging.getLogger(__name__)


class PathUtils:
    """Utilities for path handling and file operations."""

    @staticmethod
    def normalize_path(path: Union[str, Path]) -> str:
        """
        Normalize a file path for cross-platform compatibility.
        
        Args:
            path: File path to normalize
            
        Returns:
            Normalized absolute path string
        """
        return os.path.abspath(os.path.normpath(str(path)))

    @staticmethod
    def get_relative_path(target_path: str, base_path: str) -> str:
        """
        Get relative path from base to target.
        
        Args:
            target_path: Target file path
            base_path: Base directory path
            
        Returns:
            Relative path string
        """
        try:
            return os.path.relpath(target_path, base_path)
        except ValueError:
            # Different drives on Windows
            return target_path

    @staticmethod
    def is_header_file(file_path: str) -> bool:
        """
        Check if a file is a C++ header file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if it's a header file
        """
        header_extensions = {'.h', '.hpp', '.hxx', '.h++', '.hh'}
        return Path(file_path).suffix.lower() in header_extensions

    @staticmethod
    def is_source_file(file_path: str) -> bool:
        """
        Check if a file is a C++ source file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if it's a source file
        """
        source_extensions = {'.cpp', '.cxx', '.cc', '.c++'}
        return Path(file_path).suffix.lower() in source_extensions

    @staticmethod
    def find_project_root(start_path: str, markers: Optional[List[str]] = None) -> Optional[str]:
        """
        Find project root directory by looking for marker files.
        
        Args:
            start_path: Directory to start searching from
            markers: List of marker files/directories to look for
            
        Returns:
            Project root path or None if not found
        """
        if markers is None:
            markers = [
                'CMakeLists.txt', 'Makefile', '.git', '.svn', 
                'configure.ac', 'configure.in', 'vcpkg.json',
                'conanfile.txt', 'conanfile.py', '.gitignore'
            ]

        current_path = Path(start_path).resolve()
        
        while current_path != current_path.parent:
            for marker in markers:
                if (current_path / marker).exists():
                    return str(current_path)
            current_path = current_path.parent
        
        return None

    @staticmethod
    def create_safe_filename(name: str) -> str:
        """
        Create a safe filename from a string.
        
        Args:
            name: Original name
            
        Returns:
            Safe filename string
        """
        # Replace unsafe characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing dots and spaces
        safe_name = safe_name.strip('. ')
        # Limit length
        if len(safe_name) > 200:
            safe_name = safe_name[:200]
        
        return safe_name or 'unnamed'


class ASTUtils:
    """Utilities for AST traversal and analysis."""

    @staticmethod
    def traverse_depth_first(
        cursor: Cursor, 
        visitor: Callable[[Cursor, int], bool],
        max_depth: int = 100
    ) -> None:
        """
        Traverse AST depth-first with a visitor function.
        
        Args:
            cursor: Starting cursor
            visitor: Function that takes (cursor, depth) and returns continue flag
            max_depth: Maximum traversal depth
        """
        def _traverse(cur: Cursor, depth: int) -> None:
            if depth > max_depth:
                logger.warning(f"Max depth {max_depth} reached in AST traversal")
                return
            
            try:
                # Visit current node
                should_continue = visitor(cur, depth)
                
                if should_continue:
                    # Visit children
                    for child in cur.get_children():
                        _traverse(child, depth + 1)
            except Exception as e:
                logger.warning(f"Error in AST traversal at depth {depth}: {e}")
        
        _traverse(cursor, 0)

    @staticmethod
    def find_cursors_by_kind(
        root_cursor: Cursor, 
        target_kinds: Union[CursorKind, List[CursorKind]],
        max_depth: int = 50
    ) -> List[Cursor]:
        """
        Find all cursors of specified kinds in the AST.
        
        Args:
            root_cursor: Root cursor to search from
            target_kinds: Cursor kind(s) to find
            max_depth: Maximum search depth
            
        Returns:
            List of matching cursors
        """
        if isinstance(target_kinds, CursorKind):
            target_kinds = [target_kinds]
        
        found_cursors = []
        
        def visitor(cursor: Cursor, depth: int) -> bool:
            if cursor.kind in target_kinds:
                found_cursors.append(cursor)
            return True
        
        ASTUtils.traverse_depth_first(root_cursor, visitor, max_depth)
        return found_cursors

    @staticmethod
    def get_cursor_path(cursor: Cursor) -> List[str]:
        """
        Get the hierarchical path to a cursor (namespace::class::method).
        
        Args:
            cursor: Target cursor
            
        Returns:
            List of names from root to cursor
        """
        path = []
        current = cursor
        
        while current and current.kind != CursorKind.TRANSLATION_UNIT:
            if current.spelling:
                path.insert(0, current.spelling)
            current = current.semantic_parent
        
        return path

    @staticmethod
    def is_cursor_in_file(cursor: Cursor, file_path: str) -> bool:
        """
        Check if cursor is defined in the specified file.
        
        Args:
            cursor: Cursor to check
            file_path: File path to compare against
            
        Returns:
            True if cursor is in the file
        """
        if not cursor.location.file:
            return False
        
        cursor_file = str(cursor.location.file)
        normalized_file = PathUtils.normalize_path(file_path)
        normalized_cursor_file = PathUtils.normalize_path(cursor_file)
        
        return normalized_cursor_file == normalized_file

    @staticmethod
    def get_cursor_text(cursor: Cursor) -> str:
        """
        Get the source text for a cursor.
        
        Args:
            cursor: Cursor to get text for
            
        Returns:
            Source text string
        """
        try:
            if cursor.extent and cursor.extent.start.file == cursor.extent.end.file:
                with open(str(cursor.extent.start.file), 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    start_line = cursor.extent.start.line - 1
                    end_line = cursor.extent.end.line - 1
                    start_col = cursor.extent.start.column - 1
                    end_col = cursor.extent.end.column - 1
                    
                    if start_line == end_line:
                        return lines[start_line][start_col:end_col]
                    else:
                        result = lines[start_line][start_col:]
                        for line_idx in range(start_line + 1, end_line):
                            result += lines[line_idx]
                        result += lines[end_line][:end_col]
                        return result
        except Exception as e:
            logger.warning(f"Error getting cursor text: {e}")
        
        return ""


class TypeUtils:
    """Utilities for type analysis and manipulation."""

    @staticmethod
    def get_canonical_type_name(type_obj: Type) -> str:
        """
        Get canonical type name, resolving typedefs and aliases.
        
        Args:
            type_obj: Clang Type object
            
        Returns:
            Canonical type name
        """
        try:
            canonical = type_obj.get_canonical()
            return canonical.spelling if canonical else type_obj.spelling
        except Exception:
            return type_obj.spelling if type_obj else ""

    @staticmethod
    def is_pointer_type(type_obj: Type) -> bool:
        """Check if type is a pointer."""
        return type_obj.kind == TypeKind.POINTER if type_obj else False

    @staticmethod
    def is_reference_type(type_obj: Type) -> bool:
        """Check if type is a reference."""
        return type_obj.kind in [TypeKind.LVALUEREFERENCE, TypeKind.RVALUEREFERENCE] if type_obj else False

    @staticmethod
    def is_const_type(type_obj: Type) -> bool:
        """Check if type is const-qualified."""
        return type_obj.is_const_qualified() if type_obj else False

    @staticmethod
    def get_pointee_type(type_obj: Type) -> Optional[Type]:
        """Get the type pointed to by a pointer type."""
        try:
            if TypeUtils.is_pointer_type(type_obj):
                return type_obj.get_pointee()
        except Exception:
            pass
        return None

    @staticmethod
    def parse_template_arguments(type_name: str) -> List[str]:
        """
        Parse template arguments from a type name.
        
        Args:
            type_name: Type name like "std::vector<int>"
            
        Returns:
            List of template argument strings
        """
        # Simple regex-based parsing (not perfect for complex nested templates)
        match = re.search(r'<(.+)>', type_name)
        if not match:
            return []
        
        args_str = match.group(1)
        args = []
        bracket_depth = 0
        current_arg = ""
        
        for char in args_str:
            if char == '<':
                bracket_depth += 1
                current_arg += char
            elif char == '>':
                bracket_depth -= 1
                current_arg += char
            elif char == ',' and bracket_depth == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args


class DiagnosticUtils:
    """Utilities for processing diagnostics."""

    @staticmethod
    def format_diagnostic(diagnostic: Diagnostic) -> str:
        """
        Format a diagnostic message.
        
        Args:
            diagnostic: Clang diagnostic
            
        Returns:
            Formatted diagnostic string
        """
        severity_names = {
            Diagnostic.Ignored: "ignored",
            Diagnostic.Note: "note",
            Diagnostic.Warning: "warning", 
            Diagnostic.Error: "error",
            Diagnostic.Fatal: "fatal"
        }
        
        severity = severity_names.get(diagnostic.severity, "unknown")
        location = ""
        
        if diagnostic.location.file:
            location = f"{diagnostic.location.file}:{diagnostic.location.line}:{diagnostic.location.column}: "
        
        return f"{location}{severity}: {diagnostic.spelling}"

    @staticmethod
    def filter_diagnostics(
        diagnostics: List[Diagnostic],
        min_severity: int = Diagnostic.Warning,
        exclude_categories: Optional[Set[str]] = None
    ) -> List[Diagnostic]:
        """
        Filter diagnostics by severity and category.
        
        Args:
            diagnostics: List of diagnostics to filter
            min_severity: Minimum severity level
            exclude_categories: Categories to exclude
            
        Returns:
            Filtered list of diagnostics
        """
        if exclude_categories is None:
            exclude_categories = set()
        
        filtered = []
        for diag in diagnostics:
            if (diag.severity >= min_severity and
                diag.category_name not in exclude_categories):
                filtered.append(diag)
        
        return filtered


class OutputUtils:
    """Utilities for output formatting and serialization."""

    @staticmethod
    def format_json(data: Any, indent: int = 2, ensure_ascii: bool = False) -> str:
        """
        Format data as JSON string.
        
        Args:
            data: Data to serialize
            indent: JSON indentation
            ensure_ascii: Whether to ensure ASCII output
            
        Returns:
            JSON string
        """
        try:
            return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, default=str)
        except Exception as e:
            logger.error(f"Error formatting JSON: {e}")
            return "{}"

    @staticmethod
    def create_summary_table(analysis_results: List[Dict[str, Any]]) -> str:
        """
        Create a summary table of analysis results.
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            Formatted table string
        """
        if not analysis_results:
            return "No analysis results to display."
        
        # Calculate totals
        total_files = len(analysis_results)
        total_classes = sum(len(result.get('classes', [])) for result in analysis_results)
        total_functions = sum(len(result.get('functions', [])) for result in analysis_results)
        total_variables = sum(len(result.get('variables', [])) for result in analysis_results)
        total_errors = sum(len([d for d in result.get('diagnostics', []) 
                              if d.get('severity') == 'error']) for result in analysis_results)
        total_warnings = sum(len([d for d in result.get('diagnostics', []) 
                                if d.get('severity') == 'warning']) for result in analysis_results)
        
        table = f"""
Analysis Summary
================
Files analyzed:     {total_files:6d}
Classes found:      {total_classes:6d}
Functions found:    {total_functions:6d}
Variables found:    {total_variables:6d}
Errors:             {total_errors:6d}
Warnings:           {total_warnings:6d}
"""
        return table.strip()

    @staticmethod
    def format_file_list(files: List[str], base_path: Optional[str] = None) -> str:
        """
        Format a list of files for display.
        
        Args:
            files: List of file paths
            base_path: Base path for relative display
            
        Returns:
            Formatted file list string
        """
        if not files:
            return "No files found."
        
        formatted_files = []
        for file_path in sorted(files):
            display_path = file_path
            if base_path:
                display_path = PathUtils.get_relative_path(file_path, base_path)
            formatted_files.append(f"  {display_path}")
        
        return "\n".join(formatted_files)


class SystemUtils:
    """Utilities for system-specific operations."""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Get system information relevant to C++ analysis.
        
        Returns:
            Dictionary with system information
        """
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_executable": sys.executable
        }

    @staticmethod
    def find_libclang_library() -> Optional[str]:
        """
        Try to find libclang library on the system.
        
        Returns:
            Path to libclang library or None if not found
        """
        possible_paths = []
        
        if platform.system() == "Windows":
            possible_paths.extend([
                "C:\\Program Files\\LLVM\\bin\\libclang.dll",
                "C:\\Program Files (x86)\\LLVM\\bin\\libclang.dll",
                "libclang.dll"
            ])
        elif platform.system() == "Darwin":  # macOS
            possible_paths.extend([
                "/usr/local/lib/libclang.dylib",
                "/opt/homebrew/lib/libclang.dylib",
                "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/libclang.dylib",
                "libclang.dylib"
            ])
        else:  # Linux and others
            possible_paths.extend([
                "/usr/lib/libclang.so",
                "/usr/lib/x86_64-linux-gnu/libclang.so",
                "/usr/lib/llvm/libclang.so",
                "libclang.so"
            ])
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None

    @staticmethod
    def get_compiler_info() -> Dict[str, Any]:
        """
        Get information about available C++ compilers.
        
        Returns:
            Dictionary with compiler information
        """
        compilers = {}
        
        # Check for common compilers
        compiler_commands = {
            "gcc": "gcc --version",
            "clang": "clang --version", 
            "msvc": "cl.exe",  # Windows only
            "icc": "icc --version"
        }
        
        for name, command in compiler_commands.items():
            try:
                import subprocess
                result = subprocess.run(
                    command.split(), 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    compilers[name] = {
                        "available": True,
                        "version_info": result.stdout.split('\n')[0]
                    }
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                compilers[name] = {"available": False}
        
        return compilers


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Reduce clang logging noise
    logging.getLogger("clang").setLevel(logging.WARNING)