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
                type_name = field_type._name
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
def analyze_workflow_data_flow(workflow_function) -> List[Tuple[str, str, Dict, List[Dict]]]:
    """
    Analyze a workflow function to determine the data flow between agents.
    Returns a list of (source, target, data_schema, transformations) tuples.
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
    
    # Find all occurrences of run_team_member
    for i, line in enumerate(source_lines):
        if "run_team_member" in line and "await" in line:
            # Extract the agent name
            for member in TeamMember:
                if member.value in line:
                    target = member.value
                    break
            
            # If target found, analyze data passed to this agent
            if target:
                # Look at context (5 lines before) to understand data flow
                context_lines = source_lines[max(0, i-5):i]
                context_text = "\n".join(context_lines)
                
                # Find transformations relevant to this agent call
                agent_transformations = []
                for t in all_transformations:
                    if any(var in context_text for var in [t['target'], t['source']]):
                        agent_transformations.append(t)
                
                # Determine schema based on the source
                if source == "input":
                    data_schema = extract_schema_info(CodingTeamInput)
                else:
                    data_schema = extract_schema_info(TeamMemberResult)
                
                flows.append((source, target, data_schema, agent_transformations))
                source = target
                target = None
    
    return flows

# Enhanced graph generation
def generate_workflow_graph(workflow_name: str, data_flows: List[Tuple[str, str, Dict, List[Dict]]]) -> graphviz.Digraph:
    """Generate a detailed directed graph visualizing the workflow data flow."""
    dot = graphviz.Digraph(comment=f'{workflow_name} Workflow', 
                          graph_attr={'rankdir': 'LR', 'splines': 'ortho'})
    
    # Add nodes
    nodes = set()
    for source, target, _, _ in data_flows:
        nodes.add(source)
        nodes.add(target)
    
    for node in nodes:
        if node == "input":
            dot.node(node, shape='ellipse', style='filled', fillcolor='lightblue')
        elif node == "output":
            dot.node(node, shape='ellipse', style='filled', fillcolor='lightgreen')
        else:
            # Make agent nodes more informative
            dot.node(node, f"{node.replace('_agent', '')}", 
                    shape='box', style='filled', fillcolor='#FFFACD',  # Light yellow
                    fontname="Arial", fontsize="12")
    
    # Add edges with schema information
    for source, target, schema, transformations in data_flows:
        # Format schema info for edge label
        if schema:
            # Remove internal fields and keep only key data fields
            visible_fields = {k: v for k, v in schema.items() 
                            if not k.startswith('_') and k not in ['__doc__']}
            
            # Format as field: type pairs
            schema_str = "\\n".join([f"{k}: {v}" for k, v in visible_fields.items()])
            
            # Add transformation info if available
            if transformations:
                trans_str = "\\n\\nTransformations:\\n" + "\\n".join([
                    f"{t['target']} = {t['source'][:30]}..." if len(t['source']) > 30 
                    else f"{t['target']} = {t['source']}" 
                    for t in transformations[:3]
                ])
                if len(transformations) > 3:
                    trans_str += f"\\n(+{len(transformations)-3} more)"
                schema_str += trans_str
            
            # Truncate if too long
            if len(schema_str) > 300:
                schema_str = schema_str[:297] + "..."
        else:
            schema_str = "Unknown Schema"
            
        dot.edge(source, target, label=schema_str, fontsize='10', fontname="Arial", penwidth="1.5")
    
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
            
            # Render to PNG with higher DPI
            graph.render(str(output_dir / filename), format='png', cleanup=True, 
                        renderer='cairo', formatter='cairo', dpi=300)
            print(f"High-resolution PNG saved to {png_path}")
        except Exception as e:
            print(f"Warning: Could not render graph to PDF/PNG with enhanced settings: {e}")
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
                    "transformations": trans
                } 
                for source, target, schema, trans in flows
            ]
            json.dump(serializable_flows, f, indent=2)
        print(f"Detailed JSON flows saved to {json_path}")
        
        # Add documentation for this workflow
        docs.append(f"## {name}\n\n")
        docs.append(f"**Description:** {info['desc']}\n\n")
        docs.append(f"![{name} Visualization](workflow_visualizations/{filename}.png)\n\n")
        docs.append("### Data Flow Details\n\n")
        
        for source, target, schema, trans in flows:
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
                          graph_attr={'rankdir': 'TD', 'splines': 'polyline',
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
                  renderer='cairo', formatter='cairo', dpi=300)
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
