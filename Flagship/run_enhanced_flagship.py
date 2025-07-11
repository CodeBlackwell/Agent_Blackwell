#!/usr/bin/env python3
"""Run the enhanced Flagship orchestrator with proper imports"""

import sys
import os
from pathlib import Path

# Set up Python path before any imports
flagship_dir = Path(__file__).parent
sys.path.insert(0, str(flagship_dir))

# Now we can safely run the server
if __name__ == "__main__":
    # Import and run the server
    if "--streaming" in sys.argv:
        from flagship_server_streaming import main
    else:
        from flagship_server_simple import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8100)