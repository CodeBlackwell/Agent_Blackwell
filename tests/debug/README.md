# Debug Scripts

This directory contains debugging utilities for troubleshooting workflow issues.

## Scripts

- `debug_incremental_parser.py` - Debug script for analyzing incremental workflow parsing issues
  - Reads test output JSON files to extract designer output
  - Shows how features are being parsed
  - Helps identify parsing problems

## Usage

These scripts are meant for debugging specific issues. They typically require:

1. A test results JSON file from a previous workflow run
2. Manual updates to file paths based on your test outputs

Example:
```bash
# Update the results path in the script first
python tests/debug/debug_incremental_parser.py
```