#!/usr/bin/env python3
"""
Command-line interface for C++ code analysis tool.

This module provides a comprehensive CLI for analyzing C++ source files
and projects using libclang with Rich console output.
"""

import os
import sys
import argparse
import json
from typing import List, Dict, Any, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import (
        Progress, SpinnerColumn, TextColumn, 
        BarColumn, TimeRemainingColumn, MofNCompleteColumn
    )
    from rich.syntax import Syntax
    from rich.tree import Tree
except ImportError:
    raise ImportError(
        "Rich library not found. Please install with: pip install rich"
    )

from .analyzer import CppAnalyzer
from .indexer import CppIndexer, FileInfo
from .models import AnalysisResult, ProjectAnalysisResult
from .utils import (
    SystemUtils, 
    setup_logging
)

# Initialize console
console = Console()


class CppAnalyzerCLI:
    """Command-line interface for C++ code analysis."""

    def __init__(self):
        """Initialize the CLI."""
        self.analyzer: Optional[CppAnalyzer] = None
        self.indexer: Optional[CppIndexer] = None

    def main(self) -> int:
        """
        Main entry point for the CLI.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            args = self._parse_arguments()
            
            # Set up logging
            log_level = "DEBUG" if args.verbose else "INFO"
            if args.quiet:
                log_level = "WARNING"
            
            log_file = args.log_file if hasattr(args, 'log_file') else None
            setup_logging(log_level, log_file)
            
            # Initialize components
            self._initialize_components(args)
            
            # Execute command
            return self._execute_command(args)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            return 1
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            try:
                if hasattr(args, 'verbose') and args.verbose:
                    console.print_exception()
            except NameError:
                # args not defined yet, skip verbose output
                pass
            return 1

    def _parse_arguments(self) -> argparse.Namespace:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(
            description="C++ Code Analysis Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s analyze file.cpp                    # Analyze single file
  %(prog)s analyze src/ --recursive            # Analyze directory recursively
  %(prog)s analyze src/ --output results.json # Save results to JSON
  %(prog)s project src/ --summary              # Project-wide analysis summary
  %(prog)s info --system                       # Show system information
            """
        )
        
        # Global options
        parser.add_argument(
            "--verbose", "-v", action="store_true",
            help="Enable verbose output"
        )
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress non-essential output"
        )
        parser.add_argument(
            "--std", default="c++17",
            choices=["c++11", "c++14", "c++17", "c++20"],
            help="C++ standard to use (default: c++17)"
        )
        parser.add_argument(
            "-I", action="append", dest="include_paths",
            help="Add include directory (can be used multiple times)"
        )
        parser.add_argument(
            "--define", "-D", action="append", dest="defines",
            help="Define macro (format: NAME=VALUE)"
        )
        parser.add_argument(
            "--libclang-path",
            help="Path to libclang library"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Analyze command
        analyze_parser = subparsers.add_parser(
            "analyze", help="Analyze C++ files or directories"
        )
        analyze_parser.add_argument(
            "path", help="File or directory to analyze"
        )
        analyze_parser.add_argument(
            "--output", "-o", help="Output file for results (JSON format)"
        )
        analyze_parser.add_argument(
            "--recursive", "-r", action="store_true",
            help="Recursively analyze directories"
        )
        analyze_parser.add_argument(
            "--format", choices=["json", "table", "tree"], default="table",
            help="Output format (default: table)"
        )
        analyze_parser.add_argument(
            "--include-headers", action="store_true", default=True,
            help="Include header files in analysis"
        )
        analyze_parser.add_argument(
            "--include-sources", action="store_true", default=True,
            help="Include source files in analysis"
        )
        
        # Project command
        project_parser = subparsers.add_parser(
            "project", help="Analyze entire project"
        )
        project_parser.add_argument(
            "path", help="Project root directory"
        )
        project_parser.add_argument(
            "--output", "-o", help="Output file for results"
        )
        project_parser.add_argument(
            "--summary", action="store_true",
            help="Show project summary only"
        )
        project_parser.add_argument(
            "--exclude-tests", action="store_true",
            help="Exclude test files from analysis"
        )
        project_parser.add_argument(
            "--exclude-examples", action="store_true",
            help="Exclude example files from analysis"
        )
        
        # Index command
        index_parser = subparsers.add_parser(
            "index", help="Index C++ files in a project"
        )
        index_parser.add_argument(
            "path", help="Directory to index"
        )
        index_parser.add_argument(
            "--clear-cache", action="store_true",
            help="Clear existing cache before indexing"
        )
        index_parser.add_argument(
            "--cache-info", action="store_true",
            help="Show cache information"
        )
        
        # Info command
        info_parser = subparsers.add_parser(
            "info", help="Show system and tool information"
        )
        info_parser.add_argument(
            "--system", action="store_true",
            help="Show system information"
        )
        info_parser.add_argument(
            "--compilers", action="store_true",
            help="Show compiler information"
        )
        info_parser.add_argument(
            "--libclang", action="store_true",
            help="Show libclang information"
        )
        
        args = parser.parse_args()
        
        # Set default command if none specified
        if not args.command:
            if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
                # Assume analyze command if path is provided
                args.command = "analyze"
                args.path = sys.argv[1]
                args.output = None
                args.recursive = True
                args.format = "table"
                args.include_headers = True
                args.include_sources = True
            else:
                parser.print_help()
                sys.exit(1)
        
        return args

    def _initialize_components(self, args: argparse.Namespace) -> None:
        """Initialize analyzer and indexer components."""
        # Initialize analyzer
        self.analyzer = CppAnalyzer(
            cpp_standard=args.std,
            library_path=args.libclang_path
        )
        
        # Initialize indexer
        self.indexer = CppIndexer()

    def _execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command."""
        if args.command == "analyze":
            return self._cmd_analyze(args)
        elif args.command == "project":
            return self._cmd_project(args)
        elif args.command == "index":
            return self._cmd_index(args)
        elif args.command == "info":
            return self._cmd_info(args)
        else:
            console.print(f"[red]Unknown command: {args.command}[/red]")
            return 1

    def _cmd_analyze(self, args: argparse.Namespace) -> int:
        """Execute analyze command."""
        if not os.path.exists(args.path):
            console.print(f"[red]Path does not exist: {args.path}[/red]")
            return 1
        
        console.print(f"[blue]Analyzing: {args.path}[/blue]")
        
        try:
            if os.path.isfile(args.path):
                # Single file analysis
                result = self._analyze_single_file(args.path, args)
                if result:
                    self._display_analysis_result(result, args.format)
                    if args.output:
                        self._save_results([result], args.output)
            else:
                # Directory analysis
                results = self._analyze_directory(args.path, args)
                if results:
                    if len(results) == 1:
                        self._display_analysis_result(results[0], args.format)
                    else:
                        self._display_multiple_results(results, args.format)
                    
                    if args.output:
                        self._save_results(results, args.output)
            
            return 0
            
        except Exception as e:
            console.print(f"[red]Analysis failed: {e}[/red]")
            return 1

    def _cmd_project(self, args: argparse.Namespace) -> int:
        """Execute project command."""
        if not os.path.isdir(args.path):
            console.print(f"[red]Project directory does not exist: {args.path}[/red]")
            return 1
        
        try:
            console.print(f"[blue]Analyzing project: {args.path}[/blue]")
            
            # Discover project files
            categorized_files = self.indexer.get_project_files(
                args.path,
                include_tests=not args.exclude_tests,
                include_examples=not args.exclude_examples
            )
            
            # Analyze all files
            all_results = []
            total_files = sum(len(files) for files in categorized_files.values())
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing files...", total=total_files)
                
                for category, files in categorized_files.items():
                    for file_info in files:
                        result = self._analyze_single_file(file_info.file_path, args)
                        if result:
                            all_results.append(result)
                        progress.advance(task)
            
            # Create project result
            project_result = ProjectAnalysisResult(
                project_path=args.path,
                files_analyzed=[r.file_path for r in all_results],
                analysis_results=all_results
            )
            project_result.summary_statistics = project_result.get_project_statistics()
            
            if args.summary:
                self._display_project_summary(project_result)
            else:
                self._display_project_results(project_result)
            
            if args.output:
                self._save_project_results(project_result, args.output)
            
            return 0
            
        except Exception as e:
            console.print(f"[red]Project analysis failed: {e}[/red]")
            return 1

    def _cmd_index(self, args: argparse.Namespace) -> int:
        """Execute index command."""
        try:
            if args.clear_cache:
                self.indexer.clear_cache(args.path)
                console.print("[green]Cache cleared[/green]")
            
            if args.cache_info:
                cache_info = self.indexer.get_cache_info(args.path)
                self._display_cache_info(cache_info)
                return 0
            
            console.print(f"[blue]Indexing: {args.path}[/blue]")
            
            files = self.indexer.discover_cpp_files(args.path)
            
            console.print(f"[green]Found {len(files)} C++ files[/green]")
            self._display_file_list(files)
            
            return 0
            
        except Exception as e:
            console.print(f"[red]Indexing failed: {e}[/red]")
            return 1

    def _cmd_info(self, args: argparse.Namespace) -> int:
        """Execute info command."""
        try:
            if args.system:
                self._display_system_info()
            
            if args.compilers:
                self._display_compiler_info()
            
            if args.libclang:
                self._display_libclang_info()
            
            if not any([args.system, args.compilers, args.libclang]):
                # Show all info by default
                self._display_system_info()
                console.print()
                self._display_compiler_info()
                console.print()
                self._display_libclang_info()
            
            return 0
            
        except Exception as e:
            console.print(f"[red]Info command failed: {e}[/red]")
            return 1

    def _analyze_single_file(self, file_path: str, args: argparse.Namespace) -> Optional[AnalysisResult]:
        """Analyze a single file."""
        try:
            result = self.analyzer.analyze_file(
                file_path=file_path,
                include_paths=args.include_paths or [],
                define_macros=args.defines or []
            )
            return result
        except Exception as e:
            console.print(f"[red]Error analyzing {file_path}: {e}[/red]")
            return None

    def _analyze_directory(self, dir_path: str, args: argparse.Namespace) -> List[AnalysisResult]:
        """Analyze all C++ files in a directory."""
        # Discover files
        files = self.indexer.discover_cpp_files(
            dir_path,
            recursive=args.recursive,
            include_headers=args.include_headers,
            include_sources=args.include_sources
        )
        
        results = []
        
        if not files:
            console.print("[yellow]No C++ files found[/yellow]")
            return results
        
        # Analyze with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing files...", total=len(files))
            
            for file_info in files:
                result = self._analyze_single_file(file_info.file_path, args)
                if result:
                    results.append(result)
                progress.advance(task)
        
        return results

    def _display_analysis_result(self, result: AnalysisResult, format_type: str) -> None:
        """Display analysis result in specified format."""
        if format_type == "json":
            console.print(Syntax(
                json.dumps(result.model_dump(), indent=2, default=str),
                "json",
                theme="monokai"
            ))
        elif format_type == "tree":
            self._display_result_tree(result)
        else:  # table format
            self._display_result_table(result)

    def _display_result_table(self, result: AnalysisResult) -> None:
        """Display analysis result as a table."""
        # File header
        console.print(Panel(
            f"[bold blue]{result.file_path}[/bold blue]",
            title="Analysis Result"
        ))
        
        # Statistics
        stats = result.get_statistics()
        stats_table = Table(title="Statistics", show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")
        
        for key, value in stats.items():
            stats_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(stats_table)
        
        # Diagnostics
        if result.diagnostics:
            console.print()
            diag_table = Table(title="Diagnostics", show_header=True)
            diag_table.add_column("Severity", style="red")
            diag_table.add_column("Message", style="white")
            diag_table.add_column("Location", style="dim")
            
            for diag in result.diagnostics[:10]:  # Show first 10
                diag_table.add_row(
                    diag.severity,
                    diag.message[:80] + "..." if len(diag.message) > 80 else diag.message,
                    f"{diag.location.line}:{diag.location.column}"
                )
            
            console.print(diag_table)

    def _display_result_tree(self, result: AnalysisResult) -> None:
        """Display analysis result as a tree."""
        tree = Tree(f"[bold blue]{os.path.basename(result.file_path)}[/bold blue]")
        
        # Add classes
        if result.classes:
            classes_branch = tree.add("[cyan]Classes[/cyan]")
            for cls in result.classes:
                class_node = classes_branch.add(f"[green]{cls.name}[/green]")
                if cls.methods:
                    methods_node = class_node.add("[yellow]Methods[/yellow]")
                    for method in cls.methods[:5]:  # Show first 5
                        methods_node.add(f"{method.name}()")
        
        # Add functions
        if result.functions:
            functions_branch = tree.add("[cyan]Functions[/cyan]")
            for func in result.functions[:10]:  # Show first 10
                functions_branch.add(f"[green]{func.name}()[/green]")
        
        # Add namespaces
        if result.namespaces:
            namespaces_branch = tree.add("[cyan]Namespaces[/cyan]")
            for ns in result.namespaces:
                namespaces_branch.add(f"[blue]{ns.name}[/blue]")
        
        console.print(tree)

    def _display_multiple_results(self, results: List[AnalysisResult], format_type: str) -> None:
        """Display multiple analysis results."""
        if format_type == "json":
            data = [result.model_dump() for result in results]
            console.print(Syntax(
                json.dumps(data, indent=2, default=str),
                "json",
                theme="monokai"
            ))
        else:
            # Summary table
            summary_table = Table(title="Analysis Summary")
            summary_table.add_column("File", style="blue")
            summary_table.add_column("Classes", style="green")
            summary_table.add_column("Functions", style="cyan")
            summary_table.add_column("Errors", style="red")
            summary_table.add_column("Warnings", style="yellow")
            
            for result in results:
                stats = result.get_statistics()
                summary_table.add_row(
                    os.path.basename(result.file_path),
                    str(stats["total_classes"]),
                    str(stats["total_functions"]),
                    str(stats["error_count"]),
                    str(stats["warning_count"])
                )
            
            console.print(summary_table)

    def _display_project_summary(self, project_result: ProjectAnalysisResult) -> None:
        """Display project analysis summary."""
        stats = project_result.summary_statistics
        
        summary_table = Table(title="Project Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="green")
        
        for key, value in stats.items():
            summary_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(summary_table)

    def _display_project_results(self, project_result: ProjectAnalysisResult) -> None:
        """Display full project analysis results."""
        self._display_project_summary(project_result)
        console.print()
        self._display_multiple_results(project_result.analysis_results, "table")

    def _display_file_list(self, files: List[FileInfo]) -> None:
        """Display list of discovered files."""
        if not files:
            return
        
        table = Table(title="Discovered Files")
        table.add_column("File", style="blue")
        table.add_column("Type", style="green")
        table.add_column("Size", style="cyan")
        
        for file_info in files[:20]:  # Show first 20
            table.add_row(
                os.path.basename(file_info.file_path),
                file_info.file_type,
                f"{file_info.size:,} bytes"
            )
        
        console.print(table)
        
        if len(files) > 20:
            console.print(f"[dim]... and {len(files) - 20} more files[/dim]")

    def _display_cache_info(self, cache_info: Dict[str, Any]) -> None:
        """Display cache information."""
        if not cache_info["exists"]:
            console.print("[yellow]No cache found[/yellow]")
            return
        
        info_table = Table(title="Cache Information", show_header=False)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")
        
        for key, value in cache_info.items():
            if key != "exists":
                info_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(info_table)

    def _display_system_info(self) -> None:
        """Display system information."""
        info = SystemUtils.get_system_info()
        
        system_table = Table(title="System Information", show_header=False)
        system_table.add_column("Property", style="cyan")
        system_table.add_column("Value", style="green")
        
        for key, value in info.items():
            system_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(system_table)

    def _display_compiler_info(self) -> None:
        """Display compiler information."""
        compilers = SystemUtils.get_compiler_info()
        
        compiler_table = Table(title="Compiler Information")
        compiler_table.add_column("Compiler", style="blue")
        compiler_table.add_column("Available", style="green")
        compiler_table.add_column("Version", style="cyan")
        
        for name, info in compilers.items():
            status = "✓" if info["available"] else "✗"
            version = info.get("version_info", "N/A")[:50]
            compiler_table.add_row(name.upper(), status, version)
        
        console.print(compiler_table)

    def _display_libclang_info(self) -> None:
        """Display libclang information."""
        libclang_path = SystemUtils.find_libclang_library()
        
        info_table = Table(title="libclang Information", show_header=False)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")
        
        info_table.add_row("Library Found", "✓" if libclang_path else "✗")
        if libclang_path:
            info_table.add_row("Library Path", libclang_path)
        
        console.print(info_table)

    def _save_results(self, results: List[AnalysisResult], output_file: str) -> None:
        """Save analysis results to file."""
        try:
            data = [result.model_dump() for result in results]
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            console.print(f"[green]Results saved to: {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving results: {e}[/red]")

    def _save_project_results(self, project_result: ProjectAnalysisResult, output_file: str) -> None:
        """Save project analysis results to file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(project_result.model_dump(), f, indent=2, default=str)
            console.print(f"[green]Project results saved to: {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving project results: {e}[/red]")


def main() -> int:
    """Main entry point."""
    cli = CppAnalyzerCLI()
    return cli.main()


if __name__ == "__main__":
    sys.exit(main())