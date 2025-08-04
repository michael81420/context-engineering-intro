#!/usr/bin/env python3
"""
Find specific function in specific class from C++ files

Usage:
python find_function.py file.cpp ClassName FunctionName
"""

import sys
import json
from cpp_analyzer.analyzer import CppAnalyzer
from cpp_analyzer.models import AnalysisResult


def find_function_in_class(file_path: str, class_name: str, function_name: str):
    """
    Find specific function in specific class from C++ file
    
    Args:
        file_path: C++ file path
        class_name: Target class name
        function_name: Target function name
    """
    try:
        # Initialize analyzer
        analyzer = CppAnalyzer(cpp_standard="c++17")
        
        # Analyze file
        print(f"Analyzing file: {file_path}")
        result = analyzer.analyze_file(file_path)
        
        # Get all classes (including nested and namespaced classes)
        all_classes = result.get_all_classes()
        
        # Find target class
        target_class = None
        for cls in all_classes:
            if cls.name == class_name:
                target_class = cls
                break
        
        if not target_class:
            print(f"[X] Class '{class_name}' not found")
            print(f"Available classes: {[cls.name for cls in all_classes]}")
            return None
        
        print(f"[OK] Found class '{class_name}'")
        print(f"   Location: {target_class.location.file_path}:{target_class.location.line}")
        print(f"   Namespace: {target_class.namespace or '(global)'}")
        print(f"   Type: {'Abstract' if target_class.is_abstract else 'Concrete'}")
        
        # Find target function
        target_functions = []
        for method in target_class.methods:
            if method.name == function_name:
                target_functions.append(method)
        
        if not target_functions:
            print(f"[X] Function '{function_name}' not found in class '{class_name}'")
            print(f"Available methods: {[method.name for method in target_class.methods]}")
            return None
        
        # Display found functions
        print(f"\n[FOUND] Found {len(target_functions)} matching function(s):")
        for i, func in enumerate(target_functions, 1):
            print(f"\n--- Function {i} ---")
            print(f"Name: {func.name}")
            print(f"Location: {func.location.file_path}:{func.location.line}:{func.location.column}")
            print(f"Return type: {func.return_type}")
            print(f"Parameters: {len(func.parameters)}")
            
            if func.parameters:
                print("Parameter list:")
                for j, param in enumerate(func.parameters):
                    print(f"  {j+1}. {param.type_name} {param.name}")
            
            print(f"Access: {func.access_specifier.value}")
            print(f"Virtual: {'Yes' if func.is_virtual else 'No'}")
            print(f"Pure virtual: {'Yes' if func.is_pure_virtual else 'No'}")
            print(f"Static: {'Yes' if func.is_static else 'No'}")
            print(f"Const: {'Yes' if func.is_const else 'No'}")
            print(f"Constructor: {'Yes' if func.is_constructor else 'No'}")
            print(f"Destructor: {'Yes' if func.is_destructor else 'No'}")
        
        return target_functions
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        return None


def main():
    if len(sys.argv) < 4:
        print("Usage: python find_function.py <file.cpp> <ClassName> <FunctionName>")
        print("Example: python find_function.py sample.cpp Calculator calculate")
        sys.exit(1)
    
    file_path = sys.argv[1]
    class_name = sys.argv[2]
    function_name = sys.argv[3]
    
    print(f"Search task:")
    print(f"   File: {file_path}")
    print(f"   Class: {class_name}")
    print(f"   Function: {function_name}")
    print("-" * 50)
    
    functions = find_function_in_class(file_path, class_name, function_name)
    
    if functions:
        print(f"\n[SUCCESS] Search completed! Found {len(functions)} match(es)")
    else:
        print(f"\n[FAIL] Search completed, but no matches found")


if __name__ == "__main__":
    main()