#!/usr/bin/env python
"""
Entry point wrapper for console-app command.
This ensures the src module is found correctly.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import app

if __name__ == "__main__":
    app()

