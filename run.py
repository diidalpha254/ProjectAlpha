#!/usr/bin/env python3
"""
Project Alpha Launcher
Entry point for running the application.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Run the application
if __name__ == "__main__":
    from app.main import main
    main()