#!/usr/bin/env python3
"""
Debug script to understand what's happening with the incremental parser
"""
import sys
import os
import json
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.utils.feature_parser import FeatureParser

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Read the actual designer output from our test
# Note: This path may need to be updated based on the actual test run
results_path = os.path.join(os.path.dirname(__file__), "../outputs/incremental_calculator/results_20250705_161025.json")
if not os.path.exists(results_path):
    print(f"Warning: Results file not found at {results_path}")
    print("Please update the path to point to an actual test results file")
    sys.exit(1)

with open(results_path, "r") as f:
    data = json.load(f)

# Find the designer output in the results
designer_output = None
for result in data["results"]:
    if "designer" in str(result.get("agent", "")):
        output = result["output"]
        # The output is a string representation of a Message object
        # Extract the actual content
        import re
        content_match = re.search(r"content='([^']+)'", output, re.DOTALL)
        if content_match:
            designer_output = content_match.group(1)
            # Unescape the content
            designer_output = designer_output.replace('\\n', '\n').replace("\\'", "'").replace('\\\\', '\\')
            break

if designer_output:
    print("="*80)
    print("DESIGNER OUTPUT:")
    print("="*80)
    print(designer_output[:2000])  # First 2000 chars
    print("\n... [TRUNCATED] ...\n")
    
    # Check for IMPLEMENTATION PLAN
    if "IMPLEMENTATION PLAN" in designer_output:
        plan_start = designer_output.find("IMPLEMENTATION PLAN")
        print("\n" + "="*80)
        print("IMPLEMENTATION PLAN SECTION:")
        print("="*80)
        print(designer_output[plan_start:plan_start+2000])
    
    # Parse with FeatureParser
    print("\n" + "="*80)
    print("PARSING RESULTS:")
    print("="*80)
    
    parser = FeatureParser()
    features = parser.parse(designer_output)
    
    print(f"\nParsed {len(features)} features:")
    for i, feature in enumerate(features):
        print(f"\n{i+1}. {feature.id}: {feature.title}")
        print(f"   Description: {feature.description[:100]}...")
        print(f"   Files: {feature.files}")
        
else:
    print("Could not find designer output in the results file")