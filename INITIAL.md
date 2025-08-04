## FEATURE:

C++ Code Analysis Tool using Python libclang that provides comprehensive static analysis of C++ source files including:

- **File Indexing System**: Recursively discover and index C++ files (.cpp, .hpp, .h, .cc, .cxx) in project directories
- **AST-based Analysis**: Use libclang to parse C++ code into Abstract Syntax Trees and extract structural information
- **Comprehensive Code Element Extraction**:
  - Classes and structs with inheritance hierarchies, access specifiers, and template information
  - Functions and methods with parameters, return types, qualifiers (virtual, static, const, pure virtual)
  - Variables and fields with type information, const/static qualifiers, and initial values
  - Namespaces with nested structure and contained elements
  - Include directives and dependencies
- **Modern C++ Support**: Handle C++11/14/17/20 features including auto, smart pointers, lambdas, template metaprogramming
- **JSON Export**: Structured output for integration with other tools and IDEs
- **CLI Interface**: Command-line tool for analyzing individual files or entire projects
- **Error Handling**: Graceful handling of syntax errors, missing dependencies, and malformed files

## EXAMPLES:

Sample C++ files have been created in `examples/sample_cpp/` to demonstrate different language features:

- `examples/sample_cpp/sample.cpp` - Comprehensive example showing:
  - Abstract base classes with virtual/pure virtual methods
  - Inheritance hierarchies and access specifiers
  - Template functions and classes
  - Namespaces and nested structures
  - Modern C++ features (smart pointers, auto, range-based loops)
  - Exception handling patterns

- `examples/sample_cpp/complex_example.h` - Advanced C++ constructs including:
  - Template specializations and variadic templates
  - Nested classes and enums within namespaces
  - Friend functions and operator overloading
  - Constexpr functions and alias templates
  - Complex inheritance patterns

The analyzer should be able to parse these files and extract all structural information accurately, providing a foundation for more complex real-world C++ codebases.

## DOCUMENTATION:

**Primary Documentation:**
- libclang Python Documentation: https://libclang.readthedocs.io/en/latest/
- Official Clang Documentation: https://clang.llvm.org/docs/
- Clang AST Internals: https://clang.llvm.org/docs/IntroductionToTheClangAST.html

**Key libclang Concepts to Reference:**
- Index and TranslationUnit creation and management
- Cursor traversal patterns for AST navigation
- CursorKind enumeration for different C++ constructs
- Type system access for extracting type information
- Source location tracking for file/line/column information
- Diagnostic reporting for syntax errors and warnings

**Implementation Resources:**
- Clang Python Bindings API Reference
- Examples of cursor traversal and AST analysis
- Best practices for handling large C++ codebases
- Error handling patterns for malformed source files

## OTHER CONSIDERATIONS:

**Critical Implementation Details:**

1. **libclang Setup Requirements**:
   - Ensure libclang shared library is properly installed and accessible
   - Handle different libclang versions and their API differences
   - Set up appropriate compiler flags and include paths for parsing
   - Support multiple C++ standards through compilation arguments

2. **Performance Considerations**:
   - Implement efficient file indexing to avoid re-parsing unchanged files
   - Use appropriate AST traversal strategies to minimize memory usage
   - Consider parallel processing for analyzing multiple files
   - Implement caching mechanisms for frequently accessed analysis results

3. **Robustness Requirements**:
   - Handle incomplete or syntactically incorrect C++ files gracefully
   - Manage missing header dependencies and system includes
   - Provide meaningful error messages when parsing fails
   - Support analysis of header-only libraries and template-heavy code

4. **Template Handling Gotchas**:
   - Template instantiations may not be fully available in the AST
   - Template parameters and specializations require special handling
   - SFINAE patterns and complex template metaprogramming may have limited analysis
   - Consider both template declarations and their instantiations

5. **Modern C++ Feature Support**:
   - Auto type deduction and decltype expressions
   - Lambda functions with capture lists
   - Smart pointer types and RAII patterns
   - Concept definitions and constraints (C++20)
   - Coroutines and modules (C++20)

6. **Integration Considerations**:
   - Design JSON output schema for compatibility with IDEs and other tools
   - Support incremental analysis for large codebases
   - Provide extensible architecture for adding custom analysis rules
   - Consider integration with build systems (CMake, Make, etc.) for proper compilation flags

7. **Common AI Assistant Pitfalls to Avoid**:
   - Don't attempt manual C++ parsing - always use libclang
   - Don't assume template code will be fully expanded in the AST
   - Handle forward declarations separately from full definitions
   - Remember that header files may contain multiple translation units worth of information
   - Don't ignore libclang diagnostics - they often contain crucial parsing information