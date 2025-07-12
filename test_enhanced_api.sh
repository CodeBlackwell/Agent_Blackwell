#!/bin/bash
# Test the enhanced workflow via API

echo "Testing Enhanced Full Workflow via API"
echo "======================================"
echo ""
echo "Make sure both services are running:"
echo "1. python orchestrator/orchestrator_agent.py"
echo "2. python api/orchestrator_api.py"
echo ""
read -p "Press Enter when both services are running..."

# Test with a simple request
curl -X POST http://localhost:8000/coding-team \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a Python function that converts temperature between Celsius and Fahrenheit",
    "workflow_type": "enhanced_full",
    "team_members": ["planner", "designer", "coder", "reviewer"]
  }' | python -m json.tool

echo ""
echo "Check the response for:"
echo "- execution_id"
echo "- team_outputs from each agent"
echo "- performance_metrics in metadata"
echo "- optimization_suggestions"