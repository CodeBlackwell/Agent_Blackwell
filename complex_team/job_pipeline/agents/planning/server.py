#!/usr/bin/env python3
"""
Planning Agent Server

Standalone server script for the Planning Agent.
Run this to start the Planning Agent on its configured port.
"""

import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import AGENT_PORTS

def main():
    """Start the Planning Agent server."""
    # Import the server from the agent module
    from agents.planning.planning_agent import server
    
    print(f"Starting Planning Agent on port {AGENT_PORTS['planner']}...")
    server.run(port=AGENT_PORTS["planner"])

if __name__ == "__main__":
    main()
