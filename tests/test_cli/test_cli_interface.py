"""
Tests for CLI interface functionality.

This module contains tests for the command-line interface, including
argument parsing, command execution, and output formatting.
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from cpp_analyzer.cli import CppAnalyzerCLI, main
from cpp_analyzer.models import AnalysisResult, ClassInfo, FunctionInfo, ElementKind, SourceLocation


@pytest.fixture
def cli():
    """Create CLI instance for testing."""
    return CppAnalyzerCLI()


@pytest.fixture
def sample_analysis_result():
    """Create sample analysis result for testing."""
    return AnalysisResult(
        file_path="/test/sample.cpp",
        analysis_metadata={
            "cpp_standard": "c++17",
            "analysis_time": "2024-01-01T12:00:00",
            "total_classes": 1,
            "total_functions": 2
        },
        classes=[
            ClassInfo(
                name="TestClass",
                kind=ElementKind.CLASS,
                location=SourceLocation(file_path="/test/sample.cpp", line=10, column=1)
            )
        ],
        functions=[
            FunctionInfo(
                name="testFunction",
                kind=ElementKind.FUNCTION,
                location=SourceLocation(file_path="/test/sample.cpp", line=20, column=1),
                return_type="void"
            )
        ]
    )


@pytest.fixture
def temp_cpp_file():
    """Create temporary C++ file for testing."""
    content = '''
class TestClass {
public:
    void method() {}
};

void function() {}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    yield temp_file
    
    try:
        os.unlink(temp_file)
    except OSError:
        pass


class TestCLIArgumentParsing:
    """Test command-line argument parsing."""
    
    def test_default_arguments(self, cli):
        """Test parsing with minimal arguments."""
        with patch('sys.argv', ['cpp-analyzer', 'test.cpp']):
            args = cli._parse_arguments()
            assert args.command == "analyze"
            assert args.path == "test.cpp"
            assert args.std == "c++17"
            assert args.verbose is False
            assert args.quiet is False
    
    def test_analyze_command_arguments(self, cli):
        """Test analyze command argument parsing."""
        test_args = [
            'cpp-analyzer', 'analyze', 'src/test.cpp',
            '--output', 'results.json',
            '--recursive',
            '--format', 'json',
            '--std', 'c++20'
        ]
        
        with patch('sys.argv', test_args):
            args = cli._parse_arguments()
            assert args.command == "analyze"
            assert args.path == "src/test.cpp"
            assert args.output == "results.json"
            assert args.recursive is True
            assert args.format == "json"
            assert args.std == "c++20"
    
    def test_project_command_arguments(self, cli):
        """Test project command argument parsing."""
        test_args = [
            'cpp-analyzer', 'project', '/path/to/project',
            '--summary',
            '--exclude-tests',
            '--output', 'project.json'
        ]
        
        with patch('sys.argv', test_args):
            args = cli._parse_arguments()
            assert args.command == "project"
            assert args.path == "/path/to/project"
            assert args.summary is True
            assert args.exclude_tests is True
            assert args.output == "project.json"
    
    def test_index_command_arguments(self, cli):
        """Test index command argument parsing."""
        test_args = [
            'cpp-analyzer', 'index', '/path/to/code',
            '--clear-cache',
            '--cache-info'
        ]
        
        with patch('sys.argv', test_args):
            args = cli._parse_arguments()
            assert args.command == "index"
            assert args.path == "/path/to/code"
            assert args.clear_cache is True
            assert args.cache_info is True
    
    def test_info_command_arguments(self, cli):
        """Test info command argument parsing."""
        test_args = [
            'cpp-analyzer', 'info',
            '--system',
            '--compilers',
            '--libclang'
        ]
        
        with patch('sys.argv', test_args):
            args = cli._parse_arguments()
            assert args.command == "info"
            assert args.system is True
            assert args.compilers is True
            assert args.libclang is True
    
    def test_global_options(self, cli):
        """Test global option parsing."""
        test_args = [
            'cpp-analyzer', 
            '--verbose',
            '-I', '/usr/include',
            '-I', '/usr/local/include',
            '--define', 'DEBUG=1',
            '--define', 'VERSION=2',
            'analyze', 'test.cpp'
        ]
        
        with patch('sys.argv', test_args):
            args = cli._parse_arguments()
            assert args.verbose is True
            assert args.include_paths == ['/usr/include', '/usr/local/include']
            assert args.defines == ['DEBUG=1', 'VERSION=2']


class TestCLICommandExecution:
    """Test CLI command execution."""
    
    @patch('cpp_analyzer.cli.CppAnalyzer')
    @patch('cpp_analyzer.cli.CppIndexer')
    def test_analyze_single_file(self, mock_indexer, mock_analyzer, cli, sample_analysis_result):
        """Test analyzing a single file."""
        # Setup mocks
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_file.return_value = sample_analysis_result
        
        # Test arguments
        args = Mock()
        args.command = "analyze"
        args.path = "/test/sample.cpp"
        args.output = None
        args.format = "table"
        args.include_paths = []
        args.defines = []
        
        # Mock file existence
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('cpp_analyzer.cli.console') as mock_console:
            
            result = cli._cmd_analyze(args)
            
            assert result == 0
            mock_analyzer_instance.analyze_file.assert_called_once()
            mock_console.print.assert_called()
    
    @patch('cpp_analyzer.cli.CppAnalyzer')
    @patch('cpp_analyzer.cli.CppIndexer')
    def test_analyze_directory(self, mock_indexer, mock_analyzer, cli, sample_analysis_result):
        """Test analyzing a directory."""
        # Setup mocks
        mock_indexer_instance = Mock()
        mock_indexer.return_value = mock_indexer_instance
        mock_indexer_instance.discover_cpp_files.return_value = [
            Mock(file_path="/test/file1.cpp"),
            Mock(file_path="/test/file2.cpp")
        ]
        
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze_file.return_value = sample_analysis_result
        
        args = Mock()
        args.command = "analyze"
        args.path = "/test/directory"
        args.output = None
        args.format = "table"
        args.recursive = True
        args.include_headers = True
        args.include_sources = True
        args.include_paths = []
        args.defines = []
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=False), \
             patch('cpp_analyzer.cli.console') as mock_console:
            
            result = cli._cmd_analyze(args)
            
            assert result == 0
            assert mock_analyzer_instance.analyze_file.call_count == 2
    
    def test_analyze_nonexistent_path(self, cli):
        """Test analyzing non-existent path."""
        args = Mock()
        args.command = "analyze"
        args.path = "/nonexistent/path"
        
        with patch('cpp_analyzer.cli.console') as mock_console:
            result = cli._cmd_analyze(args)
            
            assert result == 1
            mock_console.print.assert_called_with(
                f"[red]Path does not exist: {args.path}[/red]"
            )
    
    @patch('cpp_analyzer.cli.CppIndexer')
    def test_project_command(self, mock_indexer, cli):
        """Test project analysis command."""
        mock_indexer_instance = Mock()
        mock_indexer.return_value = mock_indexer_instance
        mock_indexer_instance.get_project_files.return_value = {
            'sources': [Mock(file_path="/test/src.cpp")],
            'headers': [Mock(file_path="/test/header.h")],
            'tests': [],
            'examples': []
        }
        
        args = Mock()
        args.command = "project"
        args.path = "/test/project"
        args.summary = True
        args.exclude_tests = False
        args.exclude_examples = False
        args.output = None
        
        with patch('os.path.isdir', return_value=True), \
             patch('cpp_analyzer.cli.console') as mock_console, \
             patch.object(cli, '_analyze_single_file', return_value=sample_analysis_result):
            
            result = cli._cmd_project(args)
            
            # Should complete without error
            assert result == 0
            mock_console.print.assert_called()
    
    @patch('cpp_analyzer.cli.CppIndexer')
    def test_index_command(self, mock_indexer, cli):
        """Test index command."""
        mock_indexer_instance = Mock()
        mock_indexer.return_value = mock_indexer_instance
        mock_indexer_instance.discover_cpp_files.return_value = [
            Mock(file_path="/test/file1.cpp", file_type="source", size=1024),
            Mock(file_path="/test/file2.h", file_type="header", size=512)
        ]
        
        args = Mock()
        args.command = "index"
        args.path = "/test/directory"
        args.clear_cache = False
        args.cache_info = False
        
        with patch('cpp_analyzer.cli.console') as mock_console:
            result = cli._cmd_index(args)
            
            assert result == 0
            mock_indexer_instance.discover_cpp_files.assert_called_once()
    
    def test_info_command(self, cli):
        """Test info command."""
        args = Mock()
        args.command = "info"
        args.system = True
        args.compilers = False
        args.libclang = False
        
        with patch('cpp_analyzer.cli.console') as mock_console, \
             patch.object(cli, '_display_system_info') as mock_display:
            
            result = cli._cmd_info(args)
            
            assert result == 0
            mock_display.assert_called_once()


class TestCLIOutputFormatting:
    """Test CLI output formatting."""
    
    def test_display_result_table(self, cli, sample_analysis_result):
        """Test table format display."""
        with patch('cpp_analyzer.cli.console') as mock_console:
            cli._display_result_table(sample_analysis_result)
            
            # Should call console.print multiple times for different sections
            assert mock_console.print.call_count >= 2
    
    def test_display_result_tree(self, cli, sample_analysis_result):
        """Test tree format display."""
        with patch('cpp_analyzer.cli.console') as mock_console:
            cli._display_result_tree(sample_analysis_result)
            
            mock_console.print.assert_called_once()
    
    def test_display_result_json(self, cli, sample_analysis_result):
        """Test JSON format display."""
        with patch('cpp_analyzer.cli.console') as mock_console:
            cli._display_analysis_result(sample_analysis_result, "json")
            
            mock_console.print.assert_called_once()
            # Verify it's trying to display JSON syntax
            call_args = mock_console.print.call_args[0][0]
            assert hasattr(call_args, 'lexer_name') or 'json' in str(call_args).lower()
    
    def test_save_results_to_file(self, cli, sample_analysis_result):
        """Test saving results to JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            with patch('cpp_analyzer.cli.console') as mock_console:
                cli._save_results([sample_analysis_result], output_file)
                
                # Should print success message
                mock_console.print.assert_called_with(
                    f"[green]Results saved to: {output_file}[/green]"
                )
                
                # Verify file was created and contains valid JSON
                assert os.path.exists(output_file)
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    assert isinstance(data, list)
                    assert len(data) == 1
        
        finally:
            try:
                os.unlink(output_file)
            except OSError:
                pass


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_main_function_success(self):
        """Test main function with successful execution."""
        test_args = ['cpp-analyzer', 'info', '--system']
        
        with patch('sys.argv', test_args), \
             patch('cpp_analyzer.cli.CppAnalyzerCLI.main', return_value=0) as mock_main:
            
            result = main()
            assert result == 0
            mock_main.assert_called_once()
    
    def test_main_function_error(self):
        """Test main function with error."""
        test_args = ['cpp-analyzer', 'analyze', '/nonexistent']
        
        with patch('sys.argv', test_args), \
             patch('cpp_analyzer.cli.CppAnalyzerCLI.main', return_value=1) as mock_main:
            
            result = main()
            assert result == 1
    
    def test_keyboard_interrupt_handling(self, cli):
        """Test handling of keyboard interrupt."""
        with patch.object(cli, '_parse_arguments', side_effect=KeyboardInterrupt), \
             patch('cpp_analyzer.cli.console') as mock_console:
            
            result = cli.main()
            
            assert result == 1
            mock_console.print.assert_called_with(
                "\n[yellow]Operation cancelled by user[/yellow]"
            )
    
    def test_exception_handling(self, cli):
        """Test general exception handling."""
        with patch.object(cli, '_parse_arguments', side_effect=Exception("Test error")), \
             patch('cpp_analyzer.cli.console') as mock_console:
            
            result = cli.main()
            
            assert result == 1
            mock_console.print.assert_called_with("[red]Error: Test error[/red]")
    
    @patch('cpp_analyzer.cli.CppAnalyzer')
    @patch('cpp_analyzer.cli.CppIndexer')
    def test_end_to_end_analysis(self, mock_indexer, mock_analyzer, cli, temp_cpp_file):
        """End-to-end test of file analysis."""
        # Setup mocks to avoid actual libclang dependency
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        sample_result = AnalysisResult(
            file_path=temp_cpp_file,
            analysis_metadata={"cpp_standard": "c++17"}
        )
        mock_analyzer_instance.analyze_file.return_value = sample_result
        
        test_args = ['cpp-analyzer', 'analyze', temp_cpp_file, '--format', 'json']
        
        with patch('sys.argv', test_args), \
             patch('cpp_analyzer.cli.console') as mock_console:
            
            result = cli.main()
            
            assert result == 0
            mock_analyzer_instance.analyze_file.assert_called_once()


class TestCLIUtilityMethods:
    """Test CLI utility methods."""
    
    def test_initialize_components(self, cli):
        """Test component initialization."""
        args = Mock()
        args.std = "c++20"
        args.libclang_path = None
        
        with patch('cpp_analyzer.cli.CppAnalyzer') as mock_analyzer, \
             patch('cpp_analyzer.cli.CppIndexer') as mock_indexer:
            
            cli._initialize_components(args)
            
            mock_analyzer.assert_called_once_with(
                cpp_standard="c++20",
                library_path=None
            )
            mock_indexer.assert_called_once()
    
    def test_unknown_command_handling(self, cli):
        """Test handling of unknown commands."""
        args = Mock()
        args.command = "unknown_command"
        
        with patch('cpp_analyzer.cli.console') as mock_console:
            result = cli._execute_command(args)
            
            assert result == 1
            mock_console.print.assert_called_with(
                "[red]Unknown command: unknown_command[/red]"
            )