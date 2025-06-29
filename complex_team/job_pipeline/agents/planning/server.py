#!/usr/bin/env python3
"""
Planning Agent Server

This script starts the Planning Agent server on port 8001.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.planning.planning_agent import server
from config.config import AGENT_PORTS

if __name__ == "__main__":
    port = AGENT_PORTS.get("planning", 8001)
    print(f"Starting Planning Agent server on port {port}...")
    server.run(port=port)
