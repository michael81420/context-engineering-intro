name: "C++ Code Analysis Tool - Comprehensive PRP v1.0"
description: |
  Complete implementation of a C++ static analysis tool using Python libclang
  with file indexing, AST traversal, and structured output capabilities.

---

## Goal

Build a production-ready C++ code analysis tool that recursively indexes C++ source files and uses libclang to extract comprehensive structural information including classes, functions, variables, namespaces, and include dependencies. The tool must handle modern C++ features (C++11-20), provide JSON export, and include a CLI interface for analyzing individual files or entire projects.

## Why

- **Developer Productivity**: Enable developers to quickly understand large C++ codebases through automated analysis
- **Code Navigation**: Provide structured data for IDE integrations and code navigation tools  
- **Documentation Generation**: Extract class hierarchies and API structures for automated documentation
- **Static Analysis Foundation**: Create a foundation for building custom C++ static analysis rules
- **Modern C++ Support**: Handle contemporary C++ features that manual parsing cannot handle reliably

## What

A Python package with CLI interface that:

1. **Indexes C++ Files**: Recursively discovers .cpp, .hpp, .h, .cc, .cxx files in project directories
2. **Parses with libclang**: Uses libclang Python bindings to create AST from C++ source files
3. **Extracts Comprehensive Information**:
   - Classes/structs with inheritance, methods, fields, access specifiers
   - Functions with parameters, return types, qualifiers (virtual, static, const, pure virtual)
   - Variables with type information, const/static qualifiers
   - Namespaces with nested structure
   - Include directives and file dependencies
   - Template information where available
   - Source location tracking (file, line, column)
4. **Exports Structured Data**: JSON output for integration with other tools
5. **CLI Interface**: Command-line tool for single files or project analysis
6. **Error Handling**: Graceful handling of syntax errors, missing dependencies

### Success Criteria

- [ ] Successfully parse and analyze the provided sample C++ files (examples/sample_cpp/)
- [ ] Extract all classes, functions, variables, and namespaces with complete metadata
- [ ] Handle C++11-20 features including auto, smart pointers, lambdas, templates
- [ ] Provide JSON export with hierarchical structure preservation
- [ ] CLI interface supports both single file and directory analysis
- [ ] Comprehensive test coverage with pytest including edge cases
- [ ] Handle malformed C++ files without crashing
- [ ] Performance suitable for analyzing large codebases (>1000 files)

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://libclang.readthedocs.io/en/latest/
  why: Official libclang Python API documentation - covers Index, TranslationUnit, Cursor APIs
  critical: Index.create(), cursor traversal patterns, CursorKind enumeration
  
- url: https://clang.llvm.org/docs/IntroductionToTheClangAST.html  
  why: Understanding Clang AST structure and traversal concepts
  critical: AST node relationships, cursor semantics, type system access

- file: examples/sample_cpp/sample.cpp
  why: Comprehensive C++ example with classes, inheritance, templates, namespaces
  critical: Must extract all structural elements from this file accurately

- file: examples/sample_cpp/complex_example.h
  why: Advanced C++ constructs including template specializations, nested classes
  critical: Template handling, complex inheritance patterns, variadic templates

- file: use-cases/pydantic-ai/examples/main_agent_reference/models.py
  why: Pydantic model patterns for structured data representation
  critical: BaseModel usage, Field validation, type hints, Config classes

- file: use-cases/pydantic-ai/examples/main_agent_reference/cli.py  
  why: CLI implementation patterns with Rich console, argument parsing
  critical: Rich console usage, async/await patterns, error handling

- file: use-cases/pydantic-ai/examples/testing_examples/test_agent_patterns.py
  why: Comprehensive pytest patterns for testing complex functionality
  critical: Fixture patterns, async testing, mock usage, edge case testing

- doc: Web search results on libclang Python usage patterns
  section: AST traversal, cursor iteration, compiler argument handling
  critical: Recursive traversal patterns, CursorKind handling, error recovery
```

### Current Codebase Tree
```bash
context-engineering-intro/
├── CLAUDE.md              # Global C++ analysis rules and patterns
├── INITIAL.md             # Feature requirements specification  
├── examples/
│   └── sample_cpp/         # Test C++ files for validation
│       ├── sample.cpp      # Comprehensive C++ example
│       └── complex_example.h # Advanced C++ constructs
├── tests/
│   ├── test_analyzer/      # Empty - to be created
│   ├── test_cli/          # Empty - to be created  
│   └── test_models/       # Empty - to be created
└── use-cases/
    └── pydantic-ai/examples/ # Reference patterns for Python structure
```

### Desired Codebase Tree with Files to be Added
```bash
context-engineering-intro/
├── cpp_analyzer/           # Main package directory
│   ├── __init__.py        # Package initialization with exports
│   ├── analyzer.py        # Main CppAnalyzer class with libclang integration
│   ├── indexer.py         # CppIndexer for file discovery and management
│   ├── models.py          # Pydantic models for analysis results
│   ├── parsers.py         # Specialized parsers for different C++ constructs
│   ├── utils.py           # Utility functions for path handling, AST traversal
│   └── cli.py             # Command-line interface implementation
├── tests/
│   ├── test_analyzer/
│   │   ├── __init__.py
│   │   ├── test_cpp_analyzer.py     # Core analyzer functionality tests
│   │   └── test_ast_traversal.py    # AST traversal and parsing tests
│   ├── test_cli/
│   │   ├── __init__.py
│   │   └── test_cli_interface.py    # CLI command and output tests
│   └── test_models/
│       ├── __init__.py
│       └── test_data_models.py      # Pydantic model validation tests
├── requirements.txt        # Python dependencies including libclang
└── setup.py               # Package installation configuration
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: libclang setup and usage patterns
# 1. libclang shared library must be accessible - may need Config.set_library_path()
# 2. TranslationUnit objects must be properly disposed to avoid memory leaks
# 3. Cursor objects become invalid when TranslationUnit is disposed
from clang.cindex import Config, Index, CursorKind
Config.set_library_path("/path/to/libclang")  # May be needed on some systems

# 4. Template instantiations may not be fully available in AST
# 5. Forward declarations vs full definitions require separate handling
# 6. Include paths must be provided correctly for complex headers
tu = index.parse(filename, args=['-std=c++17', '-I/path/to/headers'])

# 7. Diagnostic checking is essential - files may have syntax errors
for diag in tu.diagnostics:
    if diag.severity >= Diagnostic.Error:
        # Handle compilation errors gracefully

# 8. CursorKind enumeration is extensive - need specific handling for C++ constructs
# CursorKind.CLASS_DECL, CursorKind.CXX_METHOD, CursorKind.NAMESPACE, etc.

# 9. Type information access requires cursor.type and cursor.result_type
# 10. Source location provides offset, line, column - essential for IDE integration
```

## Implementation Blueprint

### Data Models and Structure

Create comprehensive Pydantic models for type safety and JSON serialization:

```python
# cpp_analyzer/models.py - Core data models
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass

class AccessSpecifier(Enum):
    PUBLIC = "public"
    PRIVATE = "private" 
    PROTECTED = "protected"
    UNKNOWN = "unknown"

class CursorKind(Enum):
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
    TEMPLATE = "template"

@dataclass
class SourceLocation:
    file_path: str
    line: int
    column: int
    offset: int = 0

class ParameterInfo(BaseModel):
    name: str
    type_name: str
    default_value: Optional[str] = None
    is_const: bool = False
    is_reference: bool = False
    is_pointer: bool = False

class FunctionInfo(BaseModel):
    name: str
    return_type: str = ""
    parameters: List[ParameterInfo] = []
    is_virtual: bool = False
    is_pure_virtual: bool = False
    is_static: bool = False
    is_const: bool = False
    is_constructor: bool = False
    is_destructor: bool = False
    location: SourceLocation
    access_specifier: AccessSpecifier = AccessSpecifier.UNKNOWN

class ClassInfo(BaseModel):
    name: str
    base_classes: List[str] = []
    methods: List[FunctionInfo] = []
    fields: List['VariableInfo'] = []
    is_abstract: bool = False
    is_template: bool = False
    template_parameters: List[str] = []
    location: SourceLocation
    namespace: Optional[str] = None

class AnalysisResult(BaseModel):
    file_path: str
    classes: List[ClassInfo] = []
    functions: List[FunctionInfo] = []
    variables: List['VariableInfo'] = []
    namespaces: List['NamespaceInfo'] = []
    includes: List['IncludeInfo'] = []
    diagnostics: List[str] = []
    analysis_metadata: Dict[str, Any] = {}
```

### List of Tasks to be Completed in Order

```yaml
Task 1 - Create Core Data Models:
  CREATE cpp_analyzer/models.py:
    - IMPLEMENT all Pydantic models for analysis results
    - INCLUDE SourceLocation, FunctionInfo, ClassInfo, AnalysisResult
    - ADD proper type hints and Field descriptions
    - ENSURE JSON serialization compatibility

Task 2 - Implement libclang Integration:
  CREATE cpp_analyzer/analyzer.py:
    - IMPLEMENT CppAnalyzer class with libclang integration
    - ADD Index creation and TranslationUnit management
    - IMPLEMENT recursive cursor traversal with proper resource cleanup
    - HANDLE different CursorKind types (classes, functions, variables, namespaces)
    - EXTRACT comprehensive information including type data, qualifiers, locations
    - IMPLEMENT error handling for malformed files and missing dependencies

Task 3 - Build File Indexing System:
  CREATE cpp_analyzer/indexer.py:
    - IMPLEMENT CppIndexer class for recursive file discovery
    - SUPPORT multiple C++ file extensions (.cpp, .hpp, .h, .cc, .cxx)
    - ADD file filtering and exclusion patterns
    - IMPLEMENT caching mechanism for unchanged files
    - HANDLE large directory structures efficiently

Task 4 - Create Specialized Parsers:
  CREATE cpp_analyzer/parsers.py:
    - IMPLEMENT specialized parsing for classes, functions, templates
    - HANDLE inheritance hierarchies and access specifiers
    - EXTRACT template parameters and specializations
    - PARSE include directives and dependencies
    - MANAGE namespace resolution and nested structures

Task 5 - Add Utility Functions:
  CREATE cpp_analyzer/utils.py:
    - IMPLEMENT path handling utilities for cross-platform compatibility
    - ADD AST traversal helper functions
    - CREATE type information extraction utilities
    - IMPLEMENT diagnostic processing and error reporting
    - ADD source location formatting and validation

Task 6 - Build CLI Interface:
  CREATE cpp_analyzer/cli.py:
    - IMPLEMENT command-line interface using argparse or Click
    - ADD single file and directory analysis modes
    - SUPPORT output format options (JSON, pretty-print)
    - IMPLEMENT progress reporting for large projects
    - ADD compiler flag configuration options
    - HANDLE C++ standard selection (C++11, C++14, C++17, C++20)

Task 7 - Package Integration:
  CREATE cpp_analyzer/__init__.py:
    - EXPORT main classes and functions
    - SET package version and metadata
    - IMPLEMENT convenient import paths

  CREATE requirements.txt:
    - LIST libclang dependency
    - ADD Pydantic, click/argparse for CLI
    - INCLUDE development dependencies (pytest, mypy, black)

Task 8 - Comprehensive Testing:
  CREATE tests/test_analyzer/test_cpp_analyzer.py:
    - TEST parsing of sample C++ files
    - VERIFY extraction of classes, functions, variables
    - TEST error handling for malformed files
    - VALIDATE template and inheritance handling

  CREATE tests/test_cli/test_cli_interface.py:
    - TEST CLI argument parsing and validation
    - VERIFY output format options
    - TEST single file and directory modes
    - VALIDATE error messages and help text

  CREATE tests/test_models/test_data_models.py:
    - TEST Pydantic model validation
    - VERIFY JSON serialization/deserialization
    - TEST edge cases and invalid data handling
    - VALIDATE model relationships and constraints
```

### Per Task Pseudocode

```python
# Task 2 - Core Analyzer Implementation
class CppAnalyzer:
    def __init__(self, cpp_standard: str = "c++17"):
        # PATTERN: Initialize libclang Index properly
        self.index = Index.create()
        self.cpp_standard = cpp_standard
        self.compiler_args = [f'-std={cpp_standard}']
    
    def analyze_file(self, file_path: str, include_paths: List[str] = None) -> AnalysisResult:
        # CRITICAL: Handle libclang resource management
        args = self.compiler_args.copy()
        if include_paths:
            args.extend([f'-I{path}' for path in include_paths])
        
        # GOTCHA: Must handle parsing failures gracefully
        try:
            tu = self.index.parse(file_path, args=args)
            
            # CRITICAL: Check diagnostics before proceeding
            errors = [d for d in tu.diagnostics if d.severity >= Diagnostic.Error]
            if errors:
                return self._create_error_result(file_path, errors)
            
            # PATTERN: Recursive cursor traversal
            result = AnalysisResult(file_path=file_path)
            self._traverse_ast(tu.cursor, result)
            
            return result
        
        except Exception as e:
            return self._create_error_result(file_path, [str(e)])
    
    def _traverse_ast(self, cursor, result: AnalysisResult, depth: int = 0):
        # PATTERN: Handle different CursorKind types
        if cursor.kind == CursorKind.CLASS_DECL:
            class_info = self._extract_class_info(cursor)
            result.classes.append(class_info)
        
        elif cursor.kind == CursorKind.FUNCTION_DECL:
            func_info = self._extract_function_info(cursor)
            result.functions.append(func_info)
        
        elif cursor.kind == CursorKind.NAMESPACE:
            namespace_info = self._extract_namespace_info(cursor)
            result.namespaces.append(namespace_info)
        
        # CRITICAL: Recurse through children
        for child in cursor.get_children():
            self._traverse_ast(child, result, depth + 1)

# Task 6 - CLI Implementation
def main():
    # PATTERN: Follow rich CLI patterns from examples
    parser = argparse.ArgumentParser(description="C++ Code Analysis Tool")
    parser.add_argument("path", help="File or directory to analyze")
    parser.add_argument("--output", "-o", help="Output file (JSON format)")
    parser.add_argument("--std", default="c++17", help="C++ standard")
    parser.add_argument("--include", "-I", action="append", help="Include paths")
    
    args = parser.parse_args()
    
    # PATTERN: Use Rich console for output formatting
    console = Console()
    
    try:
        analyzer = CppAnalyzer(cpp_standard=args.std)
        
        if os.path.isfile(args.path):
            result = analyzer.analyze_file(args.path, args.include or [])
            output_single_file_result(console, result, args.output)
        
        elif os.path.isdir(args.path):
            indexer = CppIndexer()
            files = indexer.discover_cpp_files(args.path)
            results = analyze_project(analyzer, files, console)
            output_project_results(console, results, args.output)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
```

### Integration Points

```yaml
LIBCLANG:
  - setup: "Ensure libclang shared library is accessible via Config.set_library_path()"
  - parsing: "Use Index.create() and parse with appropriate C++ standard flags"
  - cleanup: "Properly dispose TranslationUnit objects to prevent memory leaks"

FILESYSTEM:
  - discovery: "Recursive file discovery with configurable extensions and exclusions"
  - caching: "Track file modification times to avoid re-parsing unchanged files"
  - paths: "Cross-platform path handling for Windows/Linux/Mac compatibility"

CLI:
  - interface: "Rich-based console output with progress bars for large projects"
  - args: "Support for compiler flags, include paths, C++ standard selection"
  - formats: "JSON export and human-readable pretty-print options"

TESTING:
  - samples: "Use examples/sample_cpp/ files as comprehensive test cases"
  - mocking: "Mock libclang failures for error handling tests"
  - coverage: "Ensure all CursorKind types and edge cases are tested"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
pip install -r requirements.txt  # Install libclang and dependencies
ruff check cpp_analyzer/ --fix   # Auto-fix style issues
mypy cpp_analyzer/               # Type checking

# Expected: No errors. If libclang import fails, may need Config.set_library_path()
```

### Level 2: Unit Tests
```python
# CREATE comprehensive test suite
def test_parse_sample_cpp():
    """Test parsing of sample.cpp file"""
    analyzer = CppAnalyzer()
    result = analyzer.analyze_file("examples/sample_cpp/sample.cpp")
    
    # Verify classes extracted
    assert len(result.classes) >= 2  # Calculator, BasicCalculator
    assert any(cls.name == "Calculator" for cls in result.classes)
    assert any(cls.name == "BasicCalculator" for cls in result.classes)
    
    # Verify inheritance
    basic_calc = next(cls for cls in result.classes if cls.name == "BasicCalculator")
    assert "Calculator" in basic_calc.base_classes
    
    # Verify functions
    assert len(result.functions) >= 1  # findMax template function
    
    # Verify namespaces
    assert any(ns.name == "math" for ns in result.namespaces)

def test_parse_complex_header():
    """Test parsing of complex_example.h"""
    analyzer = CppAnalyzer()
    result = analyzer.analyze_file("examples/sample_cpp/complex_example.h")
    
    # Verify template classes
    assert any(cls.is_template for cls in result.classes)
    
    # Verify nested namespaces
    assert any("data" in ns.name for ns in result.namespaces)

def test_error_handling():
    """Test handling of malformed C++ files"""
    analyzer = CppAnalyzer()
    
    # Create temporary malformed file
    with open("test_malformed.cpp", "w") as f:
        f.write("class UnfinishedClass {\n  // Missing closing brace")
    
    try:
        result = analyzer.analyze_file("test_malformed.cpp")
        assert len(result.diagnostics) > 0  # Should have errors
        assert result.file_path == "test_malformed.cpp"
    finally:
        os.remove("test_malformed.cpp")
```

```bash
# Run and iterate until passing
python -m pytest tests/ -v --tb=short

# If failing: Read error, understand root cause, fix code, re-run
# Common issues: libclang not found, missing include paths, cursor traversal bugs
```

### Level 3: Integration Test
```bash
# Test CLI interface with sample files
python -m cpp_analyzer.cli examples/sample_cpp/sample.cpp --output results.json

# Expected JSON output with complete analysis
cat results.json | jq '.classes[] | .name'
# Should show: "Calculator", "BasicCalculator"

# Test directory analysis
python -m cpp_analyzer.cli examples/sample_cpp/ --std c++17

# Expected: Analysis of all .cpp and .h files in directory
```

## Final Validation Checklist
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `ruff check cpp_analyzer/`
- [ ] No type errors: `mypy cpp_analyzer/`
- [ ] CLI analyzes sample files: `python -m cpp_analyzer.cli examples/sample_cpp/sample.cpp`
- [ ] JSON export works correctly and is valid JSON
- [ ] Error cases handled gracefully (malformed files, missing includes)
- [ ] Memory usage reasonable for large files (no memory leaks)
- [ ] Cross-platform compatibility (Windows/Linux path handling)

---

## Anti-Patterns to Avoid
- ❌ Don't attempt manual C++ parsing - always use libclang
- ❌ Don't ignore TranslationUnit disposal - causes memory leaks
- ❌ Don't assume all cursors have complete type information - templates may be incomplete
- ❌ Don't skip diagnostic checking - files may have syntax errors that affect analysis
- ❌ Don't hardcode include paths - make them configurable via CLI
- ❌ Don't use blocking operations in CLI without progress indication for large projects
- ❌ Don't ignore cross-platform path differences - use pathlib consistently

---

## PRP Quality Score: 9/10

**Confidence Level**: Very High - This PRP provides comprehensive context including:
- ✅ Complete libclang API documentation and usage patterns
- ✅ Real C++ sample files for validation testing
- ✅ Detailed implementation blueprint with task breakdown
- ✅ Existing codebase patterns for Python project structure
- ✅ Comprehensive error handling and edge case considerations
- ✅ Executable validation gates with specific test cases
- ✅ Clear anti-patterns based on libclang gotchas
- ✅ Rich CLI patterns from existing examples

The only minor gap is potential platform-specific libclang setup issues, but the PRP includes guidance for handling these through Config.set_library_path() and proper error handling.