#!/usr/bin/env python3
"""Setup script for C++ Code Analyzer."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract package name (ignore version constraints for setup.py)
            package = line.split('>=')[0].split('==')[0].split('<=')[0]
            requirements.append(package)

setup(
    name="cpp-analyzer",
    version="1.0.0",
    author="Claude Code Assistant",
    author_email="noreply@anthropic.com",
    description="C++ Code Analysis Tool using libclang",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/cpp-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0", 
            "pytest-cov>=4.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
            "black>=23.0.0",
        ],
        "cli": [
            "click>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cpp-analyzer=cpp_analyzer.cli:main",
            "cppa=cpp_analyzer.cli:main",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "cpp_analyzer": ["py.typed"],
    },
    keywords=[
        "cpp", "c++", "static-analysis", "code-analysis", 
        "libclang", "ast", "parsing", "clang"
    ],
    project_urls={
        "Bug Reports": "https://github.com/example/cpp-analyzer/issues",
        "Source": "https://github.com/example/cpp-analyzer",
        "Documentation": "https://cpp-analyzer.readthedocs.io/",
    },
)