"""
Workflow Visualizer

This script generates visualizations of the data flow between agents in the workflow system,
including schema information and directional arrows.
"""

import os
import sys
from pathlib import Path
import inspect
from typing import Dict, List, Tuple, Set, Optional
import importlib
import json

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

# Schema information extraction
def extract_schema_info(obj_type) -> Dict:
    """Extract schema information from a type annotation."""
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
            
            schema[field_name] = type_name
            
    return schema

# Agent data flow analyzer
def analyze_workflow_data_flow(workflow_function) -> List[Tuple[str, str, Dict]]:
    """
    Analyze a workflow function to determine the data flow between agents.
    Returns a list of (source, target, data_schema) tuples.
    """
    flows = []
    source = "input"
    target = None
    data_schema = {}
    
    # Inspect the source code
    source_lines = inspect.getsource(workflow_function).split('\n')
    
    # Find all occurrences of run_team_member
    for i, line in enumerate(source_lines):
        if "run_team_member" in line and "await" in line:
            # Extract the agent name
            for member in TeamMember:
                if member.value in line:
                    target = member.value
                    break
            
            # Find what data is passed to this agent
            # This is a simplified approach - in reality you might need more sophisticated parsing
            if target:
                # Look backward to find what's being passed to this agent
                context_lines = source_lines[max(0, i-5):i]
                for context_line in context_lines:
                    if "=" in context_line and "results" in context_line:
                        # Simple schema extraction based on what we know about our data models
                        if source == "input":
                            data_schema = extract_schema_info(CodingTeamInput)
                        else:
                            data_schema = extract_schema_info(TeamMemberResult)
                
                flows.append((source, target, data_schema))
                source = target
                target = None
    
    return flows

# Graph generation
def generate_workflow_graph(workflow_name: str, data_flows: List[Tuple[str, str, Dict]]) -> graphviz.Digraph:
    """Generate a directed graph visualizing the workflow data flow."""
    dot = graphviz.Digraph(comment=f'{workflow_name} Workflow')
    
    # Add nodes
    nodes = set()
    for source, target, _ in data_flows:
        nodes.add(source)
        nodes.add(target)
    
    for node in nodes:
        if node == "input":
            dot.node(node, shape='ellipse', style='filled', fillcolor='lightblue')
        else:
            dot.node(node, shape='box', style='filled', fillcolor='lightgreen')
    
    # Add edges with schema information
    for source, target, schema in data_flows:
        # Format schema info for edge label
        if schema:
            schema_str = "\\n".join([f"{k}: {v}" for k, v in schema.items()])
            # Truncate if too long
            if len(schema_str) > 200:
                schema_str = schema_str[:197] + "..."
        else:
            schema_str = "Unknown Schema"
            
        dot.edge(source, target, label=schema_str, fontsize='8')
    
    return dot

def visualize_all_workflows():
    """Generate visualizations for all workflows."""
    output_dir = project_root / "docs" / "workflow_visualizations"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Mapping of workflow functions to their names
    workflows = {
        "TDD Workflow": run_tdd_workflow,
        "Full Workflow": run_full_workflow,
        "Individual Workflow": run_individual_workflow
    }
    
    print(f"Generating workflow visualizations in {output_dir}...")
    
    for name, func in workflows.items():
        print(f"Analyzing {name}...")
        flows = analyze_workflow_data_flow(func)
        
        print(f"Generating graph for {name}...")
        graph = generate_workflow_graph(name, flows)
        
        # Save as both DOT file and rendered PDF/PNG
        filename = name.lower().replace(" ", "_")
        dot_path = output_dir / f"{filename}.dot"
        pdf_path = output_dir / f"{filename}.pdf"
        png_path = output_dir / f"{filename}.png"
        
        graph.save(str(dot_path))
        try:
            # Render to PDF
            graph.render(str(output_dir / filename), format='pdf', cleanup=True)
            print(f"PDF saved to {pdf_path}")
            
            # Render to PNG for easier viewing
            graph.render(str(output_dir / filename), format='png', cleanup=True)
            print(f"PNG saved to {png_path}")
        except Exception as e:
            print(f"Warning: Could not render graph to PDF/PNG: {e}")
            print("This often happens if Graphviz is not properly installed.")
            print("You can still use the DOT file with an online Graphviz viewer.")
        
        print(f"DOT file saved to {dot_path}")
        
        # Also generate a JSON representation of the flows
        json_path = output_dir / f"{filename}_flows.json"
        with open(json_path, 'w') as f:
            # Convert schema dicts to strings to make them JSON serializable
            serializable_flows = [
                (source, target, str(schema)) 
                for source, target, schema in flows
            ]
            json.dump(serializable_flows, f, indent=2)
        print(f"JSON flows saved to {json_path}")
    
    print("\nWorkflow visualizations complete!")
    print("To view the visualizations:")
    print(f"1. Open the PDF or PNG files in {output_dir}")
    print("2. Or use an online Graphviz viewer with the DOT files")
    print("   (e.g., https://dreampuf.github.io/GraphvizOnline/)")

def create_workflow_overview_visualization():
    """Create an overview visualization showing all workflow types."""
    dot = graphviz.Digraph(comment='Workflow Overview')
    
    # Add workflow types
    dot.node('input', 'User Input', shape='ellipse', style='filled', fillcolor='lightblue')
    dot.node('workflow_manager', 'Workflow Manager', shape='box', style='filled', fillcolor='lightpink')
    dot.node('tdd', 'TDD Workflow', shape='box', style='filled', fillcolor='lightgreen')
    dot.node('full', 'Full Workflow', shape='box', style='filled', fillcolor='lightgreen')
    dot.node('individual', 'Individual Workflow', shape='box', style='filled', fillcolor='lightgreen')
    
    # Add team members
    for member in TeamMember:
        dot.node(member.value, member.value.capitalize(), shape='box', style='filled', fillcolor='lightyellow')
    
    # Connect workflow manager to workflow types
    dot.edge('input', 'workflow_manager', label='CodingTeamInput')
    dot.edge('workflow_manager', 'tdd', label='if workflow=tdd_workflow')
    dot.edge('workflow_manager', 'full', label='if workflow=full_workflow')
    dot.edge('workflow_manager', 'individual', label='if workflow=individual step')
    
    # Connect workflows to team members (simplified)
    # TDD workflow
    dot.edge('tdd', 'planner_agent', label='1')
    dot.edge('planner_agent', 'designer_agent', label='2') 
    dot.edge('designer_agent', 'test_writer_agent', label='3')
    dot.edge('test_writer_agent', 'coder_agent', label='4')
    dot.edge('coder_agent', 'reviewer_agent', label='5')
    
    # Full workflow
    dot.edge('full', 'planner_agent', label='1', style='dashed')
    dot.edge('planner_agent', 'designer_agent', label='2', style='dashed')
    dot.edge('designer_agent', 'coder_agent', label='3', style='dashed')
    dot.edge('coder_agent', 'reviewer_agent', label='4', style='dashed')
    
    # Individual workflow (just examples)
    dot.edge('individual', 'planner_agent', label='if step=planning', style='dotted')
    dot.edge('individual', 'designer_agent', label='if step=design', style='dotted')
    dot.edge('individual', 'coder_agent', label='if step=coding', style='dotted')
    dot.edge('individual', 'test_writer_agent', label='if step=testing', style='dotted')
    dot.edge('individual', 'reviewer_agent', label='if step=review', style='dotted')
    
    # Save and render
    output_dir = project_root / "docs" / "workflow_visualizations"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    dot.save(str(output_dir / "workflow_overview.dot"))
    try:
        dot.render(str(output_dir / "workflow_overview"), format='pdf', cleanup=True)
        dot.render(str(output_dir / "workflow_overview"), format='png', cleanup=True)
    except Exception as e:
        print(f"Warning: Could not render overview graph: {e}")
    
    print(f"Workflow overview visualization saved to {output_dir}")
    
if __name__ == "__main__":
    print("Workflow Visualizer")
    print("=" * 50)
    
    # Create overview visualization
    print("Creating workflow overview visualization...")
    create_workflow_overview_visualization()
    
    # Analyze and visualize individual workflows
    visualize_all_workflows()
