#!/bin/bash
# Test script to demonstrate debug flag functionality

echo "======================================"
echo "Testing workflow without --debug flag:"
echo "======================================"
echo ""

# Run a simple workflow without debug
python run.py workflow individual --task "Create a simple calculator function that adds two numbers" --step planning --no-orchestrator

echo ""
echo ""
echo "======================================"
echo "Testing workflow with --debug flag:"
echo "======================================"
echo ""

# Run the same workflow with debug
python run.py workflow individual --task "Create a simple calculator function that adds two numbers" --step planning --no-orchestrator --debug

echo ""
echo "======================================"
echo "Test complete!"
echo "======================================"