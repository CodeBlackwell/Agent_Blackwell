"""
Workflow Visualizer V4 - Focused Edition

A streamlined visualization tool that produces only the preferred visualization types:
1. System Overview - Comprehensive layered architecture view
2. Flow Graphs - Clean workflow diagrams with edge types and legends

Features:
- Clean, focused code with only essential visualizations
- Modern theme with professional styling
- Edge type legends for flow understanding
- Minimal configuration options
"""

import os
import sys
from pathlib import Path
import inspect
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from dataclasses import dataclass

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

# Import shared data models
from shared.data_models import TeamMember, WorkflowStep


# ============================================================================
# THEME CONFIGURATION
# ============================================================================

@dataclass
class Theme:
    """Visual theme configuration"""
    # Background
    background: str = "#f8f9fa"
    
    # Node colors by type
    orchestrator: str = "#ce93d8"
    workflow_manager: str = "#ba68c8"
    workflow: str = "#81c784"
    agent: str = "#96ceb4"
    input: str = "#dda0dd"
    monitoring: str = "#ef5350"
    
    # Agent-specific colors
    planner: str = "#ff6b6b"
    designer: str = "#4ecdc4"
    test_writer: str = "#45b7d1"
    coder: str = "#96ceb4"
    reviewer: str = "#feca57"
    executor: str = "#ff9800"
    feature_orchestrator: str = "#4fc3f7"
    
    # Edge colors by type
    edge_sequential: str = "#3498db"
    edge_review: str = "#e74c3c"
    edge_feedback: str = "#f39c12"
    edge_approval: str = "#27ae60"
    edge_validation: str = "#9b59b6"
    
    # Cluster colors
    cluster_user: str = "#e3f2fd"
    cluster_orchestration: str = "#f3e5f5"
    cluster_workflows: str = "#e8f5e8"
    cluster_agents: str = "#fff3e0"
    cluster_monitoring: str = "#ffebee"
    
    # Text colors
    text_primary: str = "#2c3e50"
    text_white: str = "white"
    
    # Font settings
    font_family: str = "Arial"
    font_size: int = 12
    title_size: int = 24


# ============================================================================
# WORKFLOW VISUALIZER
# ============================================================================

class WorkflowVisualizer:
    """Focused workflow visualizer for system overview and flow graphs"""
    
    def __init__(self, output_dir: str = "docs/workflow_visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.theme = Theme()
        self.workflows = self._discover_workflows()
        
    def _discover_workflows(self) -> Dict[str, Any]:
        """Discover available workflows"""
        workflows = {}
        workflows_dir = project_root / "workflows"
        
        # Define known workflows
        known_workflows = [
            ("tdd", "TDD Workflow", "🧪"),
            ("full", "Full Workflow", "🚀"),
            ("individual", "Individual Steps", "📍"),
            ("incremental", "Incremental", "🔄")
        ]
        
        for workflow_name, display_name, icon in known_workflows:
            workflow_path = workflows_dir / workflow_name
            if workflow_path.exists() and workflow_path.is_dir():
                # Get workflow module info
                init_file = workflow_path / "__init__.py"
                if init_file.exists():
                    workflows[workflow_name] = {
                        "display_name": display_name,
                        "icon": icon,
                        "path": workflow_path,
                        "steps": self._extract_workflow_steps(workflow_name)
                    }
        
        return workflows
    
    def _extract_workflow_steps(self, workflow_name: str) -> List[Dict[str, str]]:
        """Extract workflow steps from workflow configuration"""
        steps = []
        
        # Define workflow steps based on workflow type
        if workflow_name == "tdd":
            # TDD follows: Planning -> Design -> Test Writing -> Implementation -> Execution -> Review
            steps = [
                {"name": "planner", "agent": "planner_agent", "icon": "📋"},
                {"name": "designer", "agent": "designer_agent", "icon": "🎨"},
                {"name": "test_writer", "agent": "test_writer_agent", "icon": "🧪"},
                {"name": "coder", "agent": "coder_agent", "icon": "💻"},
                {"name": "executor", "agent": "executor_agent", "icon": "⚡"},
                {"name": "reviewer", "agent": "reviewer_agent", "icon": "🔍"}
            ]
        elif workflow_name == "full":
            # Full workflow uses incremental coding internally
            steps = [
                {"name": "planner", "agent": "planner_agent", "icon": "📋"},
                {"name": "designer", "agent": "designer_agent", "icon": "🎨"},
                {"name": "coder", "agent": "coder_agent", "icon": "💻"},
                {"name": "reviewer", "agent": "reviewer_agent", "icon": "🔍"}
            ]
        elif workflow_name == "incremental":
            # Incremental workflow: Planning -> Design -> Feature Orchestration -> Review
            steps = [
                {"name": "planner", "agent": "planner_agent", "icon": "📋"},
                {"name": "designer", "agent": "designer_agent", "icon": "🎨"},
                {"name": "feature_orchestrator", "agent": "feature_orchestrator", "icon": "🔄"},
                {"name": "reviewer", "agent": "reviewer_agent", "icon": "🔍"}
            ]
        elif workflow_name == "individual":
            # Individual steps - can run any single agent
            steps = [
                {"name": "agent", "agent": "selected_agent", "icon": "🎯"}
            ]
        
        return steps
    
    def generate_system_overview(self) -> graphviz.Digraph:
        """Generate comprehensive system overview visualization"""
        graph = graphviz.Digraph(
            name='system_overview',
            comment='Modular Agent Workflow System Overview',
            format='svg',
            engine='dot'
        )
        
        # Graph attributes
        graph.attr(
            rankdir='TB',
            bgcolor=self.theme.background,
            fontname=self.theme.font_family,
            fontsize=str(self.theme.font_size),
            size='16,20',
            ratio='compress',
            splines='ortho',
            nodesep='0.8',
            ranksep='1.2'
        )
        
        # Title
        graph.node('title', 
                  label='🚀 Modular Agent Workflow System',
                  shape='box',
                  style='filled',
                  fillcolor='lightgrey',
                  fontsize=str(self.theme.title_size),
                  fontcolor=self.theme.text_primary)
        
        # User Layer
        with graph.subgraph(name='cluster_input') as user_layer:
            user_layer.attr(
                label='User Layer',
                style='filled,rounded',
                fillcolor=self.theme.cluster_user,
                color='#1976d2',
                fontsize='16'
            )
            
            user_layer.node('user', '👤 User',
                          shape='circle',
                          style='filled',
                          fillcolor='#bbdefb',
                          fontcolor=self.theme.text_white)
            
            user_layer.node('requirements', '📝 Requirements',
                          shape='note',
                          style='filled',
                          fillcolor='#90caf9',
                          fontcolor=self.theme.text_white)
            
            user_layer.edge('user', 'requirements')
        
        # Orchestration Layer
        with graph.subgraph(name='cluster_orchestration') as orch_layer:
            orch_layer.attr(
                label='Orchestration Layer',
                style='filled,rounded',
                fillcolor=self.theme.cluster_orchestration,
                color='#7b1fa2',
                fontsize='16'
            )
            
            orch_layer.node('orchestrator', '🎯 Orchestrator',
                          shape='tripleoctagon',
                          style='filled,bold',
                          fillcolor=self.theme.orchestrator,
                          penwidth='3')
            
            orch_layer.node('workflow_manager', '📊 Workflow Manager',
                          shape='component',
                          style='filled',
                          fillcolor=self.theme.workflow_manager,
                          fontcolor=self.theme.text_white)
        
        # Workflow Types
        with graph.subgraph(name='cluster_workflows') as workflow_layer:
            workflow_layer.attr(
                label='Workflow Types',
                style='filled,rounded',
                fillcolor=self.theme.cluster_workflows,
                color='#388e3c',
                fontsize='16'
            )
            
            for wf_name, wf_info in self.workflows.items():
                workflow_layer.node(
                    wf_name.replace('_workflow', ''),
                    f"{wf_info['icon']} {wf_info['display_name']}",
                    shape='cylinder',
                    style='filled',
                    fillcolor=self._get_workflow_color(wf_name),
                    fontcolor=self.theme.text_white
                )
        
        # Agent Pool
        with graph.subgraph(name='cluster_agents') as agent_layer:
            agent_layer.attr(
                label='Agent Pool',
                style='filled,rounded',
                fillcolor=self.theme.cluster_agents,
                color='#f57c00',
                fontsize='16',
                rank='same'
            )
            
            agents = [
                ('planner', '📋 Planner', self.theme.planner),
                ('test_writer', '🧪 Test Writer', self.theme.test_writer),
                ('designer', '🎨 Designer', self.theme.designer),
                ('coder', '💻 Coder', self.theme.coder),
                ('reviewer', '🔍 Reviewer', self.theme.reviewer)
            ]
            
            for agent_id, agent_label, color in agents:
                agent_layer.node(agent_id, agent_label,
                              shape='box3d',
                              style='filled',
                              fillcolor=color,
                              fontcolor=self.theme.text_white)
        
        # Monitoring & Analytics
        with graph.subgraph(name='cluster_monitoring') as monitor_layer:
            monitor_layer.attr(
                label='Monitoring & Analytics',
                style='filled,rounded',
                fillcolor=self.theme.cluster_monitoring,
                color='#c62828',
                fontsize='16'
            )
            
            monitor_layer.node('tracer', '📈 Execution Tracer',
                            shape='component',
                            style='filled',
                            fillcolor=self.theme.monitoring,
                            fontcolor=self.theme.text_white)
            
            monitor_layer.node('reports', '📊 Reports',
                            shape='folder',
                            style='filled',
                            fillcolor='#e53935',
                            fontcolor=self.theme.text_white)
        
        # Add edges
        graph.edge('orchestrator', 'workflow_manager', 
                   style='bold', penwidth='2')
        graph.edge('requirements', 'orchestrator',
                   style='bold', penwidth='3')
        graph.edge('orchestrator', 'tracer',
                   style='dashed', color='red', label='monitors')
        graph.edge('tracer', 'reports')
        
        # Workflow connections
        for wf_name in self.workflows:
            wf_id = wf_name
            graph.edge('workflow_manager', wf_id,
                      label=f"if {wf_id.title()}", fontsize='10')
            
            # Connect workflows to agents
            for agent in ['planner', 'designer', 'test_writer', 'coder', 'reviewer']:
                graph.edge(wf_id, agent,
                          style='dashed,dotted', color='gray', arrowhead='none')
        
        return graph
    
    def generate_workflow_flow(self, workflow_name: str) -> graphviz.Digraph:
        """Generate flow graph for a specific workflow"""
        workflow_info = self.workflows.get(workflow_name)
        if not workflow_info:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        graph = graphviz.Digraph(
            name=f'{workflow_name}_flow',
            comment=f'{workflow_info["display_name"]} Flow',
            format='svg',
            engine='dot'
        )
        
        # Graph attributes
        graph.attr(
            rankdir='TB',
            bgcolor=self.theme.background,
            fontname=self.theme.font_family,
            fontsize=str(self.theme.font_size),
            size='12,16',
            ratio='compress',
            splines='true',
            nodesep='0.8',
            ranksep='1.0'
        )
        
        # Title
        graph.node('title',
                  label=f'{workflow_info["display_name"]} Workflow',
                  shape='box',
                  style='filled',
                  fillcolor='lightgrey',
                  fontsize='20',
                  fontcolor=self.theme.text_primary)
        
        # Input node
        graph.node('input', '📥 Input',
                  shape='invhouse',
                  style='filled',
                  fillcolor=self.theme.input,
                  fontcolor=self.theme.text_white)
        
        # Add workflow steps
        steps = workflow_info.get('steps', [])
        prev_node = 'input'
        
        for i, step in enumerate(steps):
            node_id = f"{step['agent']}"
            label = f"{step['icon']} {step['name'].replace('_', ' ').title()}"
            color = getattr(self.theme, step['name'], self.theme.agent)
            
            # Special handling for feature orchestrator
            if step['name'] == 'feature_orchestrator':
                color = '#4fc3f7'  # Light blue for orchestrator
                shape = 'doubleoctagon'
            else:
                shape = 'component'
            
            graph.node(node_id, label,
                      shape=shape,
                      style='filled',
                      fillcolor=color,
                      fontcolor=self.theme.text_white)
            
            # Add sequential edge
            if prev_node:
                edge_label = None
                if i == 0:
                    edge_label = 'initial_input'
                elif prev_node == 'input':
                    edge_label = 'requirements'
                    
                graph.edge(prev_node, node_id,
                          color=self.theme.edge_sequential,
                          penwidth='2',
                          label=edge_label,
                          fontsize='10')
            
            # Special handling for TDD workflow review connections
            if workflow_name == 'tdd':
                # In TDD, planner/designer/test_writer outputs are reviewed before next step
                if step['name'] in ['planner', 'designer', 'test_writer']:
                    # Create a review point after this step
                    review_point = f"{step['name']}_review"
                    graph.node(review_point, '🔍',
                              shape='diamond',
                              style='filled',
                              fillcolor=self.theme.reviewer,
                              width='0.5',
                              height='0.5')
                    
                    # Connect step to review point
                    graph.edge(node_id, review_point,
                              color=self.theme.edge_review,
                              style='dashed',
                              penwidth='2',
                              fontsize='10')
                    
                    # Connect review point to next step
                    if i < len(steps) - 1:
                        next_step = steps[i + 1]
                        graph.edge(review_point, f"{next_step['agent']}",
                                  color=self.theme.edge_approval,
                                  penwidth='2',
                                  fontsize='10')
            
            # Special handling for incremental workflow
            elif workflow_name == 'incremental' and step['name'] == 'feature_orchestrator':
                # Show the incremental coding loop
                with graph.subgraph(name='cluster_features') as features:
                    features.attr(
                        label='Feature-by-Feature Implementation',
                        style='rounded,dashed',
                        color='#546e7a',
                        fontsize='12'
                    )
                    
                    # Add coder node inside
                    features.node('incremental_coder', '💻 Coder',
                                shape='box',
                                style='filled',
                                fillcolor=self.theme.coder,
                                fontcolor=self.theme.text_white)
                    
                    # Add retry mechanism
                    features.node('retry_logic', '🔄 Retry Logic',
                                shape='diamond',
                                style='filled',
                                fillcolor='#ffb74d',
                                fontcolor=self.theme.text_white)
                    
                # Connect orchestrator to coder
                graph.edge(node_id, 'incremental_coder',
                          color='#4fc3f7',
                          penwidth='2',
                          label='for each feature',
                          fontsize='10')
                
                # Connect coder to retry logic
                graph.edge('incremental_coder', 'retry_logic',
                          color=self.theme.edge_validation,
                          style='dotted',
                          penwidth='2')
                
                # Retry loop
                graph.edge('retry_logic', 'incremental_coder',
                          color=self.theme.edge_feedback,
                          style='dashed',
                          penwidth='2',
                          label='retry',
                          fontsize='10')
            
            prev_node = node_id
        
        # Add final output
        if steps:
            last_step = steps[-1]
            graph.node('output', '📤 Output',
                      shape='house',
                      style='filled',
                      fillcolor='#c8e6c9',
                      fontcolor='black')
            
            graph.edge(f"{last_step['agent']}", 'output',
                      color=self.theme.edge_approval,
                      penwidth='2',
                      label='final',
                      fontsize='10')
        
        # Add legend
        with graph.subgraph(name='cluster_legend') as legend:
            legend.attr(
                label='Flow Types',
                style='filled,rounded',
                fillcolor='#ecf0f1',
                color='#34495e',
                fontsize='14'
            )
            
            # Legend nodes
            legend_items = [
                ('legend_sequential', 'Sequential', self.theme.edge_sequential),
                ('legend_review', 'Review', self.theme.edge_review),
                ('legend_feedback', 'Feedback', self.theme.edge_feedback),
                ('legend_approval', 'Approval', self.theme.edge_approval),
                ('legend_validation', 'Validation', self.theme.edge_validation)
            ]
            
            prev_legend = None
            for node_id, label, color in legend_items:
                legend.node(node_id, label,
                          shape='box',
                          style='filled',
                          fillcolor='lightgrey')
                
                if prev_legend:
                    legend.edge(prev_legend, node_id,
                              color=color,
                              penwidth='2')
                prev_legend = node_id
        
        return graph
    
    def _get_workflow_color(self, workflow_name: str) -> str:
        """Get color for workflow based on name"""
        colors = {
            'tdd': '#81c784',
            'full': '#66bb6a',
            'individual': '#4caf50',
            'incremental': '#43a047'
        }
        return colors.get(workflow_name, self.theme.workflow)
    
    def generate_all(self):
        """Generate all visualizations"""
        print("🎨 Generating workflow visualizations...")
        
        # Generate system overview
        print("  📊 Creating system overview...")
        system_graph = self.generate_system_overview()
        system_graph.render(
            filename=str(self.output_dir / 'system_overview'),
            format='svg',
            cleanup=True
        )
        system_graph.render(
            filename=str(self.output_dir / 'system_overview'),
            format='png',
            cleanup=True
        )
        
        # Generate workflow flows
        for workflow_name, workflow_info in self.workflows.items():
            print(f"  {workflow_info['icon']} Creating {workflow_info['display_name']} flow...")
            flow_graph = self.generate_workflow_flow(workflow_name)
            flow_graph.render(
                filename=str(self.output_dir / f'{workflow_name}_flow'),
                format='svg',
                cleanup=True
            )
            flow_graph.render(
                filename=str(self.output_dir / f'{workflow_name}_flow'),
                format='png',
                cleanup=True
            )
        
        print(f"\n✅ Visualizations generated in: {self.output_dir}")
        print(f"   - System Overview: system_overview.svg/png")
        for wf_name, wf_info in self.workflows.items():
            print(f"   - {wf_info['display_name']}: {wf_name}_flow.svg/png")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the visualizer"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate focused workflow visualizations (system overview and flow graphs)'
    )
    parser.add_argument(
        '--output-dir',
        default='docs/workflow_visualizations',
        help='Output directory for visualizations'
    )
    parser.add_argument(
        '--workflow',
        choices=['tdd', 'full', 'individual', 'incremental'],
        help='Generate visualization for specific workflow only'
    )
    parser.add_argument(
        '--system-only',
        action='store_true',
        help='Generate only the system overview'
    )
    
    args = parser.parse_args()
    
    # Create visualizer
    visualizer = WorkflowVisualizer(output_dir=args.output_dir)
    
    if args.system_only:
        print("🎨 Generating system overview only...")
        system_graph = visualizer.generate_system_overview()
        system_graph.render(
            filename=str(visualizer.output_dir / 'system_overview'),
            format='svg',
            cleanup=True
        )
        system_graph.render(
            filename=str(visualizer.output_dir / 'system_overview'),
            format='png',
            cleanup=True
        )
        print(f"✅ System overview generated in: {visualizer.output_dir}")
    elif args.workflow:
        print(f"🎨 Generating visualization for {args.workflow}...")
        flow_graph = visualizer.generate_workflow_flow(args.workflow)
        flow_graph.render(
            filename=str(visualizer.output_dir / f'{args.workflow}_flow'),
            format='svg',
            cleanup=True
        )
        flow_graph.render(
            filename=str(visualizer.output_dir / f'{args.workflow}_flow'),
            format='png',
            cleanup=True
        )
        print(f"✅ Workflow flow generated in: {visualizer.output_dir}")
    else:
        visualizer.generate_all()


if __name__ == "__main__":
    main()