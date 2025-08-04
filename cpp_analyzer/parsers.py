"""
Specialized parsers for different C++ constructs.

This module provides specialized parsing functions for complex C++ language
features like templates, inheritance hierarchies, and advanced type analysis.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

try:
    from clang.cindex import (
        Cursor, CursorKind, TypeKind,
        AccessSpecifier as ClangAccessSpecifier
    )
except ImportError:
    raise ImportError(
        "libclang not found. Please install with: pip install libclang"
    )

from .models import (
    AccessSpecifier, SourceLocation
)

# Set up logging
logger = logging.getLogger(__name__)


class TemplateKind(Enum):
    """Types of C++ templates."""
    FUNCTION_TEMPLATE = "function_template"
    CLASS_TEMPLATE = "class_template"
    VARIABLE_TEMPLATE = "variable_template"
    ALIAS_TEMPLATE = "alias_template"
    CONCEPT = "concept"


class InheritanceType(Enum):
    """Types of inheritance in C++."""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    VIRTUAL = "virtual"


class CppParser:
    """
    Specialized parser for complex C++ constructs.
    
    This class provides methods to parse and analyze advanced C++ features
    that require deeper understanding of the language semantics.
    """

    def __init__(self):
        """Initialize the C++ parser."""
        logger.debug("Initialized CppParser")

    def parse_template_info(self, cursor: Cursor) -> Dict[str, Any]:
        """
        Parse template information from a cursor.
        
        Args:
            cursor: Clang cursor representing a template
            
        Returns:
            Dictionary containing template information
        """
        template_info = {
            "is_template": False,
            "kind": None,
            "parameters": [],
            "specializations": [],
            "instantiations": []
        }

        try:
            # Check if this is a template
            if cursor.kind in [CursorKind.CLASS_TEMPLATE, CursorKind.FUNCTION_TEMPLATE]:
                template_info["is_template"] = True
                
                if cursor.kind == CursorKind.CLASS_TEMPLATE:
                    template_info["kind"] = TemplateKind.CLASS_TEMPLATE.value
                elif cursor.kind == CursorKind.FUNCTION_TEMPLATE:
                    template_info["kind"] = TemplateKind.FUNCTION_TEMPLATE.value

                # Extract template parameters
                template_info["parameters"] = self._extract_template_parameters(cursor)
                
                # Find specializations and instantiations
                template_info["specializations"] = self._find_template_specializations(cursor)

        except Exception as e:
            logger.warning(f"Error parsing template info: {e}")

        return template_info

    def parse_inheritance_hierarchy(self, cursor: Cursor) -> Dict[str, Any]:
        """
        Parse inheritance hierarchy information.
        
        Args:
            cursor: Clang cursor representing a class
            
        Returns:
            Dictionary containing inheritance information
        """
        inheritance_info = {
            "base_classes": [],
            "derived_classes": [],
            "inheritance_depth": 0,
            "is_abstract": False,
            "virtual_methods": [],
            "pure_virtual_methods": []
        }

        try:
            # Extract base classes with access specifiers
            for child in cursor.get_children():
                if child.kind == CursorKind.CXX_BASE_SPECIFIER:
                    base_info = self._parse_base_class_specifier(child)
                    if base_info:
                        inheritance_info["base_classes"].append(base_info)

            # Find virtual and pure virtual methods
            virtual_methods, pure_virtual_methods = self._find_virtual_methods(cursor)
            inheritance_info["virtual_methods"] = virtual_methods
            inheritance_info["pure_virtual_methods"] = pure_virtual_methods
            inheritance_info["is_abstract"] = len(pure_virtual_methods) > 0

            # Calculate inheritance depth (simplified)
            inheritance_info["inheritance_depth"] = len(inheritance_info["base_classes"])

        except Exception as e:
            logger.warning(f"Error parsing inheritance hierarchy: {e}")

        return inheritance_info

    def parse_function_overloads(self, cursor: Cursor, class_cursor: Optional[Cursor] = None) -> List[Dict[str, Any]]:
        """
        Find all overloads of a function.
        
        Args:
            cursor: Function cursor
            class_cursor: Parent class cursor if this is a method
            
        Returns:
            List of overload information
        """
        overloads = []
        function_name = cursor.spelling

        try:
            # Search scope for overloads
            search_cursor = class_cursor if class_cursor else cursor.semantic_parent
            
            if search_cursor:
                for child in search_cursor.get_children():
                    if (child.kind in [CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD] and
                        child.spelling == function_name and
                        child != cursor):
                        
                        overload_info = {
                            "location": self._create_source_location(child),
                            "parameters": self._extract_parameters_detailed(child),
                            "return_type": child.result_type.spelling if child.result_type else "",
                            "is_const": child.is_const_method(),
                            "is_virtual": child.is_virtual_method(),
                            "is_static": child.is_static_method()
                        }
                        overloads.append(overload_info)

        except Exception as e:
            logger.warning(f"Error finding function overloads: {e}")

        return overloads

    def parse_operator_overloads(self, cursor: Cursor) -> List[Dict[str, Any]]:
        """
        Parse operator overload information.
        
        Args:
            cursor: Class cursor
            
        Returns:
            List of operator overload information
        """
        operators = []

        try:
            for child in cursor.get_children():
                if child.kind == CursorKind.CXX_METHOD and child.spelling.startswith("operator"):
                    operator_info = {
                        "operator": child.spelling,
                        "location": self._create_source_location(child),
                        "parameters": self._extract_parameters_detailed(child),
                        "return_type": child.result_type.spelling if child.result_type else "",
                        "is_const": child.is_const_method(),
                        "access_specifier": self._map_access_specifier(child.access_specifier)
                    }
                    operators.append(operator_info)

        except Exception as e:
            logger.warning(f"Error parsing operator overloads: {e}")

        return operators

    def parse_friend_declarations(self, cursor: Cursor) -> List[Dict[str, Any]]:
        """
        Parse friend function and class declarations.
        
        Args:
            cursor: Class cursor
            
        Returns:
            List of friend declaration information
        """
        friends = []

        try:
            for child in cursor.get_children():
                if child.kind == CursorKind.FRIEND_DECL:
                    friend_info = {
                        "type": "unknown",
                        "name": child.spelling,
                        "location": self._create_source_location(child)
                    }

                    # Determine if it's a friend function or class
                    for grandchild in child.get_children():
                        if grandchild.kind in [CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD]:
                            friend_info["type"] = "function"
                            friend_info["signature"] = grandchild.displayname
                        elif grandchild.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
                            friend_info["type"] = "class"

                    friends.append(friend_info)

        except Exception as e:
            logger.warning(f"Error parsing friend declarations: {e}")

        return friends

    def parse_nested_types(self, cursor: Cursor) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse nested types (classes, enums, typedefs, etc.).
        
        Args:
            cursor: Parent cursor (class or namespace)
            
        Returns:
            Dictionary of nested type information by category
        """
        nested_types = {
            "classes": [],
            "enums": [],
            "typedefs": [],
            "using_declarations": [],
            "aliases": []
        }

        try:
            for child in cursor.get_children():
                location = self._create_source_location(child)
                
                if child.kind in [CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL]:
                    nested_types["classes"].append({
                        "name": child.spelling,
                        "kind": "class" if child.kind == CursorKind.CLASS_DECL else "struct",
                        "location": location,
                        "access_specifier": self._map_access_specifier(child.access_specifier)
                    })
                
                elif child.kind == CursorKind.ENUM_DECL:
                    nested_types["enums"].append({
                        "name": child.spelling,
                        "is_scoped": child.is_scoped_enum(),
                        "location": location,
                        "access_specifier": self._map_access_specifier(child.access_specifier)
                    })
                
                elif child.kind == CursorKind.TYPEDEF_DECL:
                    nested_types["typedefs"].append({
                        "name": child.spelling,
                        "underlying_type": child.underlying_typedef_type.spelling if child.underlying_typedef_type else "",
                        "location": location
                    })
                
                elif child.kind == CursorKind.TYPE_ALIAS_DECL:
                    nested_types["aliases"].append({
                        "name": child.spelling,
                        "aliased_type": child.underlying_typedef_type.spelling if child.underlying_typedef_type else "",
                        "location": location
                    })

        except Exception as e:
            logger.warning(f"Error parsing nested types: {e}")

        return nested_types

    def parse_lambda_expressions(self, cursor: Cursor) -> List[Dict[str, Any]]:
        """
        Find and parse lambda expressions in a scope.
        
        Args:
            cursor: Scope cursor to search
            
        Returns:
            List of lambda expression information
        """
        lambdas = []

        try:
            # Recursively search for lambda expressions
            self._find_lambdas_recursive(cursor, lambdas)

        except Exception as e:
            logger.warning(f"Error parsing lambda expressions: {e}")

        return lambdas

    def parse_auto_type_deduction(self, cursor: Cursor) -> Dict[str, Any]:
        """
        Analyze auto type deduction in variable declarations.
        
        Args:
            cursor: Variable declaration cursor
            
        Returns:
            Auto type deduction information
        """
        auto_info = {
            "uses_auto": False,
            "deduced_type": "",
            "is_reference": False,
            "is_pointer": False,
            "is_const": False
        }

        try:
            if cursor.type:
                type_spelling = cursor.type.spelling
                
                if "auto" in type_spelling:
                    auto_info["uses_auto"] = True
                    auto_info["deduced_type"] = type_spelling
                    auto_info["is_reference"] = cursor.type.kind == TypeKind.LVALUEREFERENCE
                    auto_info["is_pointer"] = cursor.type.kind == TypeKind.POINTER
                    auto_info["is_const"] = cursor.type.is_const_qualified()

        except Exception as e:
            logger.warning(f"Error parsing auto type deduction: {e}")

        return auto_info

    def _extract_template_parameters(self, cursor: Cursor) -> List[Dict[str, Any]]:
        """Extract template parameters from a template cursor."""
        parameters = []

        try:
            for child in cursor.get_children():
                if child.kind in [CursorKind.TEMPLATE_TYPE_PARAMETER, 
                                 CursorKind.TEMPLATE_NON_TYPE_PARAMETER]:
                    param_info = {
                        "name": child.spelling,
                        "kind": "type" if child.kind == CursorKind.TEMPLATE_TYPE_PARAMETER else "non_type",
                        "default_value": "",
                        "location": self._create_source_location(child)
                    }

                    # Try to get default value for non-type parameters
                    if child.kind == CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
                        param_info["type"] = child.type.spelling if child.type else ""

                    parameters.append(param_info)

        except Exception as e:
            logger.warning(f"Error extracting template parameters: {e}")

        return parameters

    def _find_template_specializations(self, cursor: Cursor) -> List[Dict[str, Any]]:
        """Find template specializations for a template."""
        specializations = []

        try:
            # This is a simplified approach - full specialization detection
            # would require more sophisticated analysis
            template_name = cursor.spelling
            
            # Search in the same translation unit for specializations
            if cursor.translation_unit:
                for child in cursor.translation_unit.cursor.get_children():
                    if (child.kind in [CursorKind.CLASS_TEMPLATE_SPECIALIZATION, 
                                      CursorKind.FUNCTION_TEMPLATE] and
                        template_name in child.spelling):
                        
                        spec_info = {
                            "name": child.spelling,
                            "location": self._create_source_location(child),
                            "is_partial": False  # Simplified
                        }
                        specializations.append(spec_info)

        except Exception as e:
            logger.warning(f"Error finding template specializations: {e}")

        return specializations

    def _parse_base_class_specifier(self, cursor: Cursor) -> Optional[Dict[str, Any]]:
        """Parse a base class specifier."""
        try:
            base_info = {
                "name": cursor.type.spelling if cursor.type else cursor.spelling,
                "access": self._map_access_specifier(cursor.access_specifier),
                "is_virtual": cursor.is_virtual_base(),
                "location": self._create_source_location(cursor)
            }
            return base_info

        except Exception as e:
            logger.warning(f"Error parsing base class specifier: {e}")
            return None

    def _find_virtual_methods(self, cursor: Cursor) -> Tuple[List[str], List[str]]:
        """Find virtual and pure virtual methods in a class."""
        virtual_methods = []
        pure_virtual_methods = []

        try:
            for child in cursor.get_children():
                if child.kind == CursorKind.CXX_METHOD:
                    if child.is_pure_virtual_method():
                        pure_virtual_methods.append(child.spelling)
                    elif child.is_virtual_method():
                        virtual_methods.append(child.spelling)

        except Exception as e:
            logger.warning(f"Error finding virtual methods: {e}")

        return virtual_methods, pure_virtual_methods

    def _extract_parameters_detailed(self, cursor: Cursor) -> List[Dict[str, Any]]:
        """Extract detailed parameter information."""
        parameters = []

        try:
            for child in cursor.get_children():
                if child.kind == CursorKind.PARM_DECL:
                    param_info = {
                        "name": child.spelling or f"param_{len(parameters)}",
                        "type": child.type.spelling if child.type else "",
                        "is_const": child.type.is_const_qualified() if child.type else False,
                        "is_reference": child.type.kind == TypeKind.LVALUEREFERENCE if child.type else False,
                        "is_pointer": child.type.kind == TypeKind.POINTER if child.type else False,
                        "default_value": None,  # Would need more complex parsing
                        "location": self._create_source_location(child)
                    }
                    parameters.append(param_info)

        except Exception as e:
            logger.warning(f"Error extracting detailed parameters: {e}")

        return parameters

    def _find_lambdas_recursive(self, cursor: Cursor, lambdas: List[Dict[str, Any]]) -> None:
        """Recursively search for lambda expressions."""
        try:
            if cursor.kind == CursorKind.LAMBDA_EXPR:
                lambda_info = {
                    "location": self._create_source_location(cursor),
                    "capture_kind": "unknown",  # Would need more analysis
                    "parameters": [],
                    "return_type": cursor.type.spelling if cursor.type else ""
                }
                lambdas.append(lambda_info)

            # Recurse through children
            for child in cursor.get_children():
                self._find_lambdas_recursive(child, lambdas)

        except Exception as e:
            logger.warning(f"Error in lambda recursive search: {e}")

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


class NamespaceParser:
    """Specialized parser for namespace analysis."""

    def __init__(self):
        """Initialize the namespace parser."""
        logger.debug("Initialized NamespaceParser")

    def parse_namespace_hierarchy(self, cursor: Cursor) -> Dict[str, Any]:
        """
        Parse complete namespace hierarchy information.
        
        Args:
            cursor: Translation unit cursor
            
        Returns:
            Dictionary containing namespace hierarchy
        """
        hierarchy = {
            "namespaces": {},
            "global_declarations": [],
            "using_directives": [],
            "namespace_aliases": []
        }

        try:
            self._build_namespace_hierarchy(cursor, hierarchy, [])

        except Exception as e:
            logger.warning(f"Error parsing namespace hierarchy: {e}")

        return hierarchy

    def _build_namespace_hierarchy(
        self, 
        cursor: Cursor, 
        hierarchy: Dict[str, Any], 
        namespace_path: List[str]
    ) -> None:
        """Recursively build namespace hierarchy."""
        try:
            for child in cursor.get_children():
                if child.kind == CursorKind.NAMESPACE:
                    ns_name = child.spelling
                    full_path = namespace_path + [ns_name]
                    
                    # Create namespace entry
                    current_level = hierarchy["namespaces"]
                    for ns in namespace_path:
                        current_level = current_level.setdefault(ns, {}).setdefault("children", {})
                    
                    if ns_name not in current_level:
                        current_level[ns_name] = {
                            "location": self._create_source_location(child),
                            "declarations": [],
                            "children": {}
                        }
                    
                    # Recursively process namespace contents
                    self._build_namespace_hierarchy(child, hierarchy, full_path)

                elif child.kind == CursorKind.USING_DIRECTIVE:
                    hierarchy["using_directives"].append({
                        "namespace": child.spelling,
                        "location": self._create_source_location(child)
                    })

        except Exception as e:
            logger.warning(f"Error building namespace hierarchy: {e}")

    def _create_source_location(self, cursor: Cursor) -> SourceLocation:
        """Create SourceLocation from cursor location."""
        loc = cursor.location
        return SourceLocation(
            file_path=str(loc.file) if loc.file else "",
            line=loc.line,
            column=loc.column,
            offset=loc.offset
        )