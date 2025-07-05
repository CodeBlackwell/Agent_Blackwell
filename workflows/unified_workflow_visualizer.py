"""
Unified Workflow Visualizer

A comprehensive visualization system that combines static Graphviz visualizations
with interactive JSON exports. This unified approach provides multiple visualization
modes including flow graphs, metrics dashboards, timeline views, and 3D representations.

Features:
- Compatible with current architecture (run_team_member_with_tracking)
- Multiple visualization modes (static and interactive)
- Performance metrics integration
- Real-time monitoring support
- Advanced visual themes and styling
- Export to multiple formats (PNG, SVG, PDF, HTML, JSON)
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
from dataclasses import dataclass, field
from enum import Enum
import hashlib

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

# Import shared data models (avoid circular imports)
from shared.data_models import (
    TeamMember, WorkflowStep, CodingTeamInput, TeamMemberResult
)

# Import monitoring components
from workflows.monitoring import (
    WorkflowExecutionTracer, WorkflowExecutionReport, 
    StepStatus, ReviewDecision
)


# ============================================================================
# CONFIGURATION AND THEMES
# ============================================================================

class VisualizationMode(Enum):
    """Available visualization modes"""
    FLOW_GRAPH = "flow_graph"
    METRICS_DASHBOARD = "metrics"
    TIMELINE = "timeline"
    REVIEW_FLOW = "review_flow"
    SYSTEM_OVERVIEW = "system_overview"
    DEPENDENCY_GRAPH = "dependencies"
    HEAT_MAP = "heat_map"
    THREE_D = "3d"
    INTERACTIVE = "interactive"
    ALL = "all"


@dataclass
class VisualizationConfig:
    """Configuration for the unified visualizer"""
    output_dir: Path = field(default_factory=lambda: Path("docs/workflow_visualizations"))
    output_formats: List[str] = field(default_factory=lambda: ["png", "svg", "pdf", "json"])
    theme: str = "modern"  # modern, classic, dark, light
    show_metrics: bool = True
    show_transformations: bool = True
    show_schemas: bool = True
    include_timing: bool = True
    include_legends: bool = True
    resolution: int = 300  # DPI for raster outputs
    max_label_length: int = 50
    enable_3d: bool = False
    enable_animations: bool = False
    batch_process: bool = True
    

@dataclass 
class VisualTheme:
    """Visual theme configuration"""
    name: str
    background_color: str
    node_colors: Dict[str, str]
    edge_colors: Dict[str, str]
    status_colors: Dict[str, str]
    font_family: str = "Arial"
    font_size: int = 12
    
    @classmethod
    def modern_theme(cls) -> 'VisualTheme':
        """Modern vibrant theme"""
        return cls(
            name="modern",
            background_color="#F8F9FA",
            node_colors={
                'planner_agent': '#FF6B6B',      # Coral red
                'designer_agent': '#4ECDC4',     # Turquoise
                'test_writer_agent': '#45B7D1',  # Sky blue
                'coder_agent': '#96CEB4',        # Mint green
                'reviewer_agent': '#FECA57',     # Golden yellow
                'input': '#DDA0DD',              # Plum
                'output': '#98D8C8',             # Seafoam
                'test_execution': '#F7DC6F',     # Soft yellow
                'workflow_continuation': '#E8E8E8',  # Light gray
                'incremental_coder': '#7B68EE',  # Medium slate blue
                'error': '#FF4757',              # Error red
                'success': '#2ED573',            # Success green
            },
            edge_colors={
                'sequential': '#3498DB',         # Bright blue
                'review': '#E74C3C',            # Red
                'feedback': '#F39C12',          # Orange
                'approval': '#27AE60',          # Green
                'validation': '#9B59B6',        # Purple
                'retry': '#E67E22',             # Dark orange
                'error': '#C0392B',             # Dark red
                'parallel': '#16A085',          # Teal
                'data_transform': '#34495E',    # Dark gray
            },
            status_colors={
                'pending': '#95A5A6',
                'running': '#3498DB',
                'completed': '#2ECC71',
                'failed': '#E74C3C',
                'retrying': '#F39C12',
                'skipped': '#BDC3C7'
            }
        )
    
    @classmethod
    def dark_theme(cls) -> 'VisualTheme':
        """Dark theme for better contrast"""
        return cls(
            name="dark",
            background_color="#1A1A2E",
            node_colors={
                'planner_agent': '#F94144',
                'designer_agent': '#F3722C',
                'test_writer_agent': '#F8961E',
                'coder_agent': '#F9C74F',
                'reviewer_agent': '#90BE6D',
                'input': '#43AA8B',
                'output': '#577590',
                'test_execution': '#277DA1',
                'workflow_continuation': '#4D5057',
                'incremental_coder': '#8B5CF6',
                'error': '#EF4444',
                'success': '#10B981',
            },
            edge_colors={
                'sequential': '#60A5FA',
                'review': '#F87171',
                'feedback': '#FB923C',
                'approval': '#34D399',
                'validation': '#A78BFA',
                'retry': '#F59E0B',
                'error': '#DC2626',
                'parallel': '#14B8A6',
                'data_transform': '#6B7280',
            },
            status_colors={
                'pending': '#6B7280',
                'running': '#3B82F6',
                'completed': '#10B981',
                'failed': '#EF4444',
                'retrying': '#F59E0B',
                'skipped': '#9CA3AF'
            }
        )
    
    def get_gradient_color(self, value: float, min_val: float = 0, max_val: float = 1) -> str:
        """Generate a gradient color based on a value (for performance metrics)"""
        # Normalize value to 0-1 range
        normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
        # Use HSV color space for smooth gradients (green to red)
        hue = 0.3 * (1 - normalized)  # 0.3 = green, 0 = red
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"


# ============================================================================
# WORKFLOW ANALYSIS ENGINE
# ============================================================================

class WorkflowAnalyzer:
    """Core workflow analysis engine adapted from V3 for current architecture"""
    
    # Workflow module mapping
    WORKFLOW_MAPPING = {
        "TDD Workflow": ("workflows.tdd.tdd_workflow", "execute_tdd_workflow"),
        "Full Workflow": ("workflows.full.full_workflow", "execute_full_workflow"),
        "Individual Workflow": ("workflows.individual.individual_workflow", "execute_individual_workflow"),
        "Incremental Workflow": ("workflows.incremental.incremental_workflow", "execute_incremental_workflow"),
    }
    
    def __init__(self):
        self.agent_outputs = {}
        self.review_flows = {}
        
    def analyze_workflow(self, workflow_function) -> List[Tuple[str, str, Dict, List[Dict], Optional[str]]]:
        """
        Analyze a workflow function to determine the data flow between agents.
        Returns a list of (source, target, data_schema, transformations, flow_type) tuples.
        """
        # Reset state
        self.agent_outputs = {}
        self.review_flows = {}
        
        # Handle special case for individual workflow
        if workflow_function.__name__ == 'run_individual_workflow':
            return self._analyze_individual_workflow(workflow_function)
            
        # Get source code and analyze
        source_code = inspect.getsource(workflow_function)
        return self._analyze_standard_workflow(source_code)
    
    def _analyze_individual_workflow(self, workflow_function):
        """Special analyzer for individual workflow with dictionary-based dispatch"""
        source_code = inspect.getsource(workflow_function)
        tree = ast.parse(source_code)
        flows = []

        class Visitor(ast.NodeVisitor):
            def visit_Dict(self, node):
                # Find the agent_map dictionary
                if len(node.keys) > 3:  # Heuristic to find the agent_map
                    for key, value in zip(node.keys, node.values):
                        if isinstance(key, ast.Constant) and isinstance(value, ast.Tuple):
                            step_name = key.value
                            agent_name_node = value.elts[0]
                            if isinstance(agent_name_node, ast.Constant):
                                agent_name = agent_name_node.value
                                flows.append(("input", agent_name, 
                                            {"type": f"individual_step: {step_name}"}, [], None))
                                flows.append((agent_name, "output", 
                                            {"type": "result"}, [], None))
                self.generic_visit(node)

        Visitor().visit(tree)
        return self._deduplicate_flows(flows)
    
    def _analyze_standard_workflow(self, source_code: str):
        """Analyze standard workflows with sequential and review patterns"""
        flows = []
        source_lines = self._preprocess_source_lines(source_code)
        
        # Extract transformations
        transformations = self._extract_data_transformations(source_code)
        
        # Multiple analysis passes
        self._find_agent_calls(source_lines)
        flows.extend(self._find_review_flows(source_lines))
        flows.extend(self._find_test_flows(source_lines))
        flows.extend(self._find_sequential_flows(source_lines))
        
        return self._deduplicate_flows(flows)
    
    def _preprocess_source_lines(self, source_code: str) -> List[str]:
        """Pre-process source code to handle multi-line statements"""
        source_lines = source_code.split('\n')
        condensed_lines = []
        buffer = ""
        in_statement = False
        
        for line in source_lines:
            if not in_statement:
                if any(pattern in line for pattern in ["run_team_member_with_tracking(", "review_output("]):
                    buffer = line.strip()
                    if buffer.count('(') > buffer.count(')'):
                        in_statement = True
                    else:
                        condensed_lines.append(buffer)
                        buffer = ""
                else:
                    condensed_lines.append(line)
            else:
                buffer += " " + line.strip()
                if buffer.count('(') <= buffer.count(')'):
                    condensed_lines.append(buffer)
                    buffer = ""
                    in_statement = False
                    
        return condensed_lines
    
    def _extract_data_transformations(self, source_code: str) -> List[Dict[str, Any]]:
        """Extract data transformation details from function source code"""
        transformations = []
        assignment_pattern = re.compile(r'(\w+)\s*=\s*([^#\n]+)')
        matches = assignment_pattern.findall(source_code)
        
        for var_name, expr in matches:
            if 'results' in expr or 'input' in expr:
                transformations.append({
                    'target': var_name,
                    'source': expr.strip(),
                    'type': 'assignment'
                })
        
        return transformations
    
    def _find_agent_calls(self, source_lines: List[str]):
        """Find all agent calls and track their outputs"""
        for i, line in enumerate(source_lines):
            if "run_team_member_with_tracking" in line and "await" in line:
                agent_match = re.search(r'run_team_member_with_tracking\(["\']([^"\']+)["\']', line)
                result_match = re.search(r'(\w+)\s*=\s*await\s+run_team_member_with_tracking', line)
                
                if agent_match and result_match:
                    agent_name = agent_match.group(1)
                    result_var = result_match.group(1)
                    self.agent_outputs[result_var] = agent_name
                    
                    # Look for output extraction
                    for j in range(i+1, min(len(source_lines), i+10)):
                        output_line = source_lines[j]
                        if f"{result_var}[0]" in output_line or f"str({result_var}" in output_line:
                            output_match = re.search(rf'(\w+)\s*=\s*str\({result_var}', output_line)
                            if output_match:
                                output_var = output_match.group(1)
                                self.agent_outputs[output_var] = agent_name
                            break
    
    def _find_review_flows(self, source_lines: List[str]) -> List[Tuple]:
        """Find review flows and approval/feedback patterns"""
        flows = []
        
        for i, line in enumerate(source_lines):
            if "review_output(" in line:
                review_match = re.search(r'review_output\(([^,]+),\s*["\']([^"\']+)["\']', line)
                if review_match:
                    reviewed_var = review_match.group(1).strip()
                    stage = review_match.group(2)
                    
                    source_agent = self.agent_outputs.get(reviewed_var, "unknown")
                    if source_agent != "unknown":
                        flows.append((source_agent, "reviewer_agent", 
                                    {"stage": stage, "output": reviewed_var}, 
                                    [], "review"))
                        
                        # Look for approval/feedback handling
                        flows.extend(self._find_review_decisions(source_lines, i, source_agent, stage))
        
        return flows
    
    def _find_review_decisions(self, source_lines: List[str], start_idx: int, 
                               source_agent: str, stage: str) -> List[Tuple]:
        """Find approval and feedback flows after review"""
        flows = []
        
        for j in range(start_idx + 1, min(len(source_lines), start_idx + 20)):
            line = source_lines[j]
            
            if "if approved:" in line:
                # Find approval handling
                for k in range(j + 1, min(len(source_lines), j + 15)):
                    next_line = source_lines[k]
                    if "results.append" in next_line:
                        flows.append(("reviewer_agent", "workflow_continuation",
                                    {"decision": "approved", "stage": stage},
                                    [], "approval"))
                        break
                    elif "run_team_member_with_tracking" in next_line:
                        next_agent_match = re.search(
                            r'run_team_member_with_tracking\(["\']([^"\']+)["\']', 
                            next_line
                        )
                        if next_agent_match:
                            next_agent = next_agent_match.group(1)
                            flows.append(("reviewer_agent", next_agent,
                                        {"decision": "approved", "stage": stage},
                                        [], "approval"))
                        break
            
            elif any(pattern in line for pattern in ["else:", "need revision", "feedback"]):
                # Find feedback flow
                flows.append(("reviewer_agent", source_agent,
                            {"decision": "revision_needed", "stage": stage},
                            [], "feedback"))
                break
        
        return flows
    
    def _find_test_flows(self, source_lines: List[str]) -> List[Tuple]:
        """Find test execution and retry flows"""
        flows = []
        
        for i, line in enumerate(source_lines):
            if "while not all_tests_passed" in line or "retry_state" in line:
                for j in range(i, min(len(source_lines), i + 50)):
                    retry_line = source_lines[j]
                    
                    if "execute_tests(" in retry_line:
                        flows.append(("coder_agent", "test_execution",
                                    {"type": "test_validation"}, [], "validation"))
                        flows.append(("test_execution", "coder_agent",
                                    {"type": "test_results"}, [], "feedback"))
                    
                    elif all(p in retry_line for p in ["run_team_member_with_tracking", 
                                                       "reviewer_agent", "test failures"]):
                        flows.append(("test_execution", "reviewer_agent",
                                    {"type": "test_failure_analysis"}, [], "review"))
                        flows.append(("reviewer_agent", "coder_agent",
                                    {"type": "test_failure_feedback"}, [], "feedback"))
        
        return flows
    
    def _find_sequential_flows(self, source_lines: List[str]) -> List[Tuple]:
        """Find regular sequential flows between agents"""
        flows = []
        agent_sequence = []
        
        for line in source_lines:
            if "run_team_member_with_tracking" in line and "await" in line:
                agent_match = re.search(r'run_team_member_with_tracking\(["\']([^"\']+)["\']', line)
                if agent_match:
                    agent_name = agent_match.group(1)
                    if agent_name != "reviewer_agent":  # Skip reviewer calls
                        agent_sequence.append(agent_name)
        
        # Add input flow
        if agent_sequence:
            flows.append(("input", agent_sequence[0], 
                        {"type": "initial_input"}, [], None))
        
        # Add sequential flows
        for i in range(len(agent_sequence) - 1):
            flows.append((agent_sequence[i], agent_sequence[i + 1], 
                        {"type": "sequential"}, [], None))
        
        return flows
    
    def _deduplicate_flows(self, flows: List[Tuple]) -> List[Tuple]:
        """Remove duplicate flows"""
        unique_flows = []
        for flow in flows:
            if flow not in unique_flows:
                unique_flows.append(flow)
        return unique_flows


# ============================================================================
# MAIN UNIFIED VISUALIZER CLASS
# ============================================================================

class UnifiedWorkflowVisualizer:
    """Main class for unified workflow visualization"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.analyzer = WorkflowAnalyzer()
        self.theme = self._load_theme()
        self._ensure_output_dir()
        
    def _load_theme(self) -> VisualTheme:
        """Load the specified theme"""
        theme_map = {
            "modern": VisualTheme.modern_theme(),
            "dark": VisualTheme.dark_theme(),
            # Add more themes as needed
        }
        return theme_map.get(self.config.theme, VisualTheme.modern_theme())
    
    def _ensure_output_dir(self):
        """Ensure output directory exists"""
        self.config.output_dir.mkdir(exist_ok=True, parents=True)
    
    def visualize_workflow(self, workflow_name: str, workflow_function, 
                          mode: VisualizationMode = VisualizationMode.ALL,
                          execution_report: Optional[WorkflowExecutionReport] = None):
        """
        Visualize a workflow in the specified mode(s)
        
        Args:
            workflow_name: Name of the workflow
            workflow_function: The workflow function to analyze
            mode: Visualization mode(s) to generate
            execution_report: Optional execution report for metrics
        """
        print(f"\n🎨 Visualizing {workflow_name}...")
        
        # Analyze workflow
        data_flows = self.analyzer.analyze_workflow(workflow_function)
        
        # Generate visualizations based on mode
        if mode == VisualizationMode.ALL:
            self._generate_all_visualizations(workflow_name, data_flows, execution_report)
        else:
            self._generate_single_visualization(workflow_name, data_flows, mode, execution_report)
    
    def visualize_all_workflows(self, mode: VisualizationMode = VisualizationMode.ALL):
        """Visualize all available workflows"""
        print("🚀 Starting unified workflow visualization...")
        print(f"📁 Output directory: {self.config.output_dir}")
        print(f"🎨 Theme: {self.theme.name}")
        print("=" * 60)
        
        all_workflow_data = {}
        
        for name, (module_name, func_name) in WorkflowAnalyzer.WORKFLOW_MAPPING.items():
            try:
                print(f"\n📊 Processing {name}...")
                module = importlib.import_module(module_name)
                func = getattr(module, func_name)
                
                # Analyze workflow
                data_flows = self.analyzer.analyze_workflow(func)
                all_workflow_data[name] = data_flows
                
                # Generate visualizations
                self.visualize_workflow(name, func, mode)
                print(f"✅ {name} visualization complete")
                
            except Exception as e:
                print(f"❌ Failed to process {name}: {e}")
        
        # Generate system overview if requested
        if mode in [VisualizationMode.ALL, VisualizationMode.SYSTEM_OVERVIEW]:
            self._generate_system_overview(all_workflow_data)
        
        # Export interactive data if requested
        if mode in [VisualizationMode.ALL, VisualizationMode.INTERACTIVE]:
            self._export_interactive_data(all_workflow_data)
        
        print("\n✨ All visualizations complete!")
        print(f"📁 Files saved to: {self.config.output_dir}")
    
    def _generate_all_visualizations(self, workflow_name: str, data_flows: List[Tuple],
                                   execution_report: Optional[WorkflowExecutionReport] = None):
        """Generate all visualization types for a workflow"""
        # Flow graph
        self._generate_flow_graph(workflow_name, data_flows, execution_report)
        
        # Metrics dashboard (if execution report available)
        if execution_report:
            self._generate_metrics_dashboard(workflow_name, execution_report)
            self._generate_timeline_view(workflow_name, execution_report)
            self._generate_review_flow(workflow_name, execution_report)
        
        # Dependency graph
        self._generate_dependency_graph(workflow_name, data_flows)
        
        # Export JSON data
        self._export_workflow_json(workflow_name, data_flows, execution_report)
    
    def _generate_single_visualization(self, workflow_name: str, data_flows: List[Tuple],
                                     mode: VisualizationMode,
                                     execution_report: Optional[WorkflowExecutionReport] = None):
        """Generate a single visualization type"""
        mode_handlers = {
            VisualizationMode.FLOW_GRAPH: lambda: self._generate_flow_graph(
                workflow_name, data_flows, execution_report),
            VisualizationMode.METRICS_DASHBOARD: lambda: self._generate_metrics_dashboard(
                workflow_name, execution_report) if execution_report else None,
            VisualizationMode.TIMELINE: lambda: self._generate_timeline_view(
                workflow_name, execution_report) if execution_report else None,
            VisualizationMode.REVIEW_FLOW: lambda: self._generate_review_flow(
                workflow_name, execution_report) if execution_report else None,
            VisualizationMode.DEPENDENCY_GRAPH: lambda: self._generate_dependency_graph(
                workflow_name, data_flows),
            VisualizationMode.INTERACTIVE: lambda: self._export_workflow_json(
                workflow_name, data_flows, execution_report),
        }
        
        handler = mode_handlers.get(mode)
        if handler:
            handler()
        else:
            print(f"⚠️  Visualization mode {mode} not yet implemented")
    
    # Placeholder methods for each visualization type
    # These will be implemented in the next steps
    
    def _generate_flow_graph(self, workflow_name: str, data_flows: List[Tuple],
                           execution_report: Optional[WorkflowExecutionReport] = None):
        """Generate the main workflow flow graph"""
        print(f"  📊 Generating flow graph for {workflow_name}...")
        
        dot = graphviz.Digraph(comment=f'{workflow_name} Flow')
        dot.attr(rankdir='TB', size='16,24', bgcolor=self.theme.background_color, pad='0.5')
        dot.attr('node', fontname=self.theme.font_family, fontsize=str(self.theme.font_size), 
                style='filled,rounded')
        dot.attr('edge', fontname=self.theme.font_family, fontsize=str(self.theme.font_size - 2))
        
        # Add title
        title_label = f"{workflow_name} Workflow"
        if execution_report and self.config.show_metrics:
            duration = execution_report.total_duration_seconds or 0
            success_rate = (execution_report.completed_steps / execution_report.step_count * 100) if execution_report.step_count > 0 else 0
            title_label += f"\\nDuration: {duration:.2f}s | Success Rate: {success_rate:.1f}%"
        
        dot.node('title', title_label, shape='plaintext', fontsize='20', 
                fontcolor='#2C3E50' if self.theme.name != 'dark' else '#F3F4F6')
        
        # Collect unique nodes
        node_info = {}
        edge_groups = {}
        
        for source, target, schema, transformations, flow_type in data_flows:
            # Process nodes
            for node in [source, target]:
                if node and node not in node_info:
                    node_info[node] = self._get_node_info(node, execution_report)
            
            # Group edges
            if target:
                key = f"{source}->{target}"
                if key not in edge_groups:
                    edge_groups[key] = []
                edge_groups[key].append((schema, transformations, flow_type))
        
        # Add nodes
        for node, info in node_info.items():
            dot.node(node, **info)
        
        # Add edges
        for edge_key, edge_data_list in edge_groups.items():
            source, target = edge_key.split('->')
            self._add_edge(dot, source, target, edge_data_list)
        
        # Add legend if configured
        if self.config.include_legends:
            self._add_flow_legend(dot)
        
        # Save and render
        self._save_graph(dot, workflow_name, "flow")
    
    def _generate_metrics_dashboard(self, workflow_name: str, 
                                  execution_report: WorkflowExecutionReport):
        """Generate metrics dashboard visualization"""
        print(f"  📈 Generating metrics dashboard for {workflow_name}...")
        
        dot = graphviz.Digraph(comment=f'{workflow_name} Metrics')
        dot.attr(rankdir='TB', size='14,20', bgcolor=self.theme.background_color)
        dot.attr('node', fontname=self.theme.font_family, fontsize=str(self.theme.font_size))
        dot.attr('edge', fontname=self.theme.font_family, fontsize=str(self.theme.font_size - 2))
        
        # Title
        dot.node('title', f'Workflow Metrics: {execution_report.workflow_type}', 
                shape='plaintext', fontsize='20', 
                fontcolor='#2C3E50' if self.theme.name != 'dark' else '#F3F4F6')
        
        # Overall metrics
        with dot.subgraph(name='cluster_metrics') as metrics:
            metrics.attr(label='Performance Metrics', fontsize='16', 
                        style='filled,rounded', fillcolor='#ECF0F1' if self.theme.name != 'dark' else '#374151', 
                        color='#34495E' if self.theme.name != 'dark' else '#9CA3AF')
            
            overall_metrics = f"""{{
Overall Performance|
{{Duration|{execution_report.total_duration_seconds:.2f}s}}|
{{Steps|{execution_report.step_count}}}|
{{Success Rate|{(execution_report.completed_steps/execution_report.step_count*100):.1f}%}}|
{{Reviews|{execution_report.total_reviews}}}|
{{Retries|{execution_report.total_retries}}}
}}"""
            metrics.node('overall', overall_metrics, shape='record', 
                        style='filled,rounded', fillcolor='white' if self.theme.name != 'dark' else '#1F2937',
                        fontcolor='black' if self.theme.name != 'dark' else 'white')
        
        # Agent performance
        with dot.subgraph(name='cluster_agents') as agents:
            agents.attr(label='Agent Performance', fontsize='16',
                       style='filled,rounded', fillcolor='#E8F6F3' if self.theme.name != 'dark' else '#1F2937', 
                       color='#16A085' if self.theme.name != 'dark' else '#10B981')
            
            max_duration = max((perf.get('average_duration', 0) 
                               for perf in execution_report.agent_performance.values()), default=1)
            
            for agent, perf in execution_report.agent_performance.items():
                avg_duration = perf.get('average_duration', 0)
                success_rate = perf.get('success_rate', 0) * 100
                color = self.theme.get_gradient_color(avg_duration, 0, max_duration)
                
                agent_metrics = f"""{{
{agent}|
{{Calls|{perf.get('total_calls', 0)}}}|
{{Avg Time|{avg_duration:.2f}s}}|
{{Success|{success_rate:.1f}%}}|
{{Reviews|{perf.get('reviews_received', 0)}}}
}}"""
                agents.node(f'agent_{agent}', agent_metrics, shape='record',
                           style='filled,rounded', fillcolor=color, fontcolor='white')
        
        # Test results if available
        if execution_report.test_executions:
            with dot.subgraph(name='cluster_tests') as tests:
                tests.attr(label='Test Results', fontsize='16',
                          style='filled,rounded', fillcolor='#EBF5FB' if self.theme.name != 'dark' else '#1F2937', 
                          color='#3498DB' if self.theme.name != 'dark' else '#3B82F6')
                
                test_metrics = f"""{{
Test Execution|
{{Total Tests|{execution_report.total_tests}}}|
{{Passed|{execution_report.passed_tests}}}|
{{Failed|{execution_report.failed_tests}}}|
{{Pass Rate|{(execution_report.passed_tests/execution_report.total_tests*100):.1f}%}}
}}"""
                tests.node('tests', test_metrics, shape='record',
                          style='filled,rounded', fillcolor='white' if self.theme.name != 'dark' else '#374151',
                          fontcolor='black' if self.theme.name != 'dark' else 'white')
        
        self._save_graph(dot, workflow_name, "metrics")
    
    def _generate_timeline_view(self, workflow_name: str,
                              execution_report: WorkflowExecutionReport):
        """Generate timeline visualization"""
        print(f"  ⏱️  Generating timeline view for {workflow_name}...")
        
        dot = graphviz.Digraph(comment=f'{workflow_name} Timeline')
        dot.attr(rankdir='LR', size='20,10', bgcolor=self.theme.background_color)
        dot.attr('node', fontname=self.theme.font_family, fontsize=str(self.theme.font_size - 1), 
                shape='box', style='filled,rounded')
        dot.attr('edge', fontname=self.theme.font_family, fontsize=str(self.theme.font_size - 2))
        
        # Start node
        dot.node('start', 'START', shape='circle', 
                fillcolor=self.theme.status_colors['completed'], fontcolor='white')
        
        # Sort steps by start time
        sorted_steps = sorted(execution_report.steps, key=lambda s: s.start_time)
        
        # Create timeline nodes
        prev_node = 'start'
        for i, step in enumerate(sorted_steps):
            node_id = f'step_{i}'
            
            # Determine color based on status
            color = self.theme.status_colors.get(step.status.value, self.theme.status_colors['pending'])
            
            # Create label with timing info
            duration_str = f"{step.duration_seconds:.2f}s" if step.duration_seconds else "N/A"
            label = f"{step.step_name}\\n{step.agent_name}\\n{duration_str}"
            
            # Add node
            text_color = 'white' if step.status.value != 'pending' else 'black'
            if self.theme.name == 'dark':
                text_color = 'white'
            
            dot.node(node_id, label, fillcolor=color, fontcolor=text_color)
            
            # Connect to previous
            dot.edge(prev_node, node_id, label=f"{i+1}")
            prev_node = node_id
        
        # End node
        end_color = self.theme.status_colors['completed'] if execution_report.status == StepStatus.COMPLETED else self.theme.status_colors['failed']
        dot.node('end', 'END', shape='circle', fillcolor=end_color, fontcolor='white')
        dot.edge(prev_node, 'end')
        
        # Add legend for status colors
        if self.config.include_legends:
            with dot.subgraph(name='cluster_legend') as legend:
                legend.attr(label='Status Legend', fontsize='14', style='filled', 
                           fillcolor='#ECF0F1' if self.theme.name != 'dark' else '#374151')
                
                for status, color in self.theme.status_colors.items():
                    text_color = 'white' if status != 'pending' else 'black'
                    if self.theme.name == 'dark':
                        text_color = 'white'
                    legend.node(f'legend_{status}', status.title(), 
                               fillcolor=color, fontcolor=text_color)
        
        self._save_graph(dot, workflow_name, "timeline")
    
    def _generate_review_flow(self, workflow_name: str,
                            execution_report: WorkflowExecutionReport):
        """Generate review flow visualization"""
        print(f"  🔄 Generating review flow for {workflow_name}...")
        
        dot = graphviz.Digraph(comment=f'{workflow_name} Review Flow')
        dot.attr(rankdir='TB', size='12,16', bgcolor=self.theme.background_color)
        dot.attr('node', fontname=self.theme.font_family, fontsize=str(self.theme.font_size))
        dot.attr('edge', fontname=self.theme.font_family, fontsize=str(self.theme.font_size - 2))
        
        # Track which agents have been added
        agents_added = set()
        
        # Create nodes for each unique agent that received reviews
        for review in execution_report.reviews:
            target_agent = review.metadata.get('target_agent', 'unknown')
            
            if target_agent not in agents_added:
                color = self.theme.node_colors.get(target_agent, '#95A5A6')
                dot.node(target_agent, target_agent.replace('_', ' ').title(), 
                        shape='box', style='filled,rounded', fillcolor=color, fontcolor='white')
                agents_added.add(target_agent)
        
        # Add reviewer node
        dot.node('reviewer', 'Reviewer', shape='house', style='filled', 
                fillcolor=self.theme.node_colors['reviewer_agent'], fontcolor='black')
        
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
                color = self.theme.edge_colors['approval']
                arrowhead = 'normal'
            elif review.decision == ReviewDecision.REVISION_NEEDED:
                style = 'dashed'
                color = self.theme.edge_colors['feedback']
                arrowhead = 'tee'
            elif review.decision == ReviewDecision.AUTO_APPROVED:
                style = 'dotted'
                color = self.theme.edge_colors['validation']
                arrowhead = 'empty'
            else:
                style = 'solid'
                color = self.theme.edge_colors['review']
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
                fillcolor='#FFFACD' if self.theme.name != 'dark' else '#374151', 
                fontcolor='black' if self.theme.name != 'dark' else 'white',
                fontsize='14')
        
        self._save_graph(dot, workflow_name, "review_flow")
    
    def _generate_dependency_graph(self, workflow_name: str, data_flows: List[Tuple]):
        """Generate dependency graph showing data transformations"""
        print(f"  🔗 Generating dependency graph for {workflow_name}...")
        
        dot = graphviz.Digraph(comment=f'{workflow_name} Dependencies')
        dot.attr(rankdir='LR', size='16,12', bgcolor=self.theme.background_color)
        dot.attr('node', fontname=self.theme.font_family, fontsize=str(self.theme.font_size))
        dot.attr('edge', fontname=self.theme.font_family, fontsize=str(self.theme.font_size - 2))
        
        # Create clusters for each agent
        agent_clusters = {}
        
        for source, target, schema, transformations, flow_type in data_flows:
            # Create clusters for agents
            for agent in [source, target]:
                if agent and '_agent' in agent and agent not in agent_clusters:
                    cluster_name = f'cluster_{agent}'
                    cluster = graphviz.Digraph(name=cluster_name)
                    cluster.attr(label=agent.replace('_', ' ').title(), 
                               style='filled,rounded',
                               fillcolor='#E8E8E8' if self.theme.name != 'dark' else '#374151',
                               fontsize='14')
                    agent_clusters[agent] = cluster
            
            # Add schema nodes
            if schema and self.config.show_schemas:
                for field, field_type in schema.items():
                    if field != '__doc__':
                        node_id = f"{source}_{field}"
                        label = f"{field}: {field_type}" if field_type else field
                        
                        if source in agent_clusters:
                            agent_clusters[source].node(node_id, label, 
                                                       shape='ellipse', style='filled',
                                                       fillcolor='white' if self.theme.name != 'dark' else '#1F2937',
                                                       fontcolor='black' if self.theme.name != 'dark' else 'white')
            
            # Add transformation edges
            if transformations and self.config.show_transformations:
                for trans in transformations:
                    if target:
                        edge_label = f"{trans['type']}: {trans.get('target', '')}"
                        dot.edge(source, target, label=edge_label, 
                                style='dashed', color=self.theme.edge_colors['data_transform'])
        
        # Add clusters to main graph
        for cluster in agent_clusters.values():
            dot.subgraph(cluster)
        
        # Add regular flow edges
        for source, target, _, _, flow_type in data_flows:
            if target and flow_type:
                color = self.theme.edge_colors.get(flow_type, self.theme.edge_colors['sequential'])
                dot.edge(source, target, label=flow_type, color=color)
        
        self._save_graph(dot, workflow_name, "dependencies")
    
    def _generate_system_overview(self, all_workflow_data: Dict[str, List[Tuple]]):
        """Generate system overview visualization"""
        print("\n🌐 Generating system overview...")
        
        dot = graphviz.Digraph(comment='Workflow System Overview')
        dot.attr(rankdir='TB', size='18,24', bgcolor=self.theme.background_color, pad='1')
        dot.attr('node', fontname=self.theme.font_family, fontsize='14', style='filled')
        dot.attr('edge', fontname=self.theme.font_family, fontsize='11')
        
        # Title
        dot.node('title', '🚀 Modular Agent Workflow System', 
                shape='plaintext', fontsize='24', 
                fontcolor='#1A237E' if self.theme.name != 'dark' else '#E0E7FF')
        
        # User input layer
        with dot.subgraph(name='cluster_input') as inp:
            inp.attr(label='User Layer', fontsize='16', style='filled,rounded', 
                    fillcolor='#E3F2FD' if self.theme.name != 'dark' else '#1E3A8A', 
                    color='#1976D2' if self.theme.name != 'dark' else '#60A5FA')
            inp.node('user', '👤 User', shape='circle', 
                    fillcolor='#BBDEFB' if self.theme.name != 'dark' else '#2563EB',
                    fontcolor='black' if self.theme.name != 'dark' else 'white')
            inp.node('requirements', '📝 Requirements', shape='note', 
                    fillcolor='#90CAF9' if self.theme.name != 'dark' else '#3B82F6',
                    fontcolor='black' if self.theme.name != 'dark' else 'white')
            inp.edge('user', 'requirements')
        
        # Orchestration layer
        with dot.subgraph(name='cluster_orchestration') as orch:
            orch.attr(label='Orchestration Layer', fontsize='16', style='filled,rounded',
                     fillcolor='#F3E5F5' if self.theme.name != 'dark' else '#581C87', 
                     color='#7B1FA2' if self.theme.name != 'dark' else '#A78BFA')
            orch.node('orchestrator', '🎯 Orchestrator', shape='doubleoctagon', 
                     fillcolor='#CE93D8' if self.theme.name != 'dark' else '#7C3AED', 
                     fontcolor='white' if self.theme.name == 'dark' else 'black', penwidth='3')
            orch.node('workflow_manager', '📊 Workflow Manager', shape='box3d', 
                     fillcolor='#BA68C8' if self.theme.name != 'dark' else '#6D28D9', 
                     fontcolor='white')
            orch.edge('orchestrator', 'workflow_manager', style='bold')
        
        # Workflow types
        with dot.subgraph(name='cluster_workflows') as wf:
            wf.attr(label='Workflow Types', fontsize='16', style='filled,rounded',
                   fillcolor='#E8F5E8' if self.theme.name != 'dark' else '#14532D', 
                   color='#388E3C' if self.theme.name != 'dark' else '#84CC16')
            
            workflow_nodes = {
                'tdd': ('🧪 TDD Workflow', '#81C784' if self.theme.name != 'dark' else '#22C55E'),
                'full': ('🚀 Full Workflow', '#66BB6A' if self.theme.name != 'dark' else '#16A34A'),
                'individual': ('📍 Individual Steps', '#4CAF50' if self.theme.name != 'dark' else '#15803D'),
                'incremental': ('🔄 Incremental', '#43A047' if self.theme.name != 'dark' else '#166534')
            }
            
            for wf_id, (label, color) in workflow_nodes.items():
                wf.node(wf_id, label, shape='cylinder', fillcolor=color, fontcolor='white')
        
        # Agent pool
        with dot.subgraph(name='cluster_agents') as agents:
            agents.attr(label='Agent Pool', fontsize='16', style='filled,rounded',
                       fillcolor='#FFF3E0' if self.theme.name != 'dark' else '#78350F', 
                       color='#F57C00' if self.theme.name != 'dark' else '#FCD34D')
            
            agent_configs = [
                ('planner', '📋 Planner', self.theme.node_colors['planner_agent']),
                ('designer', '🎨 Designer', self.theme.node_colors['designer_agent']),
                ('test_writer', '🧪 Test Writer', self.theme.node_colors['test_writer_agent']),
                ('coder', '💻 Coder', self.theme.node_colors['coder_agent']),
                ('reviewer', '🔍 Reviewer', self.theme.node_colors['reviewer_agent'])
            ]
            
            for agent_id, label, color in agent_configs:
                agents.node(agent_id, label, shape='component', fillcolor=color, fontcolor='white')
        
        # Monitoring layer
        with dot.subgraph(name='cluster_monitoring') as mon:
            mon.attr(label='Monitoring & Analytics', fontsize='16', style='filled,rounded',
                    fillcolor='#FFEBEE' if self.theme.name != 'dark' else '#7F1D1D', 
                    color='#C62828' if self.theme.name != 'dark' else '#F87171')
            mon.node('tracer', '📈 Execution Tracer', shape='box3d', 
                    fillcolor='#EF5350' if self.theme.name != 'dark' else '#DC2626', 
                    fontcolor='white')
            mon.node('reports', '📊 Reports', shape='tab', 
                    fillcolor='#E53935' if self.theme.name != 'dark' else '#B91C1C', 
                    fontcolor='white')
            mon.edge('tracer', 'reports')
        
        # Connect layers
        dot.edge('requirements', 'orchestrator', style='bold', penwidth='3')
        dot.edge('workflow_manager', 'tdd', label='if TDD')
        dot.edge('workflow_manager', 'full', label='if Full')
        dot.edge('workflow_manager', 'individual', label='if Individual')
        dot.edge('workflow_manager', 'incremental', label='if Incremental')
        
        # Workflow to agents connections (simplified)
        for wf_node in ['tdd', 'full', 'individual', 'incremental']:
            for agent in ['planner', 'designer', 'test_writer', 'coder', 'reviewer']:
                dot.edge(wf_node, agent, style='dotted', color='gray', arrowhead='none')
        
        # Monitoring connections
        dot.edge('orchestrator', 'tracer', style='dashed', color='red')
        
        self._save_graph(dot, "system", "overview")
    
    def _export_workflow_json(self, workflow_name: str, data_flows: List[Tuple],
                            execution_report: Optional[WorkflowExecutionReport] = None):
        """Export workflow data as JSON for interactive visualization"""
        print(f"  💾 Exporting JSON data for {workflow_name}...")
        
        nodes_data = []
        edges_data = []
        node_ids = set()
        
        # Collect unique nodes
        for source, target, _, _, _ in data_flows:
            node_ids.add(source)
            if target:
                node_ids.add(target)
        
        # Generate node data
        for node_id in node_ids:
            node_info = {
                'id': node_id,
                'label': node_id.replace('_', ' ').title(),
                'type': self._get_node_type(node_id),
                'color': self.theme.node_colors.get(node_id, '#95A5A6'),
                'details': {
                    'docstring': f'Documentation for {node_id}',
                    'performance': {}
                }
            }
            
            # Add performance data if available
            if execution_report and node_id in execution_report.agent_performance:
                perf = execution_report.agent_performance[node_id]
                node_info['details']['performance'] = {
                    'average_duration': perf.get('average_duration', 0),
                    'total_calls': perf.get('total_calls', 0),
                    'success_rate': perf.get('success_rate', 0)
                }
            
            nodes_data.append(node_info)
        
        # Generate edge data
        for source, target, data_schema, transformations, flow_type in data_flows:
            if not target:
                continue
                
            edge_info = {
                'from': source,
                'to': target,
                'label': flow_type or 'data flow',
                'flow_type': flow_type,
                'color': self.theme.edge_colors.get(flow_type, self.theme.edge_colors['sequential']),
                'details': {
                    'data_schema': data_schema,
                    'transformations': transformations
                }
            }
            edges_data.append(edge_info)
        
        # Create complete workflow data
        workflow_data = {
            'workflow_name': workflow_name,
            'timestamp': datetime.now().isoformat(),
            'theme': self.theme.name,
            'nodes': nodes_data,
            'edges': edges_data,
            'metrics': {}
        }
        
        # Add execution metrics if available
        if execution_report:
            workflow_data['metrics'] = {
                'total_duration': execution_report.total_duration_seconds,
                'step_count': execution_report.step_count,
                'completed_steps': execution_report.completed_steps,
                'success_rate': (execution_report.completed_steps / execution_report.step_count * 100) if execution_report.step_count > 0 else 0,
                'total_reviews': execution_report.total_reviews,
                'total_retries': execution_report.total_retries
            }
        
        # Save JSON file
        json_path = self.config.output_dir / f"{workflow_name.lower().replace(' ', '_')}_data.json"
        with open(json_path, 'w') as f:
            json.dump(workflow_data, f, indent=2)
    
    def _export_interactive_data(self, all_workflow_data: Dict[str, List[Tuple]]):
        """Export all workflow data for interactive visualization"""
        print("\n📦 Exporting interactive data...")
        
        all_workflows = {}
        
        for workflow_name, data_flows in all_workflow_data.items():
            # Process each workflow
            nodes_data = []
            edges_data = []
            node_ids = set()
            
            for source, target, _, _, _ in data_flows:
                node_ids.add(source)
                if target:
                    node_ids.add(target)
            
            for node_id in node_ids:
                nodes_data.append({
                    'id': node_id,
                    'label': node_id.replace('_', ' ').title(),
                    'type': self._get_node_type(node_id),
                    'color': self.theme.node_colors.get(node_id, '#95A5A6')
                })
            
            for source, target, data_schema, transformations, flow_type in data_flows:
                if target:
                    edges_data.append({
                        'from': source,
                        'to': target,
                        'label': flow_type or 'data flow',
                        'flow_type': flow_type,
                        'details': {
                            'data_schema': data_schema,
                            'transformations': transformations
                        }
                    })
            
            all_workflows[workflow_name] = {
                'nodes': nodes_data,
                'edges': edges_data
            }
        
        # Save comprehensive data file
        output_path = self.config.output_dir / "interactive_workflow_data.json"
        with open(output_path, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'theme': self.theme.name,
                'workflows': all_workflows
            }, f, indent=2)
        
        print(f"✅ Interactive data exported to: {output_path}")
    
    # Helper methods
    
    def _get_node_info(self, node: str, execution_report: Optional[WorkflowExecutionReport] = None) -> Dict:
        """Get node styling information"""
        emoji_map = {
            'planner_agent': '📋',
            'designer_agent': '🎨',
            'test_writer_agent': '🧪',
            'coder_agent': '💻',
            'reviewer_agent': '🔍',
            'input': '📥',
            'output': '📤',
            'test_execution': '🧪',
            'workflow_continuation': '➡️',
            'incremental_coder': '🔄'
        }
        
        shape_map = {
            'input': 'invhouse',
            'output': 'house',
            'test_execution': 'component',
            'workflow_continuation': 'circle',
            'reviewer_agent': 'house'
        }
        
        emoji = emoji_map.get(node, '👤')
        display_name = node.replace('_agent', '').replace('_', ' ').title()
        
        # Add performance info if available
        perf_info = ""
        if execution_report and node in execution_report.agent_performance:
            perf = execution_report.agent_performance[node]
            avg_time = perf.get('average_duration', 0)
            perf_info = f"\\n⏱️ {avg_time:.1f}s avg"
        
        return {
            'label': f"{emoji} {display_name}{perf_info}",
            'shape': shape_map.get(node, 'box3d' if '_agent' in node else 'box'),
            'fillcolor': self.theme.node_colors.get(node, '#E0E0E0'),
            'fontcolor': 'white' if node != 'workflow_continuation' else 'black',
            'style': 'filled,rounded'
        }
    
    def _add_edge(self, dot: graphviz.Digraph, source: str, target: str, 
                  edge_data_list: List[Tuple[Dict, List, Optional[str]]]):
        """Add edge with appropriate styling"""
        # Determine primary flow type
        primary_flow_type = None
        for _, _, flow_type in edge_data_list:
            if flow_type in ['review', 'feedback', 'approval', 'validation']:
                primary_flow_type = flow_type
                break
        if not primary_flow_type:
            primary_flow_type = edge_data_list[0][2] if edge_data_list[0][2] else 'sequential'
        
        # Edge styling
        edge_styles = {
            'sequential': {'style': 'solid', 'penwidth': '2', 'arrowsize': '1'},
            'review': {'style': 'dashed', 'penwidth': '2', 'arrowsize': '1.2', 'arrowhead': 'diamond'},
            'feedback': {'style': 'dotted', 'penwidth': '3', 'arrowsize': '1.2', 'arrowhead': 'tee'},
            'approval': {'style': 'bold', 'penwidth': '3', 'arrowsize': '1.5', 'arrowhead': 'normal'},
            'validation': {'style': 'dashed', 'penwidth': '2', 'arrowsize': '1', 'arrowhead': 'dot'},
            'parallel': {'style': 'solid', 'penwidth': '2', 'arrowsize': '1', 'dir': 'both'}
        }
        
        style = edge_styles.get(primary_flow_type, edge_styles['sequential'])
        color = self.theme.edge_colors.get(primary_flow_type, self.theme.edge_colors['sequential'])
        
        # Build edge label
        labels = []
        for data_schema, transformations, flow_type in edge_data_list:
            if self.config.show_schemas and 'type' in data_schema:
                labels.append(data_schema['type'])
            elif flow_type:
                labels.append(flow_type.replace('_', ' ').title())
        
        if len(edge_data_list) > 1:
            labels.append(f"({len(edge_data_list)} flows)")
        
        edge_label = '\\n'.join(labels[:3]) if labels else ''  # Limit to 3 labels
        
        # Add the edge
        dot.edge(source, target, label=edge_label, color=color, **style)
    
    def _add_flow_legend(self, dot: graphviz.Digraph):
        """Add legend for flow types"""
        with dot.subgraph(name='cluster_legend') as legend:
            legend.attr(label='Flow Types', fontsize='14', style='filled', 
                       fillcolor='#F5F5F5' if self.theme.name != 'dark' else '#374151')
            
            flow_examples = [
                ('Sequential', 'sequential'),
                ('Review', 'review'),
                ('Feedback', 'feedback'),
                ('Approval', 'approval'),
                ('Validation', 'validation')
            ]
            
            prev = None
            for name, flow_type in flow_examples:
                node_id = f'legend_{flow_type}'
                legend.node(node_id, name, shape='plaintext')
                if prev:
                    color = self.theme.edge_colors.get(flow_type, '#666')
                    legend.edge(prev, node_id, style='solid', penwidth='2', color=color)
                prev = node_id
    
    def _save_graph(self, graph: graphviz.Digraph, workflow_name: str, suffix: str):
        """Save graph in configured formats"""
        base_filename = f"{workflow_name.lower().replace(' ', '_')}_{suffix}"
        base_path = self.config.output_dir / base_filename
        
        # Save DOT file
        if "dot" in self.config.output_formats:
            dot_path = f"{base_path}.dot"
            graph.save(dot_path)
            print(f"    ✅ DOT: {base_filename}.dot")
        
        # Render to other formats
        for fmt in self.config.output_formats:
            if fmt == "dot":
                continue
            try:
                if fmt in ["png", "jpg"]:
                    # Use higher resolution for raster formats
                    graph.render(str(base_path), format=fmt, cleanup=True,
                               engine='dot', renderer='cairo', formatter='cairo')
                else:
                    graph.render(str(base_path), format=fmt, cleanup=True)
                print(f"    ✅ {fmt.upper()}: {base_filename}.{fmt}")
            except Exception as e:
                print(f"    ⚠️  Failed to render {fmt}: {e}")
    
    def _get_node_type(self, node_id: str) -> str:
        """Determine node type from its ID"""
        if '_agent' in node_id:
            return 'agent'
        elif node_id == 'input':
            return 'input'
        elif node_id == 'output':
            return 'output'
        elif node_id == 'test_execution':
            return 'test'
        elif node_id == 'workflow_continuation':
            return 'flow_control'
        else:
            return 'unknown'


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for the unified visualizer"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Unified Workflow Visualizer - Generate comprehensive workflow visualizations"
    )
    parser.add_argument(
        "--mode", 
        type=str,
        choices=[mode.value for mode in VisualizationMode],
        default="all",
        help="Visualization mode to generate"
    )
    parser.add_argument(
        "--workflow",
        type=str,
        choices=list(WorkflowAnalyzer.WORKFLOW_MAPPING.keys()),
        help="Specific workflow to visualize (default: all)"
    )
    parser.add_argument(
        "--theme",
        type=str,
        choices=["modern", "dark", "light", "classic"],
        default="modern",
        help="Visual theme to use"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for visualizations"
    )
    parser.add_argument(
        "--formats",
        type=str,
        nargs="+",
        default=["png", "svg", "json"],
        help="Output formats to generate"
    )
    parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Disable metrics in visualizations"
    )
    parser.add_argument(
        "--3d",
        action="store_true",
        help="Enable 3D visualizations (experimental)"
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = VisualizationConfig(
        theme=args.theme,
        output_formats=args.formats,
        show_metrics=not args.no_metrics,
        enable_3d=getattr(args, '3d', False)
    )
    
    if args.output_dir:
        config.output_dir = Path(args.output_dir)
    
    # Create visualizer
    visualizer = UnifiedWorkflowVisualizer(config)
    
    # Generate visualizations
    mode = VisualizationMode(args.mode)
    
    if args.workflow:
        # Visualize specific workflow
        module_name, func_name = WorkflowAnalyzer.WORKFLOW_MAPPING[args.workflow]
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        visualizer.visualize_workflow(args.workflow, func, mode)
    else:
        # Visualize all workflows
        visualizer.visualize_all_workflows(mode)


if __name__ == "__main__":
    main()