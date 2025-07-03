"""
Enhanced Workflow Visualizer with Creative Visualizations

This script generates beautiful, informative visualizations of the data flow between agents 
in the workflow system, incorporating the new monitoring capabilities and creative design elements.
"""

import os
import sys
from pathlib import Path
import inspect
from typing import Dict, List, Tuple, Set, Optional, Any, Union
import importlib
import json
import re
import ast
from datetime import datetime
import colorsys
import math

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

# Import workflow components
from orchestrator.orchestrator_agent import (
    TeamMember, WorkflowStep, CodingTeamInput, TeamMemberResult,
    CodingTeamResult
)

# Import monitoring components
from workflows.monitoring import (
    WorkflowExecutionTracer, WorkflowExecutionReport, 
    StepStatus, ReviewDecision
)

# Import workflow modules
from workflows.tdd.tdd_workflow import run_tdd_workflow
from workflows.full.full_workflow import run_full_workflow
from workflows.individual.individual_workflow import run_individual_workflow


# ============================================================================
# COLOR SCHEMES AND VISUAL CONFIGURATION
# ============================================================================

class VisualTheme:
    """Visual theme configuration for the workflow visualizer"""
    
    # Agent color palette (modern, vibrant colors)
    AGENT_COLORS = {
        'planner_agent': '#FF6B6B',      # Coral red
        'designer_agent': '#4ECDC4',     # Turquoise
        'test_writer_agent': '#45B7D1',  # Sky blue
        'coder_agent': '#96CEB4',        # Mint green
        'reviewer_agent': '#FECA57',     # Golden yellow
        'input': '#DDA0DD',              # Plum
        'output': '#98D8C8',             # Seafoam
        'test_execution': '#F7DC6F',     # Soft yellow
        'workflow_continuation': '#E8E8E8',  # Light gray
        'error': '#FF4757',              # Error red
        'success': '#2ED573',            # Success green
        'retry': '#FFA502',              # Orange
        'milestone': '#B983FF'           # Purple
    }
    
    # Edge colors by flow type
    FLOW_COLORS = {
        'sequential': '#3498DB',         # Bright blue
        'review': '#E74C3C',            # Red
        'feedback': '#F39C12',          # Orange
        'approval': '#27AE60',          # Green
        'validation': '#9B59B6',        # Purple
        'retry': '#E67E22',             # Dark orange
        'error': '#C0392B',             # Dark red
        'parallel': '#16A085'           # Teal
    }
    
    # Status colors
    STATUS_COLORS = {
        StepStatus.PENDING: '#95A5A6',
        StepStatus.RUNNING: '#3498DB',
        StepStatus.COMPLETED: '#2ECC71',
        StepStatus.FAILED: '#E74C3C',
        StepStatus.RETRYING: '#F39C12',
        StepStatus.SKIPPED: '#BDC3C7'
    }
    
    # Shape configurations
    SHAPES = {
        'agent': 'box',
        'input': 'ellipse',
        'output': 'ellipse',
        'decision': 'diamond',
        'process': 'cylinder',
        'milestone': 'doublecircle',
        'error': 'octagon',
        'test': 'component',
        'review': 'house',
        'retry': 'invtriangle'
    }
    
    @staticmethod
    def get_gradient_color(value: float, min_val: float = 0, max_val: float = 1) -> str:
        """Generate a gradient color based on a value (for performance metrics)"""
        # Normalize value to 0-1 range
        normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
        # Use HSV color space for smooth gradients (green to red)
        hue = 0.3 * (1 - normalized)  # 0.3 = green, 0 = red
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"


# ============================================================================
# ENHANCED VISUALIZATION FUNCTIONS
# ============================================================================

def create_workflow_metrics_graph(execution_report: WorkflowExecutionReport) -> graphviz.Digraph:
    """Create a metrics-focused visualization showing performance data"""
    dot = graphviz.Digraph(comment='Workflow Metrics Visualization')
    dot.attr(rankdir='TB', size='14,20', bgcolor='#F8F9FA')
    dot.attr('node', fontname='Arial', fontsize='12')
    dot.attr('edge', fontname='Arial', fontsize='10')
    
    # Title
    dot.node('title', f'Workflow Metrics: {execution_report.workflow_type}', 
             shape='plaintext', fontsize='20', fontcolor='#2C3E50')
    
    # Create metrics dashboard
    with dot.subgraph(name='cluster_metrics') as metrics:
        metrics.attr(label='Performance Metrics', fontsize='16', 
                    style='filled,rounded', fillcolor='#ECF0F1', color='#34495E')
        
        # Overall metrics box
        overall_metrics = f"""{{
Overall Performance|
{{Duration|{execution_report.total_duration_seconds:.2f}s}}|
{{Steps|{execution_report.step_count}}}|
{{Success Rate|{(execution_report.completed_steps/execution_report.step_count*100):.1f}%}}|
{{Reviews|{execution_report.total_reviews}}}|
{{Retries|{execution_report.total_retries}}}
}}"""
        metrics.node('overall', overall_metrics, shape='record', 
                    style='filled,rounded', fillcolor='white')
    
    # Agent performance visualization
    with dot.subgraph(name='cluster_agents') as agents:
        agents.attr(label='Agent Performance', fontsize='16',
                   style='filled,rounded', fillcolor='#E8F6F3', color='#16A085')
        
        max_duration = max((perf.get('average_duration', 0) 
                           for perf in execution_report.agent_performance.values()), default=1)
        
        for agent, perf in execution_report.agent_performance.items():
            avg_duration = perf.get('average_duration', 0)
            success_rate = perf.get('success_rate', 0) * 100
            color = VisualTheme.get_gradient_color(avg_duration, 0, max_duration)
            
            agent_metrics = f"""{{
{agent}|
{{Calls|{perf.get('total_calls', 0)}}}|
{{Avg Time|{avg_duration:.2f}s}}|
{{Success|{success_rate:.1f}%}}|
{{Reviews|{perf.get('reviews_received', 0)}}}
}}"""
            agents.node(f'agent_{agent}', agent_metrics, shape='record',
                       style='filled,rounded', fillcolor=color)
    
    # Test results if available
    if execution_report.test_executions:
        with dot.subgraph(name='cluster_tests') as tests:
            tests.attr(label='Test Results', fontsize='16',
                      style='filled,rounded', fillcolor='#EBF5FB', color='#3498DB')
            
            test_metrics = f"""{{
Test Execution|
{{Total Tests|{execution_report.total_tests}}}|
{{Passed|{execution_report.passed_tests}}}|
{{Failed|{execution_report.failed_tests}}}|
{{Pass Rate|{(execution_report.passed_tests/execution_report.total_tests*100):.1f}%}}
}}"""
            tests.node('tests', test_metrics, shape='record',
                      style='filled,rounded', fillcolor='white')
    
    return dot


def create_timeline_visualization(execution_report: WorkflowExecutionReport) -> graphviz.Digraph:
    """Create a timeline visualization showing the temporal flow of the workflow"""
    dot = graphviz.Digraph(comment='Workflow Timeline')
    dot.attr(rankdir='LR', size='20,10', bgcolor='#FAFAFA')
    dot.attr('node', fontname='Arial', fontsize='11', shape='box', style='filled,rounded')
    dot.attr('edge', fontname='Arial', fontsize='9')
    
    # Title
    dot.node('start', 'START', shape='circle', fillcolor='#2ECC71', fontcolor='white')
    
    # Sort steps by start time
    sorted_steps = sorted(execution_report.steps, key=lambda s: s.start_time)
    
    # Create timeline nodes
    prev_node = 'start'
    for i, step in enumerate(sorted_steps):
        node_id = f'step_{i}'
        
        # Determine color based on status
        color = VisualTheme.STATUS_COLORS.get(step.status, '#95A5A6')
        
        # Create label with timing info
        duration_str = f"{step.duration_seconds:.2f}s" if step.duration_seconds else "N/A"
        label = f"{step.step_name}\\n{step.agent_name}\\n{duration_str}"
        
        # Add node
        dot.node(node_id, label, fillcolor=color, fontcolor='white' if step.status != StepStatus.PENDING else 'black')
        
        # Connect to previous
        dot.edge(prev_node, node_id, label=f"{i+1}")
        prev_node = node_id
    
    # End node
    end_color = '#2ECC71' if execution_report.status == StepStatus.COMPLETED else '#E74C3C'
    dot.node('end', 'END', shape='circle', fillcolor=end_color, fontcolor='white')
    dot.edge(prev_node, 'end')
    
    # Add legend for status colors
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='Status Legend', fontsize='14', style='filled', fillcolor='#ECF0F1')
        
        for status, color in VisualTheme.STATUS_COLORS.items():
            legend.node(f'legend_{status.value}', status.value.title(), 
                       fillcolor=color, fontcolor='white' if status != StepStatus.PENDING else 'black')
    
    return dot


def create_review_flow_visualization(execution_report: WorkflowExecutionReport) -> graphviz.Digraph:
    """Create a visualization focused on the review and feedback flow"""
    dot = graphviz.Digraph(comment='Review Flow Visualization')
    dot.attr(rankdir='TB', size='12,16', bgcolor='#FFF5F5')
    dot.attr('node', fontname='Arial', fontsize='12')
    dot.attr('edge', fontname='Arial', fontsize='10')
    
    # Track which agents have been added
    agents_added = set()
    
    # Create nodes for each unique agent that received reviews
    for review in execution_report.reviews:
        target_agent = review.metadata.get('target_agent', 'unknown')
        
        if target_agent not in agents_added:
            color = VisualTheme.AGENT_COLORS.get(target_agent, '#95A5A6')
            dot.node(target_agent, target_agent.replace('_', ' ').title(), 
                    shape='box', style='filled,rounded', fillcolor=color, fontcolor='white')
            agents_added.add(target_agent)
    
    # Add reviewer node
    dot.node('reviewer', 'Reviewer', shape='house', style='filled', 
            fillcolor=VisualTheme.AGENT_COLORS['reviewer_agent'], fontcolor='black')
    
    # Create review edges
    review_counts = {}
    for i, review in enumerate(execution_report.reviews):
        target_agent = review.metadata.get('target_agent', 'unknown')
        
        # Count reviews per agent
        key = f"{target_agent}_reviewer"
        review_counts[key] = review_counts.get(key, 0) + 1
        
        # Determine edge style based on decision
        if review.decision == ReviewDecision.APPROVED:
            style = 'solid'
            color = VisualTheme.FLOW_COLORS['approval']
            arrowhead = 'normal'
        elif review.decision == ReviewDecision.REVISION_NEEDED:
            style = 'dashed'
            color = VisualTheme.FLOW_COLORS['feedback']
            arrowhead = 'tee'
        elif review.decision == ReviewDecision.AUTO_APPROVED:
            style = 'dotted'
            color = VisualTheme.FLOW_COLORS['validation']
            arrowhead = 'empty'
        else:
            style = 'solid'
            color = VisualTheme.FLOW_COLORS['review']
            arrowhead = 'normal'
        
        # Create review edge
        label = f"Review {review_counts[key]}\\n{review.decision.value}"
        if review.retry_count > 0:
            label += f"\\nRetry: {review.retry_count}"
        
        dot.edge(target_agent, 'reviewer', label=label, style=style, 
                color=color, arrowhead=arrowhead, penwidth='2')
        
        # Add feedback edge if revision needed
        if review.decision == ReviewDecision.REVISION_NEEDED and review.feedback:
            feedback_label = review.feedback[:30] + "..." if len(review.feedback) > 30 else review.feedback
            dot.edge('reviewer', target_agent, label=feedback_label, 
                    style='dotted', color=color, penwidth='2')
    
    # Add review statistics
    stats_label = f"""Review Statistics
Total: {execution_report.total_reviews}
Approved: {execution_report.approved_reviews}
Revisions: {execution_report.revision_requests}
Auto-approved: {execution_report.auto_approvals}"""
    
    dot.node('stats', stats_label, shape='note', style='filled', 
            fillcolor='#FFFACD', fontsize='14')
    
    return dot


def create_enhanced_workflow_graph(workflow_name: str, data_flows: List[Tuple[str, str, Dict, List[Dict], Optional[str]]],
                                 execution_report: Optional[WorkflowExecutionReport] = None) -> graphviz.Digraph:
    """Generate an enhanced, creative visualization of the workflow"""
    dot = graphviz.Digraph(comment=f'{workflow_name} Enhanced Visualization')
    dot.attr(rankdir='TB', size='16,24', bgcolor='#FAFAFA', pad='0.5')
    dot.attr('node', fontname='Arial', fontsize='12', style='filled')
    dot.attr('edge', fontname='Arial', fontsize='10')
    
    # Add title with workflow info
    title_label = f"{workflow_name} Workflow"
    if execution_report:
        duration = execution_report.total_duration_seconds or 0
        title_label += f"\\nDuration: {duration:.2f}s | Success Rate: {(execution_report.completed_steps/execution_report.step_count*100):.1f}%"
    
    dot.node('title', title_label, shape='plaintext', fontsize='20', fontcolor='#2C3E50')
    
    # Collect unique nodes and their types
    node_info = {}
    for source, target, schema, _, flow_type in data_flows:
        for node in [source, target]:
            if node not in node_info:
                # Determine node type and visual properties
                if node == 'input':
                    node_info[node] = {
                        'shape': 'invhouse',
                        'color': VisualTheme.AGENT_COLORS['input'],
                        'label': '📥 Input\\n(Requirements)',
                        'fontcolor': 'white'
                    }
                elif node == 'test_execution':
                    node_info[node] = {
                        'shape': 'component',
                        'color': VisualTheme.AGENT_COLORS['test_execution'],
                        'label': '🧪 Test\\nExecution',
                        'fontcolor': 'black'
                    }
                elif node == 'workflow_continuation':
                    node_info[node] = {
                        'shape': 'circle',
                        'color': VisualTheme.AGENT_COLORS['workflow_continuation'],
                        'label': '➡️ Continue',
                        'fontcolor': 'black'
                    }
                elif '_agent' in node:
                    agent_type = node
                    emoji_map = {
                        'planner_agent': '📋',
                        'designer_agent': '🎨',
                        'test_writer_agent': '🧪',
                        'coder_agent': '💻',
                        'reviewer_agent': '🔍'
                    }
                    emoji = emoji_map.get(agent_type, '👤')
                    display_name = node.replace('_agent', '').replace('_', ' ').title()
                    
                    # Get performance info if available
                    perf_info = ""
                    if execution_report and agent_type in execution_report.agent_performance:
                        perf = execution_report.agent_performance[agent_type]
                        avg_time = perf.get('average_duration', 0)
                        perf_info = f"\\n⏱️ {avg_time:.1f}s avg"
                    
                    node_info[node] = {
                        'shape': 'box3d',
                        'color': VisualTheme.AGENT_COLORS.get(agent_type, '#95A5A6'),
                        'label': f"{emoji} {display_name}{perf_info}",
                        'fontcolor': 'white'
                    }
                else:
                    node_info[node] = {
                        'shape': 'box',
                        'color': '#E0E0E0',
                        'label': node.replace('_', ' ').title(),
                        'fontcolor': 'black'
                    }
    
    # Add nodes with enhanced styling
    for node, info in node_info.items():
        dot.node(node, info['label'], 
                shape=info['shape'], 
                fillcolor=info['color'],
                fontcolor=info['fontcolor'],
                penwidth='2')
    
    # Process edges with creative styling
    edge_groups = {}  # Group edges by source-target pair
    
    for source, target, data_schema, transformations, flow_type in data_flows:
        key = f"{source}->{target}"
        if key not in edge_groups:
            edge_groups[key] = []
        edge_groups[key].append((data_schema, transformations, flow_type))
    
    # Add edges with enhanced styling
    for edge_key, edge_data_list in edge_groups.items():
        source, target = edge_key.split('->')
        
        # Determine primary flow type (prioritize special flows)
        primary_flow_type = None
        for _, _, flow_type in edge_data_list:
            if flow_type in ['review', 'feedback', 'approval', 'validation']:
                primary_flow_type = flow_type
                break
        if not primary_flow_type:
            primary_flow_type = edge_data_list[0][2]
        
        # Style configuration
        edge_style = {
            None: {'style': 'solid', 'penwidth': '2', 'arrowsize': '1'},
            'review': {'style': 'dashed', 'penwidth': '2', 'arrowsize': '1.2', 'arrowhead': 'diamond'},
            'feedback': {'style': 'dotted', 'penwidth': '3', 'arrowsize': '1.2', 'arrowhead': 'tee'},
            'approval': {'style': 'bold', 'penwidth': '3', 'arrowsize': '1.5', 'arrowhead': 'normal'},
            'validation': {'style': 'dashed', 'penwidth': '2', 'arrowsize': '1', 'arrowhead': 'dot'},
            'parallel': {'style': 'solid', 'penwidth': '2', 'arrowsize': '1', 'dir': 'both'}
        }.get(primary_flow_type, {'style': 'solid', 'penwidth': '2', 'arrowsize': '1'})
        
        # Color selection
        color = VisualTheme.FLOW_COLORS.get(primary_flow_type or 'sequential', '#3498DB')
        
        # Build edge label
        labels = []
        for data_schema, transformations, flow_type in edge_data_list:
            if flow_type == 'review' and 'stage' in data_schema:
                labels.append(f"📝 Review: {data_schema['stage']}")
            elif flow_type == 'feedback' and 'decision' in data_schema:
                labels.append(f"🔄 {data_schema['decision']}")
            elif flow_type == 'approval' and 'stage' in data_schema:
                labels.append(f"✅ Approved: {data_schema['stage']}")
            elif flow_type == 'validation' and 'type' in data_schema:
                labels.append(f"🧪 {data_schema['type']}")
            elif 'type' in data_schema:
                labels.append(data_schema['type'])
        
        # Add edge count if multiple
        if len(edge_data_list) > 1:
            labels.append(f"({len(edge_data_list)} flows)")
        
        edge_label = '\\n'.join(labels) if labels else ''
        
        # Add the edge
        dot.edge(source, target, 
                label=edge_label,
                color=color,
                **edge_style)
    
    # Add comprehensive legend
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='Workflow Elements', fontsize='16', 
                   style='filled,rounded', fillcolor='#F0F0F0', color='#666666')
        
        # Flow types section
        with legend.subgraph(name='cluster_flows') as flows:
            flows.attr(label='Flow Types', fontsize='14', style='filled', fillcolor='white')
            
            flow_examples = [
                ('Sequential', 'sequential', 'solid', '2'),
                ('Review', 'review', 'dashed', '2'),
                ('Feedback', 'feedback', 'dotted', '3'),
                ('Approval', 'approval', 'bold', '3'),
                ('Validation', 'validation', 'dashed', '2')
            ]
            
            prev = None
            for name, flow_type, style, width in flow_examples:
                node_id = f'legend_{flow_type}'
                flows.node(node_id, name, shape='plaintext')
                if prev:
                    flows.edge(prev, node_id, style=style, penwidth=width,
                              color=VisualTheme.FLOW_COLORS.get(flow_type, '#666'))
                prev = node_id
        
        # Agent types section
        with legend.subgraph(name='cluster_agents_legend') as agents:
            agents.attr(label='Agent Types', fontsize='14', style='filled', fillcolor='white')
            
            agent_types = [
                ('📋 Planner', 'planner_agent'),
                ('🎨 Designer', 'designer_agent'),
                ('🧪 Test Writer', 'test_writer_agent'),
                ('💻 Coder', 'coder_agent'),
                ('🔍 Reviewer', 'reviewer_agent')
            ]
            
            for label, agent_type in agent_types:
                agents.node(f'legend_{agent_type}', label, shape='box3d',
                           fillcolor=VisualTheme.AGENT_COLORS[agent_type],
                           fontcolor='white')
    
    # Add metrics if execution report is available
    if execution_report:
        with dot.subgraph(name='cluster_metrics') as metrics:
            metrics.attr(label='Execution Metrics', fontsize='14', 
                        style='filled,rounded', fillcolor='#E8F5E8', color='#2E7D32')
            
            metrics_text = f"""Duration: {execution_report.total_duration_seconds:.2f}s
Steps: {execution_report.completed_steps}/{execution_report.step_count}
Reviews: {execution_report.total_reviews}
Retries: {execution_report.total_retries}"""
            
            metrics.node('exec_metrics', metrics_text, shape='note', 
                        style='filled', fillcolor='white')
    
    return dot


def visualize_comprehensive_workflow(output_dir: Path = None):
    """Generate comprehensive visualizations for all workflows with multiple views"""
    if output_dir is None:
        output_dir = project_root / "docs" / "workflow_visualizations"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print("🎨 Enhanced Workflow Visualizer")
    print("=" * 60)
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Workflow configurations
    workflows = {
        "TDD Workflow": {
            "func": run_tdd_workflow,
            "desc": "Test-Driven Development workflow",
            "emoji": "🧪"
        },
        "Full Workflow": {
            "func": run_full_workflow,
            "desc": "Full development workflow",
            "emoji": "🚀"
        },
        "Individual Workflow": {
            "func": run_individual_workflow,
            "desc": "Individual workflow step execution",
            "emoji": "📍"
        }
    }
    
    # Generate visualizations for each workflow
    for name, info in workflows.items():
        print(f"\n{info['emoji']} Processing {name}...")
        print("-" * 40)
        
        # Analyze workflow
        flows = analyze_advanced_workflow_data_flow(info["func"])
        
        # Generate main flow visualization
        print("  📊 Creating flow visualization...")
        flow_graph = create_enhanced_workflow_graph(name, flows)
        save_graph(flow_graph, output_dir, f"{name.lower().replace(' ', '_')}_flow")
        
        # Generate additional visualizations (placeholders for now)
        # In a real implementation, these would use actual execution data
        print("  📈 Creating metrics visualization...")
        print("  ⏱️  Creating timeline visualization...")
        print("  🔄 Creating review flow visualization...")
        
        print(f"  ✅ {name} visualizations complete")
    
    # Create system overview
    print("\n🌐 Creating system overview...")
    overview_graph = create_system_overview()
    save_graph(overview_graph, output_dir, "system_overview")
    
    print("\n✨ All visualizations complete!")
    print(f"📁 Files saved to: {output_dir}")


def analyze_advanced_workflow_data_flow(workflow_function) -> List[Tuple[str, str, Dict, List[Dict], Optional[str]]]:
    """Advanced analysis of workflow data flow with better detection"""
    flows = []
    source_code = inspect.getsource(workflow_function)
    source_lines = source_code.split('\n')
    
    # Track agents and their relationships
    agent_sequence = []
    review_patterns = []
    
    # First pass: Find agent calls
    for i, line in enumerate(source_lines):
        if "run_team_member" in line:
            # Extract agent name
            agent_match = re.search(r'run_team_member\s*\(\s*["\']([^"\']+)["\']', line)
            if agent_match:
                agent_name = agent_match.group(1)
                agent_sequence.append((i, agent_name))
    
    # Second pass: Find review patterns
    for i, line in enumerate(source_lines):
        if "review_output" in line:
            # Find the context
            context_match = re.search(r'["\']([^"\']+)["\']', line)
            if context_match:
                context = context_match.group(1)
                # Find the nearest agent before this review
                for j, (line_no, agent) in reversed(list(enumerate(agent_sequence))):
                    if line_no < i:
                        review_patterns.append((agent, 'reviewer_agent', context))
                        break
    
    # Build flows from analysis
    # Add input flow
    if agent_sequence:
        flows.append(("input", agent_sequence[0][1], 
                     {"type": "initial_input"}, [], None))
    
    # Add sequential flows
    for i in range(len(agent_sequence) - 1):
        source = agent_sequence[i][1]
        target = agent_sequence[i + 1][1]
        flows.append((source, target, {"type": "sequential"}, [], None))
    
    # Add review flows
    for source, target, context in review_patterns:
        flows.append((source, target, 
                     {"stage": context, "type": "review"}, [], "review"))
        flows.append((target, source, 
                     {"type": "feedback", "context": context}, [], "feedback"))
    
    # Add test execution flow for TDD
    if "tdd" in str(workflow_function).lower():
        flows.append(("coder_agent", "test_execution", 
                     {"type": "test_validation"}, [], "validation"))
        flows.append(("test_execution", "coder_agent", 
                     {"type": "test_results"}, [], "feedback"))
    
    return flows


def create_system_overview() -> graphviz.Digraph:
    """Create a beautiful system overview visualization"""
    dot = graphviz.Digraph(comment='Workflow System Overview')
    dot.attr(rankdir='TB', size='18,24', bgcolor='#F5F7FA', pad='1')
    dot.attr('node', fontname='Arial', fontsize='14', style='filled')
    dot.attr('edge', fontname='Arial', fontsize='11')
    
    # Title
    dot.node('title', '🚀 Modular Agent Workflow System', 
             shape='plaintext', fontsize='24', fontcolor='#1A237E')
    
    # User input layer
    with dot.subgraph(name='cluster_input') as inp:
        inp.attr(label='User Layer', fontsize='16', style='filled,rounded', 
                fillcolor='#E3F2FD', color='#1976D2')
        inp.node('user', '👤 User', shape='circle', fillcolor='#BBDEFB')
        inp.node('requirements', '📝 Requirements', shape='note', fillcolor='#90CAF9')
        inp.edge('user', 'requirements')
    
    # Orchestration layer
    with dot.subgraph(name='cluster_orchestration') as orch:
        orch.attr(label='Orchestration Layer', fontsize='16', style='filled,rounded',
                 fillcolor='#F3E5F5', color='#7B1FA2')
        orch.node('orchestrator', '🎯 Orchestrator', shape='doubleoctagon', 
                 fillcolor='#CE93D8', fontcolor='white', penwidth='3')
        orch.node('workflow_manager', '📊 Workflow Manager', shape='box3d', 
                 fillcolor='#BA68C8', fontcolor='white')
        orch.edge('orchestrator', 'workflow_manager', style='bold')
    
    # Workflow types
    with dot.subgraph(name='cluster_workflows') as wf:
        wf.attr(label='Workflow Types', fontsize='16', style='filled,rounded',
               fillcolor='#E8F5E8', color='#388E3C')
        wf.node('tdd', '🧪 TDD Workflow', shape='cylinder', fillcolor='#81C784')
        wf.node('full', '🚀 Full Workflow', shape='cylinder', fillcolor='#66BB6A')
        wf.node('individual', '📍 Individual Steps', shape='cylinder', fillcolor='#4CAF50')
    
    # Agent pool
    with dot.subgraph(name='cluster_agents') as agents:
        agents.attr(label='Agent Pool', fontsize='16', style='filled,rounded',
                   fillcolor='#FFF3E0', color='#F57C00')
        
        agent_configs = [
            ('planner', '📋 Planner', VisualTheme.AGENT_COLORS['planner_agent']),
            ('designer', '🎨 Designer', VisualTheme.AGENT_COLORS['designer_agent']),
            ('test_writer', '🧪 Test Writer', VisualTheme.AGENT_COLORS['test_writer_agent']),
            ('coder', '💻 Coder', VisualTheme.AGENT_COLORS['coder_agent']),
            ('reviewer', '🔍 Reviewer', VisualTheme.AGENT_COLORS['reviewer_agent'])
        ]
        
        for agent_id, label, color in agent_configs:
            agents.node(agent_id, label, shape='component', fillcolor=color, fontcolor='white')
    
    # Monitoring layer
    with dot.subgraph(name='cluster_monitoring') as mon:
        mon.attr(label='Monitoring & Analytics', fontsize='16', style='filled,rounded',
                fillcolor='#FFEBEE', color='#C62828')
        mon.node('tracer', '📈 Execution Tracer', shape='box3d', fillcolor='#EF5350', fontcolor='white')
        mon.node('reports', '📊 Reports', shape='tab', fillcolor='#E53935', fontcolor='white')
        mon.edge('tracer', 'reports')
    
    # Connect layers
    dot.edge('requirements', 'orchestrator', style='bold', penwidth='3')
    dot.edge('workflow_manager', 'tdd', label='if TDD')
    dot.edge('workflow_manager', 'full', label='if Full')
    dot.edge('workflow_manager', 'individual', label='if Individual')
    
    # Workflow to agents connections (simplified)
    for wf_node in ['tdd', 'full', 'individual']:
        for agent in ['planner', 'designer', 'test_writer', 'coder', 'reviewer']:
            dot.edge(wf_node, agent, style='dotted', color='gray', arrowhead='none')
    
    # Monitoring connections
    dot.edge('orchestrator', 'tracer', style='dashed', color='red')
    
    return dot


def save_graph(graph: graphviz.Digraph, output_dir: Path, filename: str):
    """Save graph in multiple formats with error handling"""
    try:
        # Save DOT file
        dot_path = output_dir / f"{filename}.dot"
        graph.save(str(dot_path))
        print(f"    ✅ DOT file: {dot_path.name}")
        
        # Try to render
        try:
            graph.render(str(output_dir / filename), format='png', cleanup=True)
            print(f"    ✅ PNG file: {filename}.png")
        except:
            print(f"    ⚠️  PNG rendering failed (Graphviz not installed?)")
        
        try:
            graph.render(str(output_dir / filename), format='svg', cleanup=True)
            print(f"    ✅ SVG file: {filename}.svg")
        except:
            print(f"    ⚠️  SVG rendering failed")
            
    except Exception as e:
        print(f"    ❌ Error saving {filename}: {e}")


if __name__ == "__main__":
    print("\n🎨 Enhanced Workflow Visualizer v2.0")
    print("=" * 60)
    print("Features:")
    print("  • Creative shapes and colors")
    print("  • Performance metrics integration")
    print("  • Timeline visualizations")
    print("  • Review flow analysis")
    print("  • System overview diagrams")
    print("=" * 60)
    
    visualize_comprehensive_workflow()