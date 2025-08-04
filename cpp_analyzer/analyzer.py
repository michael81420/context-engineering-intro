"""
Main C++ code analyzer using libclang.

This module provides the core CppAnalyzer class that uses libclang to parse
C++ source files and extract structural information.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Any
from datetime import datetime

try:
    from clang.cindex import (
        Index, Cursor, CursorKind, 
        AccessSpecifier as ClangAccessSpecifier,
        Diagnostic, Config
    )
except ImportError:
    raise ImportError(
        "libclang not found. Please install with: pip install libclang"
    )

from .models import (
    AnalysisResult, ClassInfo, FunctionInfo, VariableInfo, 
    NamespaceInfo, EnumInfo, IncludeInfo, DiagnosticInfo,
    ParameterInfo, SourceLocation, AccessSpecifier, ElementKind
)

# Set up logging
logger = logging.getLogger(__name__)


class CppAnalyzer:
    """
    Main C++ code analyzer using libclang.
    
    This class provides methods to analyze C++ source files and extract
    comprehensive structural information including classes, functions,
    variables, namespaces, and more.
    """

    def __init__(self, cpp_standard: str = "c++17", library_path: Optional[str] = None):
        """
        Initialize the C++ analyzer.
        
        Args:
            cpp_standard: C++ standard to use (c++11, c++14, c++17, c++20)
            library_path: Optional path to libclang shared library
        """
        self.cpp_standard = cpp_standard
        self.compiler_args = [f'-std={cpp_standard}']
        
        # Set library path if provided
        if library_path:
            Config.set_library_path(library_path)
        
        # Initialize libclang Index
        try:
            self.index = Index.create()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize libclang Index: {e}") from e
        
        logger.info(f"Initialized CppAnalyzer with C++ standard: {cpp_standard}")

    def analyze_file(
        self, 
        file_path: str, 
        include_paths: Optional[List[str]] = None,
        define_macros: Optional[List[str]] = None,
        additional_args: Optional[List[str]] = None
    ) -> AnalysisResult:
        """
        Analyze a single C++ source file.
        
        Args:
            file_path: Path to the C++ file to analyze
            include_paths: List of include directories
            define_macros: List of macro definitions (format: "NAME=VALUE")
            additional_args: Additional compiler arguments
            
        Returns:
            AnalysisResult containing extracted structural information
        """
        file_path = os.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Analyzing file: {file_path}")
        
        # Build compiler arguments
        args = self.compiler_args.copy()
        
        if include_paths:
            args.extend([f'-I{path}' for path in include_paths])
        
        if define_macros:
            args.extend([f'-D{macro}' for macro in define_macros])
        
        if additional_args:
            args.extend(additional_args)
        
        # Determine file type and add appropriate flags
        file_ext = Path(file_path).suffix.lower()
        if file_ext in ['.h', '.hpp', '.hxx']:
            args.extend(['-x', 'c++-header'])
        elif file_ext in ['.cpp', '.cxx', '.cc']:
            args.extend(['-x', 'c++'])
        
        try:
            # Parse the translation unit
            logger.debug(f"Parsing with args: {args}")
            tu = self.index.parse(file_path, args=args)
            
            if not tu:
                return self._create_error_result(
                    file_path, 
                    ["Failed to create translation unit"]
                )
            
            # Check for critical parsing errors
            critical_errors = [
                diag for diag in tu.diagnostics 
                if diag.severity >= Diagnostic.Error
            ]
            
            # Create analysis result
            result = AnalysisResult(
                file_path=file_path,
                analysis_metadata={
                    "cpp_standard": self.cpp_standard,
                    "analysis_time": datetime.now().isoformat(),
                    "compiler_args": args
                }
            )
            
            # Process diagnostics
            result.diagnostics = self._process_diagnostics(tu.diagnostics)
            
            # If there are critical errors, return early with diagnostics
            if critical_errors:
                logger.warning(f"Found {len(critical_errors)} critical errors in {file_path}")
                return result
            
            # Traverse AST and extract information
            self._traverse_ast(tu.cursor, result)
            
            # Add summary statistics to metadata
            result.analysis_metadata.update({
                "total_classes": len(result.get_all_classes()),
                "total_functions": len(result.get_all_functions()),
                "total_variables": len(result.variables),
                "total_namespaces": len(result.namespaces)
            })
            
            logger.info(f"Analysis complete: {result.get_statistics()}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return self._create_error_result(file_path, [str(e)])

    def _traverse_ast(
        self, 
        cursor: Cursor, 
        result: AnalysisResult, 
        depth: int = 0,
        namespace_stack: Optional[List[str]] = None,
        class_stack: Optional[List[str]] = None
    ) -> None:
        """
        Recursively traverse the AST and extract information.
        
        Args:
            cursor: Current cursor position in AST
            result: AnalysisResult to populate
            depth: Current traversal depth
            namespace_stack: Stack of namespace names
            class_stack: Stack of class names for nested classes
        """
        if namespace_stack is None:
            namespace_stack = []
        if class_stack is None:
            class_stack = []
        
        # Skip cursors from other files unless they're important declarations
        if (cursor.location.file and 
            str(cursor.location.file) != result.file_path and
            cursor.kind not in [CursorKind.INCLUSION_DIRECTIVE]):
            return
        
        try:
            # Handle different cursor kinds
            if cursor.kind == CursorKind.NAMESPACE:
                namespace_info = self._extract_namespace_info(cursor, namespace_stack)
                if namespace_info:
                    if not namespace_stack:  # Top-level namespace
                        result.namespaces.append(namespace_info)
                    
                    # Recursively process namespace contents
                    new_namespace_stack = namespace_stack + [namespace_info.name]
                    for child in cursor.get_children():
                        self._traverse_ast(child, result, depth + 1, new_namespace_stack, class_stack)
                    return  # Don't process children again
            
            elif cursor.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
                class_info = self._extract_class_info(cursor, namespace_stack, class_stack)
                if class_info:
                    if not class_stack:  # Top-level class
                        if namespace_stack:
                            # Add to appropriate namespace
                            self._add_to_namespace(result, namespace_stack, class_info, 'class')
                        else:
                            result.classes.append(class_info)
                    
                    # Recursively process class contents
                    new_class_stack = class_stack + [class_info.name]
                    for child in cursor.get_children():
                        self._traverse_ast(child, result, depth + 1, namespace_stack, new_class_stack)
                    return  # Don't process children again
            
            elif cursor.kind in [CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD]:
                func_info = self._extract_function_info(cursor, namespace_stack, class_stack)
                if func_info:
                    if class_stack:  # Method
                        # Add to appropriate class
                        self._add_to_class(result, namespace_stack, class_stack, func_info, 'method')
                    elif namespace_stack:  # Namespace function
                        self._add_to_namespace(result, namespace_stack, func_info, 'function')
                    else:  # Global function
                        result.functions.append(func_info)
            
            elif cursor.kind in [CursorKind.VAR_DECL, CursorKind.FIELD_DECL]:
                var_info = self._extract_variable_info(cursor, namespace_stack, class_stack)
                if var_info:
                    if class_stack:  # Field
                        self._add_to_class(result, namespace_stack, class_stack, var_info, 'field')
                    elif namespace_stack:  # Namespace variable
                        self._add_to_namespace(result, namespace_stack, var_info, 'variable')
                    else:  # Global variable
                        result.variables.append(var_info)
            
            elif cursor.kind == CursorKind.ENUM_DECL:
                enum_info = self._extract_enum_info(cursor, namespace_stack, class_stack)
                if enum_info:
                    if class_stack:  # Nested enum
                        self._add_to_class(result, namespace_stack, class_stack, enum_info, 'enum')
                    elif namespace_stack:  # Namespace enum
                        self._add_to_namespace(result, namespace_stack, enum_info, 'enum')
                    else:  # Global enum
                        result.enums.append(enum_info)
            
            elif cursor.kind == CursorKind.INCLUSION_DIRECTIVE:
                include_info = self._extract_include_info(cursor)
                if include_info:
                    result.includes.append(include_info)
            
            # Continue traversing children for other cursor types
            if cursor.kind not in [CursorKind.NAMESPACE, CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
                for child in cursor.get_children():
                    self._traverse_ast(child, result, depth + 1, namespace_stack, class_stack)
                    
        except Exception as e:
            logger.warning(f"Error processing cursor {cursor.kind} at {cursor.location}: {e}")

    def _extract_namespace_info(self, cursor: Cursor, namespace_stack: List[str]) -> Optional[NamespaceInfo]:
        """Extract namespace information from cursor."""
        try:
            name = cursor.spelling
            if not name:
                return None
            
            location = self._create_source_location(cursor)
            
            return NamespaceInfo(
                name=name,
                kind=ElementKind.NAMESPACE,
                location=location,
                display_name=cursor.displayname,
                parent_namespace="::".join(namespace_stack) if namespace_stack else None
            )
        except Exception as e:
            logger.warning(f"Error extracting namespace info: {e}")
            return None

    def _extract_class_info(
        self, 
        cursor: Cursor, 
        namespace_stack: List[str], 
        class_stack: List[str]
    ) -> Optional[ClassInfo]:
        """Extract class information from cursor."""
        try:
            name = cursor.spelling
            if not name:
                return None
            
            location = self._create_source_location(cursor)
            
            # Determine if it's abstract (has pure virtual methods)
            is_abstract = self._is_abstract_class(cursor)
            
            # Check if it's a template
            is_template = cursor.kind == CursorKind.CLASS_TEMPLATE
            
            # Extract base classes
            base_classes = self._extract_base_classes(cursor)
            
            return ClassInfo(
                name=name,
                kind=ElementKind.CLASS if cursor.kind == CursorKind.CLASS_DECL else ElementKind.STRUCT,
                location=location,
                display_name=cursor.displayname,
                base_classes=base_classes,
                is_abstract=is_abstract,
                is_template=is_template,
                namespace="::".join(namespace_stack) if namespace_stack else None,
                access_specifier=self._map_access_specifier(cursor.access_specifier)
            )
        except Exception as e:
            logger.warning(f"Error extracting class info: {e}")
            return None

    def _extract_function_info(
        self, 
        cursor: Cursor, 
        namespace_stack: List[str], 
        class_stack: List[str]
    ) -> Optional[FunctionInfo]:
        """Extract function information from cursor."""
        try:
            name = cursor.spelling
            if not name:
                return None
            
            location = self._create_source_location(cursor)
            
            # Extract return type
            return_type = cursor.result_type.spelling if cursor.result_type else ""
            
            # Extract parameters
            parameters = self._extract_parameters(cursor)
            
            # Check various function properties
            is_virtual = cursor.is_virtual_method()
            is_pure_virtual = cursor.is_pure_virtual_method()
            is_static = cursor.is_static_method()
            is_const = cursor.is_const_method()
            
            # Determine function type
            kind = ElementKind.METHOD if class_stack else ElementKind.FUNCTION
            
            if cursor.kind == CursorKind.CONSTRUCTOR:
                kind = ElementKind.CONSTRUCTOR
            elif cursor.kind == CursorKind.DESTRUCTOR:
                kind = ElementKind.DESTRUCTOR
            
            return FunctionInfo(
                name=name,
                kind=kind,
                location=location,
                display_name=cursor.displayname,
                return_type=return_type,
                parameters=parameters,
                is_virtual=is_virtual,
                is_pure_virtual=is_pure_virtual,
                is_static=is_static,
                is_const=is_const,
                is_constructor=cursor.kind == CursorKind.CONSTRUCTOR,
                is_destructor=cursor.kind == CursorKind.DESTRUCTOR,
                access_specifier=self._map_access_specifier(cursor.access_specifier),
                parent_class="::".join(class_stack) if class_stack else None
            )
        except Exception as e:
            logger.warning(f"Error extracting function info: {e}")
            return None

    def _extract_variable_info(
        self, 
        cursor: Cursor, 
        namespace_stack: List[str], 
        class_stack: List[str]
    ) -> Optional[VariableInfo]:
        """Extract variable information from cursor."""
        try:
            name = cursor.spelling
            if not name:
                return None
            
            location = self._create_source_location(cursor)
            
            # Extract type information
            type_name = cursor.type.spelling if cursor.type else ""
            
            # Check qualifiers
            is_const = cursor.type.is_const_qualified() if cursor.type else False
            is_static = cursor.storage_class == 2  # Static storage class
            
            kind = ElementKind.FIELD if class_stack else ElementKind.VARIABLE
            
            return VariableInfo(
                name=name,
                kind=kind,
                location=location,
                display_name=cursor.displayname,
                type_name=type_name,
                is_const=is_const,
                is_static=is_static,
                access_specifier=self._map_access_specifier(cursor.access_specifier)
            )
        except Exception as e:
            logger.warning(f"Error extracting variable info: {e}")
            return None

    def _extract_enum_info(
        self, 
        cursor: Cursor, 
        namespace_stack: List[str], 
        class_stack: List[str]
    ) -> Optional[EnumInfo]:
        """Extract enum information from cursor."""
        try:
            name = cursor.spelling
            if not name:
                return None
            
            location = self._create_source_location(cursor)
            
            # Check if it's a scoped enum (enum class)
            is_scoped = cursor.is_scoped_enum()
            
            # Extract enum values
            values = []
            for child in cursor.get_children():
                if child.kind == CursorKind.ENUM_CONSTANT_DECL:
                    values.append({
                        "name": child.spelling,
                        "value": str(child.enum_value) if hasattr(child, 'enum_value') else ""
                    })
            
            return EnumInfo(
                name=name,
                kind=ElementKind.ENUM,
                location=location,
                display_name=cursor.displayname,
                is_scoped=is_scoped,
                underlying_type=cursor.enum_type.spelling if cursor.enum_type else "",
                values=values,
                access_specifier=self._map_access_specifier(cursor.access_specifier)
            )
        except Exception as e:
            logger.warning(f"Error extracting enum info: {e}")
            return None

    def _extract_include_info(self, cursor: Cursor) -> Optional[IncludeInfo]:
        """Extract include information from cursor."""
        try:
            # Get the included file
            included_file = cursor.get_included_file()
            if not included_file:
                return None
            
            location = self._create_source_location(cursor)
            
            # Determine if it's a system include by checking the path
            file_path = str(included_file)
            is_system = '<' in cursor.displayname and '>' in cursor.displayname
            
            return IncludeInfo(
                file_path=os.path.basename(file_path),
                is_system_include=is_system,
                is_found=True,
                location=location
            )
        except Exception as e:
            logger.warning(f"Error extracting include info: {e}")
            return None

    def _extract_parameters(self, cursor: Cursor) -> List[ParameterInfo]:
        """Extract function parameters from cursor."""
        parameters = []
        try:
            for child in cursor.get_children():
                if child.kind == CursorKind.PARM_DECL:
                    param_name = child.spelling or f"param_{len(parameters)}"
                    param_type = child.type.spelling if child.type else ""
                    
                    # Check type qualifiers
                    is_const = child.type.is_const_qualified() if child.type else False
                    is_reference = child.type.kind.name == 'LVALUEREFERENCE' if child.type else False
                    is_pointer = child.type.kind.name == 'POINTER' if child.type else False
                    
                    parameters.append(ParameterInfo(
                        name=param_name,
                        type_name=param_type,
                        is_const=is_const,
                        is_reference=is_reference,
                        is_pointer=is_pointer
                    ))
        except Exception as e:
            logger.warning(f"Error extracting parameters: {e}")
        
        return parameters

    def _extract_base_classes(self, cursor: Cursor) -> List[str]:
        """Extract base class names from class cursor."""
        base_classes = []
        try:
            for child in cursor.get_children():
                if child.kind == CursorKind.CXX_BASE_SPECIFIER:
                    base_name = child.type.spelling if child.type else child.spelling
                    if base_name:
                        base_classes.append(base_name)
        except Exception as e:
            logger.warning(f"Error extracting base classes: {e}")
        
        return base_classes

    def _is_abstract_class(self, cursor: Cursor) -> bool:
        """Check if a class is abstract (has pure virtual methods)."""
        try:
            for child in cursor.get_children():
                if (child.kind == CursorKind.CXX_METHOD and 
                    child.is_pure_virtual_method()):
                    return True
        except Exception:
            pass
        return False

    def _create_source_location(self, cursor: Cursor) -> SourceLocation:
        """Create SourceLocation from cursor location."""
        loc = cursor.location
        return SourceLocation(
            file_path=str(loc.file) if loc.file else "",
            line=loc.line,
            column=loc.column,
            offset=loc.offset
        )

    def _map_access_specifier(self, access: ClangAccessSpecifier) -> AccessSpecifier:
        """Map libclang access specifier to our enum."""
        mapping = {
            ClangAccessSpecifier.PUBLIC: AccessSpecifier.PUBLIC,
            ClangAccessSpecifier.PRIVATE: AccessSpecifier.PRIVATE,
            ClangAccessSpecifier.PROTECTED: AccessSpecifier.PROTECTED,
        }
        return mapping.get(access, AccessSpecifier.UNKNOWN)

    def _process_diagnostics(self, diagnostics) -> List[DiagnosticInfo]:
        """Process libclang diagnostics into our format."""
        result = []
        try:
            for diag in diagnostics:
                severity_map = {
                    Diagnostic.Ignored: "ignored",
                    Diagnostic.Note: "note", 
                    Diagnostic.Warning: "warning",
                    Diagnostic.Error: "error",
                    Diagnostic.Fatal: "fatal"
                }
                
                result.append(DiagnosticInfo(
                    severity=severity_map.get(diag.severity, "unknown"),
                    message=diag.spelling,
                    location=SourceLocation(
                        file_path=str(diag.location.file) if diag.location.file else "",
                        line=diag.location.line,
                        column=diag.location.column,
                        offset=diag.location.offset
                    ),
                    category=diag.category_name
                ))
        except Exception as e:
            logger.warning(f"Error processing diagnostics: {e}")
        
        return result

    def _add_to_namespace(
        self, 
        result: AnalysisResult, 
        namespace_stack: List[str], 
        item: Any, 
        item_type: str
    ) -> None:
        """Add an item to the appropriate namespace."""
        try:
            # Find or create nested namespace structure
            current_namespaces = result.namespaces
            for ns_name in namespace_stack:
                # Find existing namespace
                found_ns = None
                for ns in current_namespaces:
                    if ns.name == ns_name:
                        found_ns = ns
                        break
                
                if not found_ns:
                    # Create new namespace
                    found_ns = NamespaceInfo(
                        name=ns_name,
                        kind=ElementKind.NAMESPACE,
                        location=SourceLocation(file_path="", line=0, column=0)
                    )
                    current_namespaces.append(found_ns)
                
                current_namespaces = found_ns.nested_namespaces
            
            # Add item to the final namespace
            target_ns = None
            for ns in (result.namespaces if len(namespace_stack) == 1 else current_namespaces):
                if ns.name == namespace_stack[-1]:
                    target_ns = ns
                    break
            
            if target_ns:
                if item_type == 'class':
                    target_ns.classes.append(item)
                elif item_type == 'function':
                    target_ns.functions.append(item)
                elif item_type == 'variable':
                    target_ns.variables.append(item)
                elif item_type == 'enum':
                    target_ns.enums.append(item)
                    
        except Exception as e:
            logger.warning(f"Error adding to namespace: {e}")

    def _add_to_class(
        self, 
        result: AnalysisResult, 
        namespace_stack: List[str], 
        class_stack: List[str], 
        item: Any, 
        item_type: str
    ) -> None:
        """Add an item to the appropriate class."""
        try:
            # Find the target class
            all_classes = result.get_all_classes()
            target_class = None
            
            for cls in all_classes:
                if cls.name == class_stack[-1]:
                    # Check if namespace matches
                    expected_ns = "::".join(namespace_stack) if namespace_stack else None
                    if cls.namespace == expected_ns:
                        target_class = cls
                        break
            
            if target_class:
                if item_type == 'method':
                    target_class.methods.append(item)
                elif item_type == 'field':
                    target_class.fields.append(item)
                elif item_type == 'enum':
                    target_class.nested_enums.append(item)
                    
        except Exception as e:
            logger.warning(f"Error adding to class: {e}")

    def _create_error_result(self, file_path: str, errors: List[str]) -> AnalysisResult:
        """Create an AnalysisResult with error information."""
        diagnostics = [
            DiagnosticInfo(
                severity="error",
                message=error,
                location=SourceLocation(file_path=file_path, line=0, column=0),
                category="Analysis Error"
            ) for error in errors
        ]
        
        return AnalysisResult(
            file_path=file_path,
            diagnostics=diagnostics,
            analysis_metadata={
                "cpp_standard": self.cpp_standard,
                "analysis_time": datetime.now().isoformat(),
                "analysis_failed": True
            }
        )

    def set_library_path(self, path: str) -> None:
        """Set the libclang library path."""
        Config.set_library_path(path)
        logger.info(f"Set libclang library path to: {path}")