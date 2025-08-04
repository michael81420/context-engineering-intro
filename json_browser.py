#!/usr/bin/env python3
"""
簡單的 JSON 瀏覽器，用於互動式瀏覽 cpp_analyzer 結果

用法:
python json_browser.py <json_file>
"""

import json
import sys
import os
from typing import Dict, List, Any


def load_json(file_path: str) -> Any:
    """載入 JSON 檔案"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"錯誤：無法載入 JSON 檔案 - {e}")
        sys.exit(1)


def browse_interactively(data: Any):
    """互動式瀏覽 JSON 資料"""
    print("=== C++ 分析結果互動式瀏覽器 ===")
    print("輸入 'help' 查看可用命令，輸入 'quit' 退出")
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'q':
                print("再見！")
                break
            elif command == 'help' or command == 'h':
                print_help()
            elif command == 'summary' or command == 's':
                show_summary(data)
            elif command == 'files' or command == 'f':
                list_files(data)
            elif command.startswith('classes'):
                parts = command.split()
                if len(parts) > 1:
                    find_class(data, parts[1])
                else:
                    list_all_classes(data)
            elif command.startswith('functions'):
                parts = command.split()
                if len(parts) > 1:
                    find_function(data, parts[1])
                else:
                    list_all_functions(data)
            elif command == 'tree':
                show_tree_structure(data)
            else:
                print(f"未知命令: {command}. 輸入 'help' 查看可用命令")
        
        except KeyboardInterrupt:
            print("\n再見！")
            break
        except Exception as e:
            print(f"錯誤：{e}")


def print_help():
    """顯示幫助資訊"""
    print("\n可用命令:")
    print("  help, h              顯示此幫助資訊")
    print("  summary, s           顯示分析摘要")
    print("  files, f             列出所有檔案")
    print("  classes              列出所有類別")
    print("  classes <name>       查找特定類別")
    print("  functions            列出所有函數")
    print("  functions <name>     查找特定函數")
    print("  tree                 顯示專案結構樹")
    print("  quit, q              退出程式")


def show_summary(data: Any):
    """顯示摘要資訊"""
    print("\n=== 分析摘要 ===")
    
    if isinstance(data, list):
        files = data
    elif isinstance(data, dict) and 'analysis_results' in data:
        files = data['analysis_results']
    else:
        files = [data]
    
    total_classes = 0
    total_functions = 0
    total_variables = 0
    total_namespaces = 0
    
    for file_data in files:
        # 計算各類元素
        total_classes += len(file_data.get('classes', []))
        total_functions += len(file_data.get('functions', []))
        total_variables += len(file_data.get('variables', []))
        total_namespaces += len(file_data.get('namespaces', []))
        
        # 加上命名空間中的元素
        for ns in file_data.get('namespaces', []):
            total_classes += len(ns.get('classes', []))
            total_functions += len(ns.get('functions', []))
            total_variables += len(ns.get('variables', []))
    
    print(f"檔案數量: {len(files)}")
    print(f"總類別數: {total_classes}")
    print(f"總函數數: {total_functions}")
    print(f"總變數數: {total_variables}")
    print(f"命名空間數: {total_namespaces}")


def list_files(data: Any):
    """列出所有檔案"""
    print("\n=== 檔案清單 ===")
    
    if isinstance(data, list):
        files = data
    elif isinstance(data, dict) and 'analysis_results' in data:
        files = data['analysis_results']
    else:
        files = [data]
    
    for i, file_data in enumerate(files, 1):
        file_path = file_data.get('file_path', 'Unknown')
        filename = os.path.basename(file_path)
        
        classes_count = len(file_data.get('classes', []))
        functions_count = len(file_data.get('functions', []))
        
        # 加上命名空間中的元素
        for ns in file_data.get('namespaces', []):
            classes_count += len(ns.get('classes', []))
            functions_count += len(ns.get('functions', []))
        
        print(f"{i:2d}. {filename}")
        print(f"     類別: {classes_count}, 函數: {functions_count}")


def list_all_classes(data: Any):
    """列出所有類別"""
    print("\n=== 所有類別 ===")
    
    if isinstance(data, list):
        files = data
    elif isinstance(data, dict) and 'analysis_results' in data:
        files = data['analysis_results']
    else:
        files = [data]
    
    for file_data in files:
        file_path = file_data.get('file_path', 'Unknown')
        filename = os.path.basename(file_path)
        
        # 全域類別
        classes = file_data.get('classes', [])
        if classes:
            print(f"\n{filename} (全域):")
            for cls in classes:
                name = cls.get('name', 'Unknown')
                kind = cls.get('kind', '').split('.')[-1] if '.' in cls.get('kind', '') else cls.get('kind', '')
                print(f"  - {name} ({kind})")
        
        # 命名空間中的類別
        for ns in file_data.get('namespaces', []):
            ns_classes = ns.get('classes', [])
            if ns_classes:
                ns_name = ns.get('name', 'Unknown')
                print(f"\n{filename} (命名空間: {ns_name}):")
                for cls in ns_classes:
                    name = cls.get('name', 'Unknown')
                    kind = cls.get('kind', '').split('.')[-1] if '.' in cls.get('kind', '') else cls.get('kind', '')
                    print(f"  - {name} ({kind})")


def find_class(data: Any, class_name: str):
    """查找特定類別"""
    print(f"\n=== 搜尋類別: {class_name} ===")
    
    if isinstance(data, list):
        files = data
    elif isinstance(data, dict) and 'analysis_results' in data:
        files = data['analysis_results']
    else:
        files = [data]
    
    found = False
    
    for file_data in files:
        file_path = file_data.get('file_path', 'Unknown')
        filename = os.path.basename(file_path)
        
        # 搜尋全域類別
        for cls in file_data.get('classes', []):
            if cls.get('name') == class_name:
                print(f"\n找到於: {filename} (全域)")
                print_class_details(cls)
                found = True
        
        # 搜尋命名空間中的類別
        for ns in file_data.get('namespaces', []):
            for cls in ns.get('classes', []):
                if cls.get('name') == class_name:
                    print(f"\n找到於: {filename}")
                    print(f"命名空間: {ns.get('name')}")
                    print_class_details(cls)
                    found = True
    
    if not found:
        print(f"未找到類別 '{class_name}'")


def print_class_details(cls: Dict):
    """打印類別詳細資訊"""
    name = cls.get('name', 'Unknown')
    kind = cls.get('kind', '').split('.')[-1] if '.' in cls.get('kind', '') else cls.get('kind', '')
    is_abstract = cls.get('is_abstract', False)
    
    print(f"名稱: {name}")
    print(f"類型: {kind}")
    if is_abstract:
        print("特性: 抽象類別")
    
    base_classes = cls.get('base_classes', [])
    if base_classes:
        print(f"繼承自: {', '.join(base_classes)}")
    
    methods = cls.get('methods', [])
    fields = cls.get('fields', [])
    print(f"方法數: {len(methods)}")
    print(f"欄位數: {len(fields)}")
    
    if methods:
        print("主要方法:")
        for method in methods[:5]:  # 只顯示前5個
            name = method.get('name', 'Unknown')
            return_type = method.get('return_type', 'void')
            print(f"  - {name}() -> {return_type}")
        if len(methods) > 5:
            print(f"  ... 還有 {len(methods) - 5} 個方法")


def list_all_functions(data: Any):
    """列出所有函數"""
    print("\n=== 所有函數 ===")
    
    if isinstance(data, list):
        files = data
    elif isinstance(data, dict) and 'analysis_results' in data:
        files = data['analysis_results']
    else:
        files = [data]
    
    for file_data in files:
        file_path = file_data.get('file_path', 'Unknown')
        filename = os.path.basename(file_path)
        
        # 全域函數
        functions = file_data.get('functions', [])
        if functions:
            print(f"\n{filename} (全域函數):")
            for func in functions:
                name = func.get('name', 'Unknown')
                return_type = func.get('return_type', 'void')
                print(f"  - {name}() -> {return_type}")


def find_function(data: Any, function_name: str):
    """查找特定函數"""
    print(f"\n=== 搜尋函數: {function_name} ===")
    
    if isinstance(data, list):
        files = data
    elif isinstance(data, dict) and 'analysis_results' in data:
        files = data['analysis_results']
    else:
        files = [data]
    
    found = False
    
    for file_data in files:
        file_path = file_data.get('file_path', 'Unknown')
        filename = os.path.basename(file_path)
        
        # 搜尋全域函數
        for func in file_data.get('functions', []):
            if func.get('name') == function_name:
                print(f"\n找到於: {filename} (全域函數)")
                print_function_details(func)
                found = True
        
        # 搜尋類別方法
        for cls in file_data.get('classes', []):
            for method in cls.get('methods', []):
                if method.get('name') == function_name:
                    print(f"\n找到於: {filename}")
                    print(f"所屬類別: {cls.get('name')}")
                    print_function_details(method)
                    found = True
        
        # 搜尋命名空間
        for ns in file_data.get('namespaces', []):
            for func in ns.get('functions', []):
                if func.get('name') == function_name:
                    print(f"\n找到於: {filename}")
                    print(f"命名空間: {ns.get('name')}")
                    print_function_details(func)
                    found = True
            
            for cls in ns.get('classes', []):
                for method in cls.get('methods', []):
                    if method.get('name') == function_name:
                        print(f"\n找到於: {filename}")
                        print(f"命名空間: {ns.get('name')}")
                        print(f"所屬類別: {cls.get('name')}")
                        print_function_details(method)
                        found = True
    
    if not found:
        print(f"未找到函數 '{function_name}'")


def print_function_details(func: Dict):
    """打印函數詳細資訊"""
    name = func.get('name', 'Unknown')
    return_type = func.get('return_type', 'void')
    
    print(f"名稱: {name}")
    print(f"返回類型: {return_type}")
    
    parameters = func.get('parameters', [])
    if parameters:
        print("參數:")
        for param in parameters:
            param_name = param.get('name', 'Unknown')
            param_type = param.get('type_name', 'Unknown')
            print(f"  - {param_type} {param_name}")
    else:
        print("參數: (無)")


def show_tree_structure(data: Any):
    """顯示樹狀結構"""
    print("\n=== 專案結構樹 ===")
    
    if isinstance(data, list):
        files = data
    elif isinstance(data, dict) and 'analysis_results' in data:
        files = data['analysis_results']
    else:
        files = [data]
    
    for file_data in files:
        file_path = file_data.get('file_path', 'Unknown')
        filename = os.path.basename(file_path)
        
        print(f"\n📁 {filename}")
        
        # 全域元素
        classes = file_data.get('classes', [])
        functions = file_data.get('functions', [])
        
        for cls in classes:
            print(f"  ├── 🏛️  {cls.get('name')} (class)")
            methods = cls.get('methods', [])
            for i, method in enumerate(methods):
                connector = "└──" if i == len(methods) - 1 else "├──"
                print(f"      {connector} ⚙️  {method.get('name')}()")
        
        for func in functions:
            print(f"  ├── ⚙️  {func.get('name')}() (function)")
        
        # 命名空間
        for ns in file_data.get('namespaces', []):
            print(f"  ├── 📦 {ns.get('name')} (namespace)")
            
            ns_classes = ns.get('classes', [])
            ns_functions = ns.get('functions', [])
            
            for cls in ns_classes:
                print(f"      ├── 🏛️  {cls.get('name')} (class)")
                methods = cls.get('methods', [])
                for i, method in enumerate(methods[:3]):  # 只顯示前3個方法
                    connector = "└──" if i == len(methods[:3]) - 1 else "├──"
                    print(f"          {connector} ⚙️  {method.get('name')}()")
                if len(methods) > 3:
                    print(f"          └── ... (+{len(methods) - 3} more methods)")
            
            for func in ns_functions:
                print(f"      ├── ⚙️  {func.get('name')}() (function)")


def main():
    if len(sys.argv) != 2:
        print("用法: python json_browser.py <json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"錯誤: 檔案不存在 - {json_file}")
        sys.exit(1)
    
    data = load_json(json_file)
    browse_interactively(data)


if __name__ == "__main__":
    main()