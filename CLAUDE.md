### 🔄 Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check `TASK.md`** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.
- **Use venv_linux** (the virtual environment) whenever executing Python commands, including for unit tests.
- **禁止使用EMOJI**

### 🧱 Code Structure & Modularity for C++ Analysis Tool
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
  For C++ analyzer this looks like:
    - `analyzer.py` - Main C++ code analyzer using libclang
    - `indexer.py` - File indexing and discovery functionality
    - `models.py` - Data models for analysis results (classes, functions, variables)
    - `parsers.py` - Specific parsers for different C++ constructs
    - `utils.py` - Utility functions for path handling, AST traversal
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python_dotenv and load_env()** for environment variables.

### 🔍 C++ Analysis Specific Rules
- **Always use libclang for C++ parsing** - never attempt manual parsing of C++ code.
- **Handle libclang Index and TranslationUnit objects properly** - ensure proper cleanup and error handling.
- **Extract comprehensive information from AST nodes**:
  - Classes: inheritance, methods, fields, access specifiers, templates
  - Functions: parameters, return types, virtual/static/const qualifiers
  - Variables: types, const/static qualifiers, initial values
  - Namespaces: nested structure and contained elements
- **Support multiple C++ standards** (C++11, C++14, C++17, C++20) through compiler flags.
- **Handle template code carefully** - templates may not be fully instantiated in AST.
- **Process include directives** to understand dependencies.
- **Capture source location information** (file, line, column) for all elements.

### 🧪 Testing & Reliability for C++ Analysis
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **Include sample C++ files in `examples/sample_cpp/`** for testing different language features:
  - Basic classes and inheritance
  - Templates and template specializations
  - Namespaces and nested namespaces
  - Modern C++ features (auto, smart pointers, lambdas)
  - Complex inheritance hierarchies
- **Test edge cases**:
  - Empty files
  - Files with syntax errors
  - Large files with many classes/functions
  - Files with complex template metaprogramming
- **After updating any logic**, check whether existing unit tests need to be updated.

### ✅ Task Completion for C++ Analyzer
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- **Verify libclang integration** by parsing sample files and extracting expected information.
- **Test with real-world C++ codebases** to ensure robustness.
- Add new sub-tasks or TODOs discovered during development to `TASK.md`.

### 📎 Style & Conventions for C++ Analysis
- **Use Python** as the primary language with **libclang** for C++ parsing.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for data validation** of analysis results.
- **Use dataclasses or Pydantic models** for representing C++ code elements.
- Write **docstrings for every function** using the Google style:
  ```python
  def analyze_cpp_file(file_path: str) -> AnalysisResult:
      """
      Analyze a C++ source file and extract structural information.

      Args:
          file_path (str): Path to the C++ source file to analyze.

      Returns:
          AnalysisResult: Comprehensive analysis results including classes, 
                         functions, variables, and diagnostics.
      
      Raises:
          FileNotFoundError: If the specified file doesn't exist.
          ClangError: If libclang fails to parse the file.
      """
  ```

### 🔧 libclang Integration Guidelines
- **Always import clang.cindex** for accessing libclang functionality.
- **Initialize Index objects properly**:
  ```python
  from clang.cindex import Index, CursorKind
  index = Index.create()
  ```
- **Parse with appropriate compiler flags**:
  ```python
  tu = index.parse(filename, args=['-std=c++17', '-I/path/to/headers'])
  ```
- **Use cursor traversal patterns**:
  ```python
  def traverse_ast(cursor, depth=0):
      # Process current cursor
      for child in cursor.get_children():
          traverse_ast(child, depth + 1)
  ```
- **Handle different CursorKind types**:
  - `CursorKind.CLASS_DECL` for classes
  - `CursorKind.CXX_METHOD` for methods
  - `CursorKind.FUNCTION_DECL` for functions
  - `CursorKind.NAMESPACE` for namespaces
- **Extract type information** using `cursor.type` and `cursor.result_type`.
- **Get source location** using `cursor.location` for file, line, column info.

### 📚 Documentation & Explainability for C++ Analysis
- **Update `README.md`** when new analysis features are added or C++ language support is enhanced.
- **Document supported C++ features** and any limitations of the analysis.
- **Provide examples** of analysis output for different C++ constructs.
- **Include setup instructions** for libclang dependencies and virtual environment.
- When writing complex AST traversal logic, **add `# Reason:` comments** explaining the analysis strategy.

### 🧠 AI Behavior Rules for C++ Analysis
- **Never assume libclang behavior** - always verify with documentation or testing.
- **Handle libclang exceptions gracefully** - files may have syntax errors or missing dependencies.
- **Never hallucinate C++ language features** - only analyze what libclang can parse.
- **Always confirm C++ file paths exist** before attempting analysis.
- **Respect C++ compilation requirements** - include paths, compiler flags, standard versions.
- **When in doubt about C++ semantics**, refer to official C++ standards or libclang documentation.

### 📋 Analysis Output Requirements
- **Structured data models** for all extracted information using Pydantic or dataclasses.
- **JSON serializable results** for integration with other tools.
- **Source location tracking** for all identified elements.
- **Diagnostic information** from libclang for syntax errors or warnings.
- **Hierarchical representation** of namespaces, classes, and nested structures.
- **Type information preservation** including const/volatile qualifiers, references, pointers.
- **Template information** where available from the AST.

### 🔒 Security & Safety for C++ Analysis
- **Validate all file paths** before processing to prevent directory traversal.
- **Set reasonable limits** on file size and analysis depth to prevent resource exhaustion.
- **Handle malformed C++ files safely** - never execute or evaluate C++ code.
- **Sanitize output data** to prevent injection attacks if results are used in web contexts.