#!/usr/bin/env python3
"""Space Empires - Simple run script"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try GUI first, fall back to text mode
try:
    import tkinter as tk
    from space_empires.__main__ import main
    print("Starting Space Empires GUI...")
    main()
except ImportError:
    print("Tkinter not available, starting text mode...")
    from space_empires.text_runner import main as text_main
    text_main()
except Exception as e:
    print(f"GUI error: {e}")
    print("Falling back to text mode...")
    from space_empires.text_runner import main as text_main
    text_main()