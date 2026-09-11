#!/usr/bin/env python3
"""Space Empires - Main entry point"""
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from space_empires.__main__ import main

if __name__ == "__main__":
    main()