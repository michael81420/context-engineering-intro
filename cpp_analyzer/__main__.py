"""
Main entry point for cpp_analyzer package.

This module allows running the C++ analyzer as a module:
    python -m cpp_analyzer [args...]
"""

from .cli import main

if __name__ == "__main__":
    exit(main())