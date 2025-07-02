"""
Enhanced Workflow Visualizer

This script generates detailed visualizations of the data flow between agents in the workflow system,
including comprehensive schema information, data transformations, and directional arrows.
"""

import os
import sys
from pathlib import Path
import inspect
from typing import Dict, List, Tuple, Set, Optional, Any
import importlib
import json
import re
import ast

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Visualization libraries
try:
    import graphviz
except ImportError:
    print("Graphviz not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "graphviz"])
    import graphviz

from orchestrator.orchestrator_agent import (
    TeamMember, WorkflowStep, CodingTeamInput, TeamMemberResult,
    CodingTeamResult, CodingTeamOutput
)

# Import workflow modules
from workflows.tdd.tdd_workflow import run_tdd_workflow
from workflows.full.full_workflow import run_full_workflow
from workflows.individual.individual_workflow import run_individual_workflow

# Enhanced schema information extraction
def extract_schema_info(obj_type, include_types=True) -> Dict:
    """Extract detailed schema information from a type annotation."""
    schema = {}
    
    if hasattr(obj_type, "__annotations__"):
        for field_name, field_type in obj_type.__annotations__.items():
            # Extract the field type name
            if hasattr(field_type, "__name__"):
                type_name = field_type.__name__
            elif hasattr(field_type, "_name"):
                type_name = field_type._name_
            else:
                type_name = str(field_type)
                
            # Clean up type annotations like List[str] to be more readable
            if "typing." in type_name:
                type_name = str(field_type).replace("typing.", "")
            
            if include_types:
                schema[field_name] = type_name
            else:
                schema[field_name] = ""
            
    # Add docstring information if available
    if obj_type.__doc__:
        schema["__doc__"] = obj_type.__doc__.strip()
            
    return schema

# Extract actual data transformations from code
def extract_data_transformations(func_source: str) -> List[Dict[str, Any]]:
    """Extract data transformation details from function source code."""
    transformations = []
    
    # Look for assignment patterns and data transformations
    assignment_pattern = re.compile(r'(\w+)\s*=\s*([^#\n]+)')
    matches = assignment_pattern.findall(func_source)
    
    for var_name, expr in matches:
        if 'results' in expr or 'input' in expr:
            transformations.append({
                'target': var_name,
                'source': expr.strip(),
                'type': 'assignment'
            })
    
    return transformations

# Advanced agent data flow analyzer
def analyze_workflow_data_flow(workflow_function) -> List[Tuple[str, str, Dict, List[Dict], Optional[str]]]:
    """
    Analyze a workflow function to determine the data flow between agents.
    Returns a list of (source, target, data_schema, transformations, flow_type) tuples.
    flow_type can be: None (regular flow), 'review' (review feedback), 'approval' (approval path), or 'feedback' (revision needed).
    """
    flows = []
    source = "input"
    target = None
    data_schema = {}
    transformations = []
    
    # Get the source code
    source_code = inspect.getsource(workflow_function)
    
    # Extract transformations
    all_transformations = extract_data_transformations(source_code)
    
    # Split into lines for step-by-step analysis
    source_lines = source_code.split('\n')
    
    # Track agents and their outputs for review flow detection
    agent_outputs = {}  # agent_name -> output_variable
    review_flows = {}   # output_variable -> (source_agent, review_context)
    
    # First pass: Find all agent calls and their outputs
    for i, line in enumerate(source_lines):
        if "run_team_member" in line and "await" in line:
            # Extract agent name and result variable
            agent_match = re.search(r'run_team_member\(["\']([^"\']+)["\']', line)
            result_match = re.search(r'(\w+)\s*=\s*await\s+run_team_member', line)
            
            if agent_match and result_match:
                agent_name = agent_match.group(1)
                result_var = result_match.group(1)
                agent_outputs[result_var] = agent_name
                
                # Look for output extraction
                for j in range(i+1, min(len(source_lines), i+10)):
                    output_line = source_lines[j]
                    if f"{result_var}[0]" in output_line or f"str({result_var}" in output_line:
                        output_match = re.search(rf'(\w+)\s*=\s*str\({result_var}', output_line)
                        if output_match:
                            output_var = output_match.group(1)
                            agent_outputs[output_var] = agent_name
                        break
    
    # Second pass: Find review_output calls and approval/feedback flows
    for i, line in enumerate(source_lines):
        # Detect review_output calls
        if "review_output(" in line:
            # Extract what's being reviewed
            review_match = re.search(r'review_output\(([^,]+),\s*["\']([^"\']+)["\']', line)
            if review_match:
                reviewed_var = review_match.group(1).strip()
                stage = review_match.group(2)
                
                # Find the source agent for this output
                source_agent = agent_outputs.get(reviewed_var, "unknown")
                if source_agent != "unknown":
                    # Add review flow: source_agent -> reviewer
                    flows.append((source_agent, "reviewer_agent", 
                                {"stage": stage, "output": reviewed_var}, 
                                [], "review"))
                    
                    # Look for approval/feedback handling after this review
                    for j in range(i+1, min(len(source_lines), i+20)):
                        approval_line = source_lines[j]
                        
                        # Look for approval handling
                        if "if approved:" in approval_line:
                            # Find what happens when approved
                            for k in range(j+1, min(len(source_lines), j+15)):
                                next_line = source_lines[k]
                                if "results.append" in next_line:
                                    # This indicates approval - workflow continues
                                    flows.append(("reviewer_agent", "workflow_continuation",
                                                {"decision": "approved", "stage": stage},
                                                [], "approval"))
                                    break
                                elif "run_team_member" in next_line:
                                    # Direct call to next agent after approval
                                    next_agent_match = re.search(r'run_team_member\(["\']([^"\']+)["\']', next_line)
                                    if next_agent_match:
                                        next_agent = next_agent_match.group(1)
                                        flows.append(("reviewer_agent", next_agent,
                                                    {"decision": "approved", "stage": stage},
                                                    [], "approval"))
                                    break
                        
                        # Look for feedback handling (else block or revision logic)
                        elif ("else:" in approval_line or "need revision" in approval_line.lower() or 
                              "feedback" in approval_line):
                            # Find feedback flow back to original agent
                            for k in range(j+1, min(len(source_lines), j+15)):
                                feedback_line = source_lines[k]
                                if f"{reviewed_var.split('_')[0]}_input" in feedback_line:
                                    # Feedback being added to input for retry
                                    flows.append(("reviewer_agent", source_agent,
                                                {"decision": "revision_needed", "stage": stage},
                                                [], "feedback"))
                                    break
                            break
    
    # Third pass: Find retry loops and test execution flows
    for i, line in enumerate(source_lines):
        # Detect test execution retry loops
        if "while not all_tests_passed" in line or "retry_state" in line:
            # Look for test execution and feedback patterns
            for j in range(i, min(len(source_lines), i+50)):
                retry_line = source_lines[j]
                
                # Test execution
                if "execute_tests(" in retry_line:
                    flows.append(("coder_agent", "test_execution",
                                {"type": "test_validation"}, [], "validation"))
                    flows.append(("test_execution", "coder_agent",
                                {"type": "test_results"}, [], "feedback"))
                
                # Reviewer feedback on test failures
                elif "run_team_member" in retry_line and "reviewer_agent" in retry_line and "test failures" in retry_line:
                    flows.append(("test_execution", "reviewer_agent",
                                {"type": "test_failure_analysis"}, [], "review"))
                    flows.append(("reviewer_agent", "coder_agent",
                                {"type": "test_failure_feedback"}, [], "feedback"))
    
    # Fourth pass: Find regular sequential flows between agents
    agent_sequence = []
    for i, line in enumerate(source_lines):
        if "run_team_member" in line and "await" in line:
            agent_match = re.search(r'run_team_member\(["\']([^"\']+)["\']', line)
            if agent_match:
                agent_name = agent_match.group(1)
                if agent_name != "reviewer_agent":  # Skip reviewer calls (handled above)
                    agent_sequence.append(agent_name)
    
    # Add sequential flows between main agents
    for i in range(len(agent_sequence) - 1):
        source_agent = agent_sequence[i]
        target_agent = agent_sequence[i + 1]
        
        # Check if this flow isn't already covered by review flows
        existing_flow = any(flow[0] == source_agent and flow[1] == target_agent 
                          for flow in flows)
        if not existing_flow:
            flows.append((source_agent, target_agent, 
                        {"type": "sequential"}, [], None))
    
    # Add input flow to first agent
    if agent_sequence:
        flows.insert(0, ("input", agent_sequence[0], 
                        {"type": "initial_input"}, [], None))
    
    return flows

# Enhanced graph generation
def generate_workflow_graph(workflow_name: str, data_flows: List[Tuple[str, str, Dict, List[Dict], Optional[str]]]) -> graphviz.Digraph:
    """Generate a detailed directed graph visualizing the workflow data flow."""
    dot = graphviz.Digraph(comment=f'{workflow_name} Data Flow')
    dot.attr(rankdir='TB', size='12,16')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    dot.attr('edge', fontname='Arial', fontsize='10')
    
    # Define colors and styles for different flow types
    flow_styles = {
        None: {'color': 'blue', 'style': 'solid', 'penwidth': '2'},
        'review': {'color': 'red', 'style': 'dashed', 'penwidth': '2'},
        'feedback': {'color': '#FF6600', 'style': 'dotted', 'penwidth': '2'},
        'approval': {'color': 'green', 'style': 'bold', 'penwidth': '3'},
        'validation': {'color': 'purple', 'style': 'dashed', 'penwidth': '1.5'}
    }
    
    # Define node colors for different agent types
    node_colors = {
        'input': '#E6F3FF',
        'planner_agent': '#FFE6CC',
        'designer_agent': '#E6FFE6', 
        'test_writer_agent': '#FFCCFF',
        'coder_agent': '#CCFFFF',
        'reviewer_agent': '#FFCCCC',
        'test_execution': '#F0E6FF',
        'workflow_continuation': '#E6E6E6'
    }
    
    # Collect all unique nodes
    nodes = set()
    for source, target, _, _, _ in data_flows:
        nodes.add(source)
        nodes.add(target)
    
    # Add nodes with appropriate styling
    for node in nodes:
        color = node_colors.get(node, '#F0F0F0')
        
        # Special styling for different node types
        if node == 'input':
            dot.node(node, 'Input\n(Requirements)', fillcolor=color, shape='ellipse')
        elif node == 'test_execution':
            dot.node(node, 'Test\nExecution', fillcolor=color, shape='diamond')
        elif node == 'workflow_continuation':
            dot.node(node, 'Continue\nWorkflow', fillcolor=color, shape='ellipse')
        elif '_agent' in node:
            # Clean up agent names for display
            display_name = node.replace('_agent', '').replace('_', ' ').title()
            dot.node(node, display_name, fillcolor=color)
        else:
            dot.node(node, node.replace('_', ' ').title(), fillcolor=color)
    
    # Add edges with flow-specific styling
    edge_counts = {}  # Track multiple edges between same nodes
    
    for source, target, data_schema, transformations, flow_type in data_flows:
        # Create unique edge identifier
        edge_key = f"{source}->{target}"
        edge_counts[edge_key] = edge_counts.get(edge_key, 0) + 1
        
        # Get style for this flow type
        style = flow_styles.get(flow_type, flow_styles[None])
        
        # Create edge label based on flow type and data
        label_parts = []
        
        if flow_type == 'review':
            stage = data_schema.get('stage', 'output')
            label_parts.append(f"Review {stage}")
        elif flow_type == 'feedback':
            decision = data_schema.get('decision', 'revision needed')
            label_parts.append(f"Feedback: {decision}")
        elif flow_type == 'approval':
            decision = data_schema.get('decision', 'approved')
            stage = data_schema.get('stage', '')
            label_parts.append(f"Approved: {stage}")
        elif flow_type == 'validation':
            test_type = data_schema.get('type', 'test')
            label_parts.append(f"Validate: {test_type}")
        else:
            # Regular flow - show data type
            if 'type' in data_schema:
                label_parts.append(data_schema['type'])
            elif 'stage' in data_schema:
                label_parts.append(data_schema['stage'])
        
        # Add transformation info if available
        if transformations:
            transform_info = f"({len(transformations)} transforms)"
            label_parts.append(transform_info)
        
        # Create final label
        edge_label = '\\n'.join(label_parts) if label_parts else ''
        
        # Handle multiple edges between same nodes
        if edge_counts[edge_key] > 1:
            edge_label += f" ({edge_counts[edge_key]})"
        
        # Add the edge with appropriate styling
        edge_attrs = {
            'label': edge_label,
            'color': style['color'],
            'style': style['style'],
            'penwidth': style['penwidth']
        }
        
        # Add arrowhead styling for different flow types
        if flow_type == 'review':
            edge_attrs['arrowhead'] = 'diamond'
        elif flow_type == 'feedback':
            edge_attrs['arrowhead'] = 'curve'
        elif flow_type == 'approval':
            edge_attrs['arrowhead'] = 'normal'
            edge_attrs['arrowsize'] = '1.5'
        elif flow_type == 'validation':
            edge_attrs['arrowhead'] = 'dot'
        
        dot.edge(source, target, **edge_attrs)
    
    # Add a comprehensive legend
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='Flow Types Legend', fontsize='14', style='filled', fillcolor='#F5F5F5')
        
        # Create legend nodes
        legend.node('legend_regular', 'Regular Flow', shape='plaintext', fontcolor='blue')
        legend.node('legend_review', 'Review Flow', shape='plaintext', fontcolor='red')
        legend.node('legend_feedback', 'Feedback Loop', shape='plaintext', fontcolor='#FF6600')
        legend.node('legend_approval', 'Approval Path', shape='plaintext', fontcolor='green')
        legend.node('legend_validation', 'Test Validation', shape='plaintext', fontcolor='purple')
        
        # Add legend edges showing the different styles
        legend.edge('legend_regular', 'legend_review', 
                   style='solid', color='blue', penwidth='2', label='sequential')
        legend.edge('legend_review', 'legend_feedback', 
                   style='dashed', color='red', penwidth='2', label='review', arrowhead='diamond')
        legend.edge('legend_feedback', 'legend_approval', 
                   style='dotted', color='#FF6600', penwidth='2', label='feedback', arrowhead='curve')
        legend.edge('legend_approval', 'legend_validation', 
                   style='bold', color='green', penwidth='3', label='approval', arrowhead='normal', arrowsize='1.5')
        legend.edge('legend_validation', 'legend_regular', 
                   style='dashed', color='purple', penwidth='1.5', label='validation', arrowhead='dot')
        
        # Position legend nodes
        legend.attr(rank='same')
    
    # Save the graph
    output_dir = Path(__file__).parent.parent / "docs" / "workflow_visualizations"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    filename = f"{workflow_name.lower().replace(' ', '_')}_enhanced_flow"
    dot.save(str(output_dir / f"{filename}.dot"))
    
    try:
        dot.render(str(output_dir / filename), format='pdf', cleanup=True)
        dot.render(str(output_dir / filename), format='png', cleanup=True, 
                  renderer='cairo', formatter='cairo')
        print(f"Enhanced {workflow_name} visualization saved to {output_dir}/{filename}")
    except Exception as e:
        print(f"Warning: Could not render {workflow_name} graph with enhanced settings: {e}")
        try:
            # Fall back to standard rendering
            dot.render(str(output_dir / filename), format='pdf', cleanup=True)
            dot.render(str(output_dir / filename), format='png', cleanup=True)
            print(f"{workflow_name} visualization saved to {output_dir}/{filename}")
        except Exception as e2:
            print(f"Warning: Could not render {workflow_name} graph: {e2}")
    
    return dot

def visualize_all_workflows():
    """Generate enhanced visualizations for all workflows."""
    output_dir = project_root / "docs" / "workflow_visualizations"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Mapping of workflow functions to their names and descriptions
    workflows = {
        "TDD Workflow": {
            "func": run_tdd_workflow,
            "desc": "Test-Driven Development workflow (planner → designer → test_writer → coder → reviewer)"
        },
        "Full Workflow": {
            "func": run_full_workflow,
            "desc": "Full development workflow (planner → designer → coder → reviewer)"
        },
        "Individual Workflow": {
            "func": run_individual_workflow,
            "desc": "Individual workflow step execution (single agent)"
        }
    }
    
    print(f"Generating enhanced workflow visualizations in {output_dir}...")
    
    # Create documentation content
    docs = ["# Workflow Data Flow Documentation\n\n"]
    docs.append("This document provides detailed information about data flow between agents in different workflows.\n\n")
    
    for name, info in workflows.items():
        print(f"Analyzing {name}...")
        flows = analyze_workflow_data_flow(info["func"])
        
        # Filter out duplicates (can happen with review analysis)
        unique_flows = []
        for flow in flows:
            if flow not in unique_flows:
                unique_flows.append(flow)
        flows = unique_flows
        
        print(f"Generating enhanced graph for {name}...")
        graph = generate_workflow_graph(name, flows)
        
        # Save as both DOT file and rendered PDF/PNG with better resolution
        filename = name.lower().replace(" ", "_")
        dot_path = output_dir / f"{filename}.dot"
        pdf_path = output_dir / f"{filename}.pdf"
        png_path = output_dir / f"{filename}.png"
        
        graph.save(str(dot_path))
        try:
            # Render to PDF with higher quality
            graph.render(str(output_dir / filename), format='pdf', cleanup=True)
            print(f"PDF saved to {pdf_path}")
            
            # Render to PNG with higher quality
            graph.render(str(output_dir / filename), format='png', cleanup=True)
            print(f"High-resolution PNG saved to {png_path}")
        except Exception as e:
            print(f"Warning: Could not render graph to PDF/PNG: {e}")
            try:
                # Fall back to standard rendering
                graph.render(str(output_dir / filename), format='pdf', cleanup=True)
                graph.render(str(output_dir / filename), format='png', cleanup=True)
                print("Fell back to standard rendering")
            except Exception as e2:
                print(f"Warning: Could not render graph: {e2}")
                print("This often happens if Graphviz is not properly installed.")
                print("You can still use the DOT file with an online Graphviz viewer.")
        
        print(f"DOT file saved to {dot_path}")
        
        # Generate a detailed JSON representation of the flows
        json_path = output_dir / f"{filename}_flows.json"
        with open(json_path, 'w') as f:
            # Convert schema and transformations to strings to make them JSON serializable
            serializable_flows = [
                {
                    "source": source, 
                    "target": target,
                    "schema": {k: str(v) for k, v in schema.items()},
                    "transformations": trans,
                    "flow_type": flow_type
                } 
                for source, target, schema, trans, flow_type in flows
            ]
            json.dump(serializable_flows, f, indent=2)
        print(f"Detailed JSON flows saved to {json_path}")
        
        # Add documentation for this workflow
        docs.append(f"## {name}\n\n")
        docs.append(f"**Description:** {info['desc']}\n\n")
        docs.append(f"![{name} Visualization](workflow_visualizations/{filename}.png)\n\n")
        docs.append("### Data Flow Details\n\n")
        
        for source, target, schema, trans, flow_type in flows:
            docs.append(f"#### {source} → {target}\n\n")
            
            # Add schema information
            if schema:
                docs.append("**Schema:**\n\n")
                docs.append("```\n")
                for k, v in schema.items():
                    if k != "__doc__":
                        docs.append(f"{k}: {v}\n")
                docs.append("```\n\n")
                
                # Add docstring if available
                if "__doc__" in schema:
                    docs.append(f"**Description:** {schema['__doc__']}\n\n")
            
            # Add transformation information
            if trans:
                docs.append("**Data Transformations:**\n\n")
                docs.append("```python\n")
                for t in trans:
                    docs.append(f"{t['target']} = {t['source']}\n")
                docs.append("```\n\n")
            
            docs.append("---\n\n")
    
    # Create an overview visualization showing all workflow types with more details
    create_workflow_overview_visualization()
    
    # Add the overview visualization to documentation
    docs.append("## Complete Workflow System Overview\n\n")
    docs.append("This diagram shows the entire workflow system architecture and all possible agent interactions:\n\n")
    docs.append("![Workflow System Overview](workflow_visualizations/workflow_overview.png)\n\n")
    
    # Write documentation file
    docs_path = output_dir.parent / "WORKFLOW_DATA_FLOW.md"
    with open(docs_path, 'w') as f:
        f.write("".join(docs))
    print(f"\nDetailed workflow documentation created at {docs_path}")
    
    print("\nEnhanced workflow visualizations complete!")
    print("To view the visualizations and documentation:")
    print(f"1. Open the PDF or PNG files in {output_dir}")
    print(f"2. Read the detailed documentation at {docs_path}")
    print("3. Or use an online Graphviz viewer with the DOT files")
    print("   (e.g., https://dreampuf.github.io/GraphvizOnline/)")

def create_workflow_overview_visualization():
    """Create an enhanced overview visualization showing all workflow types."""
    dot = graphviz.Digraph(comment='Workflow System Overview', 
                          graph_attr={'rankdir': 'TB', 'splines': 'polyline',
                                     'fontname': 'Arial', 'nodesep': '0.8',
                                     'ranksep': '1.2'})
    
    # Create clusters for better organization
    with dot.subgraph(name='cluster_input') as c:
        c.attr(style='filled', color='lightgrey', label='User Input')
        c.node('input', 'User Input', shape='ellipse', style='filled', fillcolor='lightblue')
    
    with dot.subgraph(name='cluster_manager') as c:
        c.attr(style='filled', color='lightgrey', label='Workflow Management')
        c.node('workflow_manager', 'Workflow Manager', shape='box', style='filled', fillcolor='#FFB6C1')
    
    with dot.subgraph(name='cluster_workflows') as c:
        c.attr(style='filled', color='lightgrey', label='Workflow Types')
        c.node('tdd', 'TDD Workflow', shape='box', style='filled', fillcolor='#98FB98')
        c.node('full', 'Full Workflow', shape='box', style='filled', fillcolor='#98FB98')
        c.node('individual', 'Individual Workflow', shape='box', style='filled', fillcolor='#98FB98')
    
    with dot.subgraph(name='cluster_agents') as c:
        c.attr(style='filled', color='lightgrey', label='Agent System')
        # Create subgroups to organize the agents by phase
        c.node('planner_agent', 'Planner', shape='box', style='filled', fillcolor='#FFFACD')
        c.node('designer_agent', 'Designer', shape='box', style='filled', fillcolor='#FFFACD')
        c.node('test_writer_agent', 'Test Writer', shape='box', style='filled', fillcolor='#FFFACD') 
        c.node('coder_agent', 'Coder', shape='box', style='filled', fillcolor='#FFFACD')
        c.node('reviewer_agent', 'Reviewer', shape='box', style='filled', fillcolor='#FFFACD')
    
    # Add schema information to edges
    dot.edge('input', 'workflow_manager', label='CodingTeamInput\n(requirements, workflow, team_members)', fontsize='10')
    
    # Connect workflow manager to workflow types with schema info
    dot.edge('workflow_manager', 'tdd', label='if workflow=tdd_workflow', fontsize='10')
    dot.edge('workflow_manager', 'full', label='if workflow=full_workflow', fontsize='10')
    dot.edge('workflow_manager', 'individual', label='if workflow=individual step', fontsize='10')
    
    # TDD workflow - show sequence with data passed
    dot.edge('tdd', 'planner_agent', label='1: requirements', color='blue', fontsize='9')
    dot.edge('planner_agent', 'designer_agent', label='2: plan', color='blue', fontsize='9')
    dot.edge('designer_agent', 'test_writer_agent', label='3: design', color='blue', fontsize='9')
    dot.edge('test_writer_agent', 'coder_agent', label='4: tests', color='blue', fontsize='9')
    dot.edge('coder_agent', 'reviewer_agent', label='5: code', color='blue', fontsize='9')
    
    # Full workflow with different color
    dot.edge('full', 'planner_agent', label='1: requirements', color='green', style='dashed', fontsize='9')
    dot.edge('planner_agent', 'designer_agent', label='2: plan', color='green', style='dashed', fontsize='9')
    dot.edge('designer_agent', 'coder_agent', label='3: design', color='green', style='dashed', fontsize='9')
    dot.edge('coder_agent', 'reviewer_agent', label='4: code', color='green', style='dashed', fontsize='9')
    
    # Individual workflow with different style
    dot.edge('individual', 'planner_agent', label='if step=planning', color='red', style='dotted', fontsize='9')
    dot.edge('individual', 'designer_agent', label='if step=design', color='red', style='dotted', fontsize='9')
    dot.edge('individual', 'test_writer_agent', label='if step=testing', color='red', style='dotted', fontsize='9')
    dot.edge('individual', 'coder_agent', label='if step=coding', color='red', style='dotted', fontsize='9')
    dot.edge('individual', 'reviewer_agent', label='if step=review', color='red', style='dotted', fontsize='9')
    
    # Add a legend
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='Legend', fontsize='12')
        legend.node('l_tdd', 'TDD Workflow', shape='plaintext', fontcolor='blue')
        legend.node('l_full', 'Full Workflow', shape='plaintext', fontcolor='green')
        legend.node('l_ind', 'Individual Steps', shape='plaintext', fontcolor='red')
        legend.node('l_review', 'Review Path', shape='plaintext')
        legend.node('l_feedback', 'Feedback Loop', shape='plaintext')
        
        # Add legend edges
        legend.edge('l_review', 'l_feedback', style='dashed', color='darkred', label='review')
        legend.edge('l_feedback', 'l_review', style='dotted', color='#DD4400', label='feedback')
        # Position the legend nodes horizontally
        legend.attr(rank='same')
        legend.edge('l_tdd', 'l_full', style='invis')
        legend.edge('l_full', 'l_ind', style='invis')
    
    # Save and render
    output_dir = project_root / "docs" / "workflow_visualizations"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    dot.save(str(output_dir / "workflow_overview.dot"))
    try:
        dot.render(str(output_dir / "workflow_overview"), format='pdf', cleanup=True)
        dot.render(str(output_dir / "workflow_overview"), format='png', cleanup=True,
                  renderer='cairo', formatter='cairo')
    except Exception as e:
        print(f"Warning: Could not render overview graph with enhanced settings: {e}")
        try:
            # Fall back to standard rendering
            dot.render(str(output_dir / "workflow_overview"), format='pdf', cleanup=True)
            dot.render(str(output_dir / "workflow_overview"), format='png', cleanup=True)
        except Exception as e2:
            print(f"Warning: Could not render overview graph: {e2}")
    
    print(f"Enhanced workflow overview visualization saved to {output_dir}")

if __name__ == "__main__":
    print("Enhanced Workflow Visualizer")
    print("=" * 50)
    
    # Create overview visualization
    print("Creating enhanced workflow overview visualization...")
    create_workflow_overview_visualization()
    
    # Analyze and visualize individual workflows
    visualize_all_workflows()
