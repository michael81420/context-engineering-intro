#!/usr/bin/env python3
"""
JSON 分析結果讀取和分析工具

用法:
python analyze_json_results.py <json_file> [command] [options]
"""

import json
import sys
import os
from typing import Dict, List, Any
from pathlib import Path


class JsonResultAnalyzer:
    """分析 cpp_analyzer 生成的 JSON 結果"""
    
    def __init__(self, json_file: str):
        """初始化分析器"""
        self.json_file = json_file
        self.data = self._load_json()
        self.is_project_result = self._detect_result_type()
    
    def _load_json(self) -> Any:
        """載入 JSON 檔案"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"錯誤：無法載入 JSON 檔案 - {e}")
            sys.exit(1)
    
    def _detect_result_type(self) -> bool:
        """偵測是單檔案結果還是專案結果"""
        if isinstance(self.data, list):
            return False  # 多檔案結果或單檔案結果列表
        elif isinstance(self.data, dict):
            return 'project_path' in self.data  # 專案結果
        return False
    
    def show_summary(self):
        """顯示結果摘要"""
        print("="*60)
        print("JSON 分析結果摘要")
        print("="*60)
        
        if self.is_project_result:
            self._show_project_summary()
        else:
            self._show_files_summary()
    
    def _show_project_summary(self):
        """顯示專案摘要"""
        project_path = self.data.get('project_path', 'Unknown')
        files_analyzed = self.data.get('files_analyzed', [])
        summary_stats = self.data.get('summary_statistics', {})
        
        print(f"專案路徑: {project_path}")
        print(f"分析的檔案數: {len(files_analyzed)}")
        print("\n專案統計:")
        for key, value in summary_stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    def _show_files_summary(self):
        """顯示檔案摘要"""
        if isinstance(self.data, list):
            files = self.data
        else:
            files = [self.data]
        
        print(f"分析的檔案數: {len(files)}")
        
        total_stats = {
            'classes': 0,
            'functions': 0,
            'variables': 0,
            'namespaces': 0,
            'errors': 0,
            'warnings': 0
        }
        
        print("\n檔案列表:")
        for i, file_data in enumerate(files, 1):
            file_path = file_data.get('file_path', 'Unknown')
            stats = self._calculate_file_stats(file_data)
            
            print(f"  {i}. {os.path.basename(file_path)}")
            print(f"     類別: {stats['classes']}, 函數: {stats['functions']}, 變數: {stats['variables']}")
            
            # 累計統計
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        
        print("\n總計統計:")
        for key, value in total_stats.items():
            print(f"  {key.title()}: {value}")
    
    def _calculate_file_stats(self, file_data: Dict) -> Dict[str, int]:
        """計算單個檔案的統計"""
        stats = {
            'classes': len(file_data.get('classes', [])),
            'functions': len(file_data.get('functions', [])),
            'variables': len(file_data.get('variables', [])),
            'namespaces': len(file_data.get('namespaces', [])),
            'errors': 0,
            'warnings': 0
        }
        
        # 加上嵌套在命名空間中的元素
        for ns in file_data.get('namespaces', []):
            stats['classes'] += len(ns.get('classes', []))
            stats['functions'] += len(ns.get('functions', []))
            stats['variables'] += len(ns.get('variables', []))
        
        # 計算診斷資訊
        for diag in file_data.get('diagnostics', []):
            severity = diag.get('severity', '')
            if severity == 'error':
                stats['errors'] += 1
            elif severity == 'warning':
                stats['warnings'] += 1
        
        return stats
    
    def list_classes(self):
        """列出所有類別"""
        print("="*60)
        print("所有類別")
        print("="*60)
        
        if self.is_project_result:
            results = self.data.get('analysis_results', [])
        else:
            results = self.data if isinstance(self.data, list) else [self.data]
        
        for result in results:
            file_path = result.get('file_path', 'Unknown')
            print(f"\n檔案: {os.path.basename(file_path)}")
            
            # 全域類別
            for cls in result.get('classes', []):
                self._print_class_info(cls, indent="  ")
            
            # 命名空間中的類別
            for ns in result.get('namespaces', []):
                print(f"  命名空間 {ns.get('name', 'Unknown')}:")
                for cls in ns.get('classes', []):
                    self._print_class_info(cls, indent="    ")
    
    def _print_class_info(self, cls: Dict, indent: str = ""):
        """打印類別資訊"""
        name = cls.get('name', 'Unknown')
        kind = cls.get('kind', 'Unknown')
        is_abstract = cls.get('is_abstract', False)
        base_classes = cls.get('base_classes', [])
        methods = cls.get('methods', [])
        fields = cls.get('fields', [])
        
        print(f"{indent}{name} ({kind.split('.')[-1] if '.' in kind else kind})")
        if is_abstract:
            print(f"{indent}  [抽象類別]")
        if base_classes:
            print(f"{indent}  繼承自: {', '.join(base_classes)}")
        print(f"{indent}  方法: {len(methods)}, 欄位: {len(fields)}")
    
    def find_class(self, class_name: str):
        """查找特定類別"""
        print("="*60)
        print(f"搜尋類別: {class_name}")
        print("="*60)
        
        found = False
        
        if self.is_project_result:
            results = self.data.get('analysis_results', [])
        else:
            results = self.data if isinstance(self.data, list) else [self.data]
        
        for result in results:
            file_path = result.get('file_path', 'Unknown')
            
            # 搜尋全域類別
            for cls in result.get('classes', []):
                if cls.get('name') == class_name:
                    print(f"找到於檔案: {os.path.basename(file_path)}")
                    self._print_class_details(cls)
                    found = True
            
            # 搜尋命名空間中的類別
            for ns in result.get('namespaces', []):
                for cls in ns.get('classes', []):
                    if cls.get('name') == class_name:
                        print(f"找到於檔案: {os.path.basename(file_path)}")
                        print(f"命名空間: {ns.get('name')}")
                        self._print_class_details(cls)
                        found = True
        
        if not found:
            print(f"未找到類別 '{class_name}'")
    
    def _print_class_details(self, cls: Dict):
        """打印類別詳細資訊"""
        print(f"\n類別名稱: {cls.get('name')}")
        print(f"類型: {cls.get('kind', 'Unknown').split('.')[-1] if '.' in cls.get('kind', '') else cls.get('kind', 'Unknown')}")
        print(f"抽象類別: {'是' if cls.get('is_abstract') else '否'}")
        
        base_classes = cls.get('base_classes', [])
        if base_classes:
            print(f"基底類別: {', '.join(base_classes)}")
        
        location = cls.get('location', {})
        if location:
            print(f"位置: 第 {location.get('line')} 行, 第 {location.get('column')} 欄")
        
        methods = cls.get('methods', [])
        if methods:
            print(f"\n方法 ({len(methods)}):")
            for method in methods:
                name = method.get('name')
                return_type = method.get('return_type')
                is_virtual = method.get('is_virtual', False)
                is_pure_virtual = method.get('is_pure_virtual', False)
                
                virtual_info = ""
                if is_pure_virtual:
                    virtual_info = " [純虛擬]"
                elif is_virtual:
                    virtual_info = " [虛擬]"
                
                print(f"  - {name}() -> {return_type}{virtual_info}")
        
        fields = cls.get('fields', [])
        if fields:
            print(f"\n欄位 ({len(fields)}):")
            for field in fields:
                name = field.get('name')
                type_name = field.get('type_name')
                print(f"  - {type_name} {name}")
    
    def find_function(self, function_name: str):
        """查找特定函數"""
        print("="*60)
        print(f"搜尋函數: {function_name}")
        print("="*60)
        
        found = False
        
        if self.is_project_result:
            results = self.data.get('analysis_results', [])
        else:
            results = self.data if isinstance(self.data, list) else [self.data]
        
        for result in results:
            file_path = result.get('file_path', 'Unknown')
            
            # 搜尋全域函數
            for func in result.get('functions', []):
                if func.get('name') == function_name:
                    print(f"找到於檔案: {os.path.basename(file_path)} (全域函數)")
                    self._print_function_details(func)
                    found = True
            
            # 搜尋類別方法
            for cls in result.get('classes', []):
                for method in cls.get('methods', []):
                    if method.get('name') == function_name:
                        print(f"找到於檔案: {os.path.basename(file_path)}")
                        print(f"所屬類別: {cls.get('name')}")
                        self._print_function_details(method)
                        found = True
            
            # 搜尋命名空間中的函數和類別方法
            for ns in result.get('namespaces', []):
                for func in ns.get('functions', []):
                    if func.get('name') == function_name:
                        print(f"找到於檔案: {os.path.basename(file_path)}")
                        print(f"命名空間: {ns.get('name')}")
                        self._print_function_details(func)
                        found = True
                
                for cls in ns.get('classes', []):
                    for method in cls.get('methods', []):
                        if method.get('name') == function_name:
                            print(f"找到於檔案: {os.path.basename(file_path)}")
                            print(f"命名空間: {ns.get('name')}")
                            print(f"所屬類別: {cls.get('name')}")
                            self._print_function_details(method)
                            found = True
        
        if not found:
            print(f"未找到函數 '{function_name}'")
    
    def _print_function_details(self, func: Dict):
        """打印函數詳細資訊"""
        print(f"\n函數名稱: {func.get('name')}")
        print(f"返回類型: {func.get('return_type')}")
        
        parameters = func.get('parameters', [])
        if parameters:
            print("參數:")
            for param in parameters:
                name = param.get('name')
                type_name = param.get('type_name')
                print(f"  - {type_name} {name}")
        else:
            print("參數: (無)")
        
        location = func.get('location', {})
        if location:
            print(f"位置: 第 {location.get('line')} 行, 第 {location.get('column')} 欄")
        
        # 函數屬性
        attrs = []
        if func.get('is_virtual'):
            attrs.append('虛擬')
        if func.get('is_pure_virtual'):
            attrs.append('純虛擬')
        if func.get('is_static'):
            attrs.append('靜態')
        if func.get('is_const'):
            attrs.append('常數')
        
        if attrs:
            print(f"屬性: {', '.join(attrs)}")


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze_json_results.py <json_file> [command] [options]")
        print("\n命令:")
        print("  summary              顯示結果摘要 (預設)")
        print("  classes              列出所有類別")
        print("  find-class <name>    查找特定類別")
        print("  find-function <name> 查找特定函數")
        print("\n範例:")
        print("  python analyze_json_results.py results.json")
        print("  python analyze_json_results.py results.json classes")
        print("  python analyze_json_results.py results.json find-class Calculator")
        print("  python analyze_json_results.py results.json find-function calculate")
        sys.exit(1)
    
    json_file = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'summary'
    
    if not os.path.exists(json_file):
        print(f"錯誤: 檔案不存在 - {json_file}")
        sys.exit(1)
    
    analyzer = JsonResultAnalyzer(json_file)
    
    if command == 'summary':
        analyzer.show_summary()
    elif command == 'classes':
        analyzer.list_classes()
    elif command == 'find-class':
        if len(sys.argv) < 4:
            print("錯誤: 請指定要查找的類別名稱")
            sys.exit(1)
        analyzer.find_class(sys.argv[3])
    elif command == 'find-function':
        if len(sys.argv) < 4:
            print("錯誤: 請指定要查找的函數名稱")
            sys.exit(1)
        analyzer.find_function(sys.argv[3])
    else:
        print(f"錯誤: 未知命令 '{command}'")
        sys.exit(1)


if __name__ == "__main__":
    main()