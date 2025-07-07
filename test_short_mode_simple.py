#!/usr/bin/env python3
"""Simple test for short mode functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from workflows.agent_output_handler import RealTimeOutputHandler
import time

# Test minimal mode
print("Testing minimal mode output:")
handler = RealTimeOutputHandler(display_mode="minimal")

# Simulate agent execution
start = handler.on_agent_start("planner_agent", "Create a plan", 1)
time.sleep(0.5)
handler.on_agent_complete("planner_agent", "Create a plan", "Plan created", start, 1)

start = handler.on_agent_start("coder_agent", "Implement feature 1/3", 2)
time.sleep(0.3)
handler.on_agent_complete("coder_agent", "Implement feature 1/3", "Code implemented", start, 2)

start = handler.on_agent_start("coder_agent", "Implement feature 2/3", 3)
time.sleep(0.2)
handler.on_agent_complete("coder_agent", "Implement feature 2/3", "Error: undefined variable", start, 3, {"error": "Failed"})

print("\nMinimal mode test completed!")