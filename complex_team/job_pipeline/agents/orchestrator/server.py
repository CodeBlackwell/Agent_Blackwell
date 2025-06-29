#!/usr/bin/env python3
"""
Orchestrator Agent Server

Standalone server script for the Orchestrator Agent.
Run this to start the Orchestrator Agent on its configured port.
"""

import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.orchestrator.orchestrator_agent import server
from config.config import AGENT_PORTS

def main():
    """Start the Orchestrator Agent server."""
    server.run(port=AGENT_PORTS["orchestrator"])

if __name__ == "__main__":
    main()
