#!/usr/bin/env python3
"""
示例脚本：在指定类中查找指定函数

用法:
python find_function_example.py file.cpp ClassName FunctionName
"""

import sys
import json
from cpp_analyzer.analyzer import CppAnalyzer
from cpp_analyzer.models import AnalysisResult


def find_function_in_class(file_path: str, class_name: str, function_name: str):
    """
    在指定文件的指定类中查找指定函数
    
    Args:
        file_path: C++ 文件路径
        class_name: 要查找的类名
        function_name: 要查找的函数名
    """
    try:
        # 初始化分析器
        analyzer = CppAnalyzer(cpp_standard="c++17")
        
        # 分析文件
        print(f"正在分析文件: {file_path}")
        result = analyzer.analyze_file(file_path)
        
        # 获取所有类（包括嵌套类和命名空间中的类）
        all_classes = result.get_all_classes()
        
        # 查找目标类
        target_class = None
        for cls in all_classes:
            if cls.name == class_name:
                target_class = cls
                break
        
        if not target_class:
            print(f"[X] 未找到类 '{class_name}'")
            print(f"可用的类: {[cls.name for cls in all_classes]}")
            return None
        
        print(f"[OK] 找到类 '{class_name}'")
        print(f"   位置: {target_class.location.file_path}:{target_class.location.line}")
        print(f"   命名空间: {target_class.namespace or '(全局)'}")
        print(f"   类型: {'抽象类' if target_class.is_abstract else '具体类'}")
        
        # 查找目标函数
        target_functions = []
        for method in target_class.methods:
            if method.name == function_name:
                target_functions.append(method)
        
        if not target_functions:
            print(f"[X] 在类 '{class_name}' 中未找到函数 '{function_name}'")
            print(f"可用的方法: {[method.name for method in target_class.methods]}")
            return None
        
        # 显示找到的函数
        print(f"\n[FOUND] 找到 {len(target_functions)} 个匹配的函数:")
        for i, func in enumerate(target_functions, 1):
            print(f"\n--- 函数 {i} ---")
            print(f"名称: {func.name}")
            print(f"位置: {func.location.file_path}:{func.location.line}:{func.location.column}")
            print(f"返回类型: {func.return_type}")
            print(f"参数: {len(func.parameters)} 个")
            
            if func.parameters:
                print("参数列表:")
                for j, param in enumerate(func.parameters):
                    print(f"  {j+1}. {param.type_name} {param.name}")
            
            print(f"访问权限: {func.access_specifier.value}")
            print(f"虚函数: {'是' if func.is_virtual else '否'}")
            print(f"纯虚函数: {'是' if func.is_pure_virtual else '否'}")
            print(f"静态函数: {'是' if func.is_static else '否'}")
            print(f"常量函数: {'是' if func.is_const else '否'}")
            print(f"构造函数: {'是' if func.is_constructor else '否'}")
            print(f"析构函数: {'是' if func.is_destructor else '否'}")
        
        return target_functions
        
    except Exception as e:
        print(f"[ERROR] 分析失败: {e}")
        return None


def main():
    if len(sys.argv) < 4:
        print("用法: python find_function_example.py <file.cpp> <ClassName> <FunctionName>")
        print("示例: python find_function_example.py sample.cpp Calculator calculate")
        sys.exit(1)
    
    file_path = sys.argv[1]
    class_name = sys.argv[2]
    function_name = sys.argv[3]
    
    print(f"查找任务:")
    print(f"   文件: {file_path}")
    print(f"   类名: {class_name}")
    print(f"   函数名: {function_name}")
    print("-" * 50)
    
    functions = find_function_in_class(file_path, class_name, function_name)
    
    if functions:
        print(f"\n[SUCCESS] 查找完成! 共找到 {len(functions)} 个匹配项")
    else:
        print(f"\n[FAIL] 查找完成，但未找到匹配项")


if __name__ == "__main__":
    main()