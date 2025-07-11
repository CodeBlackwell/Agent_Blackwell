"""Enhanced Agent Coordinator with support for new agents and multi-file outputs"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional, Union
from pathlib import Path

from .enhanced_models import (
    EnhancedTDDPhase, EnhancedAgentContext, PhaseResult, 
    MultiFileOutput, ExpandedRequirements, ProjectArchitecture
)


class EnhancedAgentCoordinator:
    """Enhanced coordinator for agent invocations with planning agents support"""
    
    def __init__(self, run_team_member_func: Optional[Callable] = None):
        """
        Initialize enhanced coordinator
        Args:
            run_team_member_func: Function to run team members (for parent system integration)
        """
        self.run_team_member_func = run_team_member_func
        self.invocation_history: List[Dict[str, Any]] = []
        
        # Extended phase-agent mapping
        self.phase_agent_map = {
            EnhancedTDDPhase.REQUIREMENTS: "planner",
            EnhancedTDDPhase.ARCHITECTURE: "designer", 
            EnhancedTDDPhase.RED: "test_writer",
            EnhancedTDDPhase.YELLOW: "coder",
            EnhancedTDDPhase.GREEN: "executor",
            EnhancedTDDPhase.VALIDATION: "validator"
        }
        
        # Agent capabilities
        self.multi_file_agents = ["coder", "designer", "validator"]
        
        # If no external function provided, we'll use local agents
        if not self.run_team_member_func:
            self._setup_local_agents()
    
    def _setup_local_agents(self):
        """Setup references to local agents including new ones"""
        # Import local agents
        import sys
        flagship_path = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(flagship_path))
        
        # Original TDD agents
        from agents.test_writer_enhanced_flagship import TestWriterEnhancedFlagship
        from agents.coder_enhanced_flagship import CoderEnhancedFlagship
        from agents.test_runner_flagship import TestRunnerFlagship
        
        # New Flagship agents
        from agents.planner_flagship import PlannerFlagship
        from agents.designer_flagship import DesignerFlagship
        
        # Validator from main system (will create Flagship version if needed)
        # For now, use a simple validator
        
        self.local_agents = {
            "test_writer": TestWriterEnhancedFlagship(),
            "coder": CoderEnhancedFlagship(),
            "executor": TestRunnerFlagship(),
            "planner": PlannerFlagship(),
            "designer": DesignerFlagship(),
            "validator": None  # Will implement later
        }
    
    async def invoke_agent(self, agent_name: str, context: EnhancedAgentContext) -> Any:
        """
        Invoke an agent with enhanced context
        Returns agent result (can be MultiFileOutput for certain agents)
        """
        start_time = datetime.now()
        
        # Build agent-specific context
        agent_input = self._build_enhanced_agent_context(agent_name, context)
        
        # Record invocation
        invocation = {
            "agent": agent_name,
            "phase": context.phase.value,
            "feature_id": context.feature_id,
            "attempt": context.attempt_number,
            "timestamp": start_time.isoformat(),
            "input": agent_input
        }
        
        try:
            if self.run_team_member_func:
                # Use external function (parent system integration)
                result = await self.run_team_member_func(agent_name, agent_input)
            else:
                # Use local agents
                result = await self._invoke_local_agent(agent_name, agent_input, context)
            
            # Process result based on agent type
            processed_result = self._process_agent_result(agent_name, result, context)
            
            # Record success
            invocation["success"] = True
            invocation["output"] = self._serialize_result(processed_result)
            invocation["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
            return processed_result
            
        except Exception as e:
            # Record failure
            invocation["success"] = False
            invocation["error"] = str(e)
            invocation["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            raise
        
        finally:
            self.invocation_history.append(invocation)
    
    def _build_enhanced_agent_context(self, agent_name: str, context: EnhancedAgentContext) -> Dict:
        """Build agent-specific context with enhanced information"""
        base_context = {
            "requirements": context.feature_description,
            "phase": context.phase.value,
            "attempt": context.attempt_number
        }
        
        # Add agent-specific context
        if agent_name == "planner":
            # Planner needs original requirements
            base_context.update({
                "task": "analyze_requirements",
                "expand_vague_requirements": True,
                "identify_features": True,
                "suggest_architecture": True
            })
            
        elif agent_name == "designer":
            # Designer needs expanded requirements and project type
            base_context.update({
                "task": "design_architecture",
                "expanded_requirements": context.expanded_requirements.__dict__ if context.expanded_requirements else None,
                "project_type": context.expanded_requirements.project_type if context.expanded_requirements else "unknown",
                "create_file_structure": True,
                "define_components": True,
                "specify_apis": True
            })
            
        elif agent_name == "test_writer":
            # Enhanced test writer with feature awareness
            base_context.update({
                "current_feature": context.current_feature.__dict__ if context.current_feature else None,
                "architecture": self._simplify_architecture(context.architecture),
                "existing_files": list(context.generated_files.keys()),
                "test_criteria": context.current_feature.test_criteria if context.current_feature else [],
                "generate_comprehensive_tests": True
            })
            
        elif agent_name == "coder":
            # Enhanced coder with multi-file support
            base_context.update({
                "test_code": context.phase_context.get("test_code", ""),
                "current_feature": context.current_feature.__dict__ if context.current_feature else None,
                "architecture": self._simplify_architecture(context.architecture),
                "existing_files": context.generated_files,
                "support_multi_file": True,
                "follow_architecture": True
            })
            
        elif agent_name == "executor":
            # Test runner with project awareness
            base_context.update({
                "test_code": context.phase_context.get("test_code", ""),
                "implementation": context.phase_context.get("implementation", ""),
                "all_files": context.generated_files,
                "run_all_tests": True,
                "generate_coverage": True
            })
            
        elif agent_name == "validator":
            # Validator needs full context
            base_context.update({
                "expanded_requirements": context.expanded_requirements.__dict__ if context.expanded_requirements else None,
                "architecture": self._simplify_architecture(context.architecture),
                "generated_files": list(context.generated_files.keys()),
                "validate_requirements": True,
                "check_test_coverage": True,
                "verify_integration": True
            })
        
        return base_context
    
    async def _invoke_local_agent(self, agent_name: str, agent_input: Dict, context: EnhancedAgentContext):
        """Invoke a local agent with enhanced capabilities"""
        if agent_name not in self.local_agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = self.local_agents[agent_name]
        
        # Handle different agent types
        if agent_name == "planner":
            # Use Flagship planner
            output = []
            async for chunk in agent.analyze_requirements(
                agent_input.get("requirements", ""),
                agent_input
            ):
                output.append(chunk)
            
            # Also get the expanded requirements
            expanded = agent.get_expanded_requirements()
            return {"output": "".join(output), "expanded_requirements": expanded}
            
        elif agent_name == "designer":
            # Use Flagship designer
            output = []
            async for chunk in agent.design_architecture(
                agent_input.get("requirements", ""),
                agent_input.get("expanded_requirements"),
                agent_input
            ):
                output.append(chunk)
            
            # Also get the architecture
            architecture = agent.get_architecture()
            return {"output": "".join(output), "architecture": architecture}
            
        elif agent_name == "validator":
            # Simple validation for now
            if not agent:
                return {"all_requirements_met": True, "message": "Validation not implemented yet"}
            
        elif agent_name == "test_writer":
            # Enhanced test writer
            if hasattr(agent, 'write_comprehensive_tests'):
                # Use enhanced method if available
                result = await agent.write_comprehensive_tests(
                    agent_input.get("requirements", ""),
                    agent_input
                )
            else:
                # Fallback to standard method
                result = await agent.write_tests(
                    agent_input.get("requirements", ""),
                    agent_input
                )
            
            # Collect streaming output
            test_code = []
            async for chunk in result:
                test_code.append(chunk)
            
            return "".join(test_code)
            
        elif agent_name == "coder":
            # Enhanced coder with multi-file support
            output = []
            async for chunk in agent.generate_multi_file_implementation(
                agent_input.get("test_code", ""),
                agent_input
            ):
                output.append(chunk)
            
            # Get implementation files
            implementation_files = agent.get_implementation_files()
            
            # Return both output and files
            return {
                "output": "".join(output),
                "files": implementation_files
            }
            
        elif agent_name == "executor":
            # Test runner
            result = await agent.run_tests(
                agent_input.get("test_code", ""),
                agent_input.get("implementation", ""),
                agent_input
            )
            
            # Collect results
            output = []
            test_results = {}
            async for chunk in result:
                output.append(chunk)
                # Parse test results from output if available
                if "test_results" in chunk:
                    test_results = json.loads(chunk)
            
            return test_results if test_results else {"output": "".join(output)}
        
        else:
            raise ValueError(f"Agent {agent_name} not implemented")
    
    def _process_agent_result(self, agent_name: str, result: Any, context: EnhancedAgentContext) -> Any:
        """Process agent result based on agent type"""
        if agent_name == "coder" and agent_name in self.multi_file_agents:
            # Check if result is already structured with files
            if isinstance(result, dict) and "files" in result:
                files = result["files"]
                
                # Determine main file
                main_file = self._determine_main_file(files, context)
                
                return MultiFileOutput(
                    files=files,
                    main_file=main_file,
                    file_types=self._classify_files(files),
                    dependencies=self._extract_dependencies(files)
                )
            
            # Check if result contains multiple files in text format
            elif isinstance(result, str) and "FILE:" in result:
                # Parse multi-file output format
                files = self._parse_multi_file_output(result)
                
                # Determine main file
                main_file = self._determine_main_file(files, context)
                
                return MultiFileOutput(
                    files=files,
                    main_file=main_file,
                    file_types=self._classify_files(files),
                    dependencies=self._extract_dependencies(files)
                )
        
        # Return result as-is for other agents
        return result
    
    def _parse_multi_file_output(self, output: str) -> Dict[str, str]:
        """Parse multi-file output from agent"""
        files = {}
        current_file = None
        current_content = []
        
        for line in output.split('\n'):
            if line.startswith("FILE:"):
                # Save previous file
                if current_file:
                    files[current_file] = '\n'.join(current_content)
                
                # Start new file
                current_file = line[5:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last file
        if current_file:
            files[current_file] = '\n'.join(current_content)
        
        return files
    
    def _determine_main_file(self, files: Dict[str, str], context: EnhancedAgentContext) -> str:
        """Determine the main/entry point file"""
        # Common entry point names
        entry_points = ["app.py", "server.py", "main.py", "index.js", "app.js", "index.html"]
        
        for entry in entry_points:
            if entry in files:
                return entry
        
        # Return first Python file if no clear entry point
        for filename in files:
            if filename.endswith(".py"):
                return filename
        
        # Return first file as fallback
        return list(files.keys())[0] if files else ""
    
    def _classify_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Classify files by type"""
        classifications = {}
        
        for filename in files:
            if filename.endswith((".html", ".css", ".js", ".jsx", ".tsx")):
                classifications[filename] = "frontend"
            elif filename.endswith((".py", ".rb", ".java", ".go")):
                if "test" in filename.lower():
                    classifications[filename] = "test"
                else:
                    classifications[filename] = "backend"
            elif filename in ["requirements.txt", "package.json", "Dockerfile", ".env"]:
                classifications[filename] = "config"
            else:
                classifications[filename] = "other"
        
        return classifications
    
    def _extract_dependencies(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """Extract dependencies from files"""
        dependencies = {}
        
        # Check for Python dependencies
        if "requirements.txt" in files:
            deps = [line.strip() for line in files["requirements.txt"].split('\n') if line.strip()]
            dependencies["python"] = deps
        
        # Check for Node dependencies
        if "package.json" in files:
            try:
                package = json.loads(files["package.json"])
                deps = list(package.get("dependencies", {}).keys())
                deps.extend(list(package.get("devDependencies", {}).keys()))
                dependencies["node"] = deps
            except:
                pass
        
        return dependencies
    
    def _simplify_architecture(self, architecture: Optional[ProjectArchitecture]) -> Optional[Dict]:
        """Simplify architecture for agent context"""
        if not architecture:
            return None
        
        return {
            "project_type": architecture.project_type,
            "structure": architecture.structure,
            "technology_stack": architecture.technology_stack,
            "components": [comp.name for comp in architecture.components]
        }
    
    def _serialize_result(self, result: Any) -> str:
        """Serialize result for storage"""
        if isinstance(result, MultiFileOutput):
            return json.dumps({
                "type": "multi_file",
                "files": list(result.files.keys()),
                "main_file": result.main_file
            })
        elif isinstance(result, dict):
            return json.dumps(result)
        else:
            return str(result)