"""
File indexing system for C++ code analysis.

This module provides the CppIndexer class for discovering and managing
C++ source files in project directories with caching and filtering capabilities.
"""

import os
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Set, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a discovered C++ file."""
    file_path: str
    size: int
    modified_time: float
    file_type: str  # 'header' or 'source'
    extension: str
    content_hash: Optional[str] = None
    last_analyzed: Optional[str] = None


@dataclass
class IndexCache:
    """Cache information for file indexing."""
    version: str = "1.0"
    created: str = ""
    last_updated: str = ""
    files: Dict[str, FileInfo] = None

    def __post_init__(self):
        if self.files is None:
            self.files = {}
        if not self.created:
            self.created = datetime.now().isoformat()


class CppIndexer:
    """
    File indexer for C++ source code projects.
    
    This class discovers C++ files in directory structures, maintains
    a cache of file information, and provides filtering capabilities.
    """

    # Default C++ file extensions
    DEFAULT_EXTENSIONS = {
        'source': {'.cpp', '.cxx', '.cc', '.c++'},
        'header': {'.h', '.hpp', '.hxx', '.h++', '.hh'}
    }

    # Default exclusion patterns
    DEFAULT_EXCLUDE_PATTERNS = {
        # Directories
        '__pycache__', '.git', '.svn', '.hg', 'node_modules',
        'build', 'Build', 'BUILD', 'dist', 'out', 'Debug', 'Release',
        '.vs', '.vscode', 'CMakeFiles', '.cmake',
        # Files
        '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.dylib',
        '*.obj', '*.o', '*.lib', '*.a', '*.exe',
        # Backup files
        '*~', '*.bak', '*.tmp', '*.swp', '*.swo',
        # IDE files
        '*.vcxproj*', '*.sln', '*.suo', '*.user'
    }

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl_hours: int = 24
    ):
        """
        Initialize the C++ file indexer.
        
        Args:
            cache_dir: Directory to store cache files (default: .cpp_analyzer_cache)
            cache_enabled: Whether to use file caching
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.cwd() / '.cpp_analyzer_cache'
        
        if self.cache_enabled:
            self.cache_dir.mkdir(exist_ok=True)
        
        self.extensions = self.DEFAULT_EXTENSIONS.copy()
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        
        logger.info(f"Initialized CppIndexer with cache: {self.cache_enabled}")

    def discover_cpp_files(
        self,
        root_path: str,
        recursive: bool = True,
        include_headers: bool = True,
        include_sources: bool = True,
        additional_extensions: Optional[Set[str]] = None,
        exclude_patterns: Optional[Set[str]] = None
    ) -> List[FileInfo]:
        """
        Discover C++ files in the given directory.
        
        Args:
            root_path: Root directory to search
            recursive: Whether to search subdirectories
            include_headers: Whether to include header files
            include_sources: Whether to include source files
            additional_extensions: Additional file extensions to include
            exclude_patterns: Additional patterns to exclude
            
        Returns:
            List of FileInfo objects for discovered files
        """
        root_path = os.path.abspath(root_path)
        
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Path does not exist: {root_path}")
        
        if not os.path.isdir(root_path):
            # Single file
            if self._is_cpp_file(root_path, include_headers, include_sources, additional_extensions):
                return [self._create_file_info(root_path)]
            else:
                return []
        
        logger.info(f"Discovering C++ files in: {root_path}")
        
        # Load cache if enabled
        cache = self._load_cache(root_path) if self.cache_enabled else None
        
        # Build effective extensions
        effective_extensions = set()
        if include_headers:
            effective_extensions.update(self.extensions['header'])
        if include_sources:
            effective_extensions.update(self.extensions['source'])
        if additional_extensions:
            effective_extensions.update(additional_extensions)
        
        # Build effective exclude patterns
        effective_exclude = self.exclude_patterns.copy()
        if exclude_patterns:
            effective_exclude.update(exclude_patterns)
        
        # Discover files
        discovered_files = []
        total_files = 0
        cached_files = 0
        
        for file_path in self._walk_directory(root_path, recursive, effective_exclude):
            total_files += 1
            
            if not self._is_cpp_file(file_path, include_headers, include_sources, additional_extensions):
                continue
            
            # Check cache first
            file_info = None
            if cache and self._is_file_cached_and_valid(file_path, cache):
                file_info = cache.files[file_path]
                cached_files += 1
            else:
                file_info = self._create_file_info(file_path)
            
            if file_info:
                discovered_files.append(file_info)
        
        logger.info(f"Discovered {len(discovered_files)} C++ files "
                   f"(total files scanned: {total_files}, cached: {cached_files})")
        
        # Update cache
        if self.cache_enabled and discovered_files:
            self._update_cache(root_path, discovered_files)
        
        return discovered_files

    def get_project_files(
        self,
        root_path: str,
        include_tests: bool = True,
        include_examples: bool = True
    ) -> Dict[str, List[FileInfo]]:
        """
        Get organized project files by category.
        
        Args:
            root_path: Root project directory
            include_tests: Whether to include test files
            include_examples: Whether to include example files
            
        Returns:
            Dictionary with file categories (sources, headers, tests, examples)
        """
        all_files = self.discover_cpp_files(root_path)
        
        categorized = {
            'sources': [],
            'headers': [],
            'tests': [],
            'examples': []
        }
        
        for file_info in all_files:
            file_path_lower = file_info.file_path.lower()
            
            # Categorize by type first
            if file_info.file_type == 'header':
                category = 'headers'
            else:
                category = 'sources'
            
            # Check for special directories/patterns
            if any(pattern in file_path_lower for pattern in ['test', 'tests', 'testing']):
                if include_tests:
                    category = 'tests'
                else:
                    continue
            elif any(pattern in file_path_lower for pattern in ['example', 'examples', 'sample', 'demo']):
                if include_examples:
                    category = 'examples'
                else:
                    continue
            
            categorized[category].append(file_info)
        
        return categorized

    def filter_files(
        self,
        files: List[FileInfo],
        min_size: Optional[int] = None,  
        max_size: Optional[int] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None,
        name_patterns: Optional[List[str]] = None,
        exclude_name_patterns: Optional[List[str]] = None
    ) -> List[FileInfo]:
        """
        Filter files based on various criteria.
        
        Args:
            files: List of files to filter
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            modified_after: Only include files modified after this date
            modified_before: Only include files modified before this date
            name_patterns: Include files matching these patterns (glob-style)
            exclude_name_patterns: Exclude files matching these patterns
            
        Returns:
            Filtered list of FileInfo objects
        """
        import fnmatch
        
        filtered = []
        
        for file_info in files:
            # Size filters
            if min_size is not None and file_info.size < min_size:
                continue
            if max_size is not None and file_info.size > max_size:
                continue
            
            # Time filters
            file_mtime = datetime.fromtimestamp(file_info.modified_time)
            if modified_after and file_mtime <= modified_after:
                continue
            if modified_before and file_mtime >= modified_before:
                continue
            
            # Name pattern filters
            filename = os.path.basename(file_info.file_path)
            
            if name_patterns:
                if not any(fnmatch.fnmatch(filename, pattern) for pattern in name_patterns):
                    continue
            
            if exclude_name_patterns:
                if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_name_patterns):
                    continue
            
            filtered.append(file_info)
        
        return filtered

    def get_file_dependencies(self, file_path: str) -> List[str]:
        """
        Get basic file dependencies by scanning include directives.
        
        Note: This is a simple text-based scan, not a full preprocessor analysis.
        
        Args:
            file_path: Path to the C++ file
            
        Returns:
            List of included file names
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Look for include directives
                    if line.startswith('#include'):
                        # Extract include file name
                        if '"' in line:
                            # Local include: #include "file.h"
                            start = line.find('"') + 1
                            end = line.find('"', start)
                            if end > start:
                                dependencies.append(line[start:end])
                        elif '<' in line and '>' in line:
                            # System include: #include <file.h>
                            start = line.find('<') + 1
                            end = line.find('>', start)
                            if end > start:
                                dependencies.append(line[start:end])
        
        except Exception as e:
            logger.warning(f"Error reading dependencies from {file_path}: {e}")
        
        return dependencies

    def calculate_content_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash of file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        except Exception as e:
            logger.warning(f"Error calculating hash for {file_path}: {e}")
            return ""
        
        return hasher.hexdigest()

    def _walk_directory(
        self, 
        root_path: str, 
        recursive: bool, 
        exclude_patterns: Set[str]
    ) -> List[str]:
        """Walk directory and yield file paths."""
        import fnmatch
        
        files = []
        
        if recursive:
            for root, dirs, filenames in os.walk(root_path):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs 
                          if not any(fnmatch.fnmatch(d, pattern) 
                                   for pattern in exclude_patterns)]
                
                for filename in filenames:
                    if not any(fnmatch.fnmatch(filename, pattern) 
                             for pattern in exclude_patterns):
                        files.append(os.path.join(root, filename))
        else:
            try:
                for item in os.listdir(root_path):
                    item_path = os.path.join(root_path, item)
                    if (os.path.isfile(item_path) and
                        not any(fnmatch.fnmatch(item, pattern) 
                               for pattern in exclude_patterns)):
                        files.append(item_path)
            except PermissionError:
                logger.warning(f"Permission denied accessing: {root_path}")
        
        return files

    def _is_cpp_file(
        self, 
        file_path: str,
        include_headers: bool,
        include_sources: bool,
        additional_extensions: Optional[Set[str]]
    ) -> bool:
        """Check if file is a C++ file."""
        ext = Path(file_path).suffix.lower()
        
        valid_extensions = set()
        if include_headers:
            valid_extensions.update(self.extensions['header'])
        if include_sources:
            valid_extensions.update(self.extensions['source'])
        if additional_extensions:
            valid_extensions.update(additional_extensions)
        
        return ext in valid_extensions

    def _create_file_info(self, file_path: str) -> FileInfo:
        """Create FileInfo object for a file."""
        try:
            stat = os.stat(file_path)
            ext = Path(file_path).suffix.lower()
            
            # Determine file type
            if ext in self.extensions['header']:
                file_type = 'header'
            else:
                file_type = 'source'
            
            return FileInfo(
                file_path=file_path,
                size=stat.st_size,
                modified_time=stat.st_mtime,
                file_type=file_type,
                extension=ext
            )
        except Exception as e:
            logger.warning(f"Error creating FileInfo for {file_path}: {e}")
            return None

    def _get_cache_file_path(self, root_path: str) -> Path:
        """Get cache file path for a root directory."""
        # Create a safe filename from the root path
        safe_name = hashlib.md5(root_path.encode()).hexdigest()
        return self.cache_dir / f"index_{safe_name}.json"

    def _load_cache(self, root_path: str) -> Optional[IndexCache]:
        """Load cache for a root directory."""
        cache_file = self._get_cache_file_path(root_path)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert file info dictionaries back to FileInfo objects
            files = {}
            for path, file_data in data.get('files', {}).items():
                files[path] = FileInfo(**file_data)
            
            cache = IndexCache(
                version=data.get('version', '1.0'),
                created=data.get('created', ''),
                last_updated=data.get('last_updated', ''),
                files=files
            )
            
            # Check if cache is expired
            if cache.last_updated:
                last_updated = datetime.fromisoformat(cache.last_updated)
                if datetime.now() - last_updated > self.cache_ttl:
                    logger.info(f"Cache expired for {root_path}")
                    return None
            
            logger.debug(f"Loaded cache with {len(cache.files)} files")
            return cache
            
        except Exception as e:
            logger.warning(f"Error loading cache for {root_path}: {e}")
            return None

    def _update_cache(self, root_path: str, files: List[FileInfo]) -> None:
        """Update cache with discovered files."""
        try:
            # Load existing cache or create new one
            cache = self._load_cache(root_path) or IndexCache()
            
            # Update with new files
            for file_info in files:
                cache.files[file_info.file_path] = file_info
            
            cache.last_updated = datetime.now().isoformat()
            
            # Save cache
            cache_file = self._get_cache_file_path(root_path)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(cache), f, indent=2, default=str)
            
            logger.debug(f"Updated cache with {len(files)} files")
            
        except Exception as e:
            logger.warning(f"Error updating cache for {root_path}: {e}")

    def _is_file_cached_and_valid(self, file_path: str, cache: IndexCache) -> bool:
        """Check if file is in cache and still valid."""
        if file_path not in cache.files:
            return False
        
        try:
            cached_info = cache.files[file_path]
            current_stat = os.stat(file_path)
            
            # Check if file has been modified
            return (cached_info.modified_time == current_stat.st_mtime and
                    cached_info.size == current_stat.st_size)
        except (OSError, FileNotFoundError):
            # File no longer exists
            return False

    def clear_cache(self, root_path: Optional[str] = None) -> None:
        """
        Clear cache files.
        
        Args:
            root_path: Specific root path to clear cache for, or None for all
        """
        if root_path:
            # Clear specific cache
            cache_file = self._get_cache_file_path(root_path)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for {root_path}")
        else:
            # Clear all cache files
            if self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("index_*.json"):
                    cache_file.unlink()
                logger.info("Cleared all index caches")

    def get_cache_info(self, root_path: str) -> Dict[str, Any]:
        """Get information about cache for a root path."""
        cache = self._load_cache(root_path)
        
        if not cache:
            return {"exists": False}
        
        cache_file = self._get_cache_file_path(root_path)
        
        return {
            "exists": True,
            "version": cache.version,
            "created": cache.created,
            "last_updated": cache.last_updated,
            "file_count": len(cache.files),
            "cache_file_size": cache_file.stat().st_size if cache_file.exists() else 0,
            "is_expired": (datetime.now() - datetime.fromisoformat(cache.last_updated)) > self.cache_ttl
        }