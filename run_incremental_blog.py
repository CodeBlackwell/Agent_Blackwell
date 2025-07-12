#!/usr/bin/env python3
"""
Simple runner for the incremental blog demo with automatic orchestrator management.
"""

import os
import sys

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the demo
from examples.incremental_blog_demo import main

if __name__ == "__main__":
    main()