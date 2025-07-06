"""
Proof of Execution Reader utility for extracting execution details from proof documents.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from workflows.workflow_config import GENERATED_CODE_PATH


class ProofOfExecutionReader:
    """Reads and extracts information from proof of execution documents"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.proof_path = self._find_proof_document()
    
    def _find_proof_document(self) -> Optional[Path]:
        """Find the proof of execution document for the session"""
        # Try standard location first
        generated_path = Path(GENERATED_CODE_PATH)
        standard_path = generated_path / self.session_id / "proof_of_execution.json"
        
        if standard_path.exists():
            return standard_path
        
        # Search in session directory and subdirectories
        session_dir = generated_path / self.session_id
        if session_dir.exists():
            proof_files = list(session_dir.rglob("proof_of_execution.json"))
            if proof_files:
                return proof_files[0]
        
        return None
    
    def read_proof_entries(self) -> List[Dict[str, Any]]:
        """Read all proof entries from the document"""
        if not self.proof_path or not self.proof_path.exists():
            return []
        
        try:
            with open(self.proof_path, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Extract a summary of the execution from proof entries"""
        entries = self.read_proof_entries()
        
        if not entries:
            return {
                "found": False,
                "session_id": self.session_id,
                "message": "No proof of execution found"
            }
        
        summary = {
            "found": True,
            "session_id": self.session_id,
            "proof_path": str(self.proof_path),
            "total_stages": len(entries),
            "stages": []
        }
        
        # Extract key information from each stage
        for entry in entries:
            stage_info = {
                "stage": entry.get("stage", "unknown"),
                "status": entry.get("status", "unknown"),
                "timestamp": entry.get("timestamp", ""),
                "details": {}
            }
            
            # Extract stage-specific details
            details = entry.get("details", {})
            
            if entry["stage"] == "environment_analysis" and entry["status"] == "completed":
                stage_info["details"] = {
                    "language": details.get("language"),
                    "version": details.get("version"),
                    "base_image": details.get("base_image"),
                    "dependencies_count": details.get("dependencies_count", 0)
                }
            
            elif entry["stage"] == "docker_setup" and entry["status"] == "completed":
                stage_info["details"] = {
                    "container_name": details.get("container_name"),
                    "container_id": details.get("container_id"),
                    "reused_existing": details.get("reused_existing", False)
                }
            
            elif entry["stage"] == "code_execution" and entry["status"] == "completed":
                stage_info["details"] = {
                    "overall_success": details.get("overall_success", False),
                    "executions": []
                }
                
                # Extract execution details
                for exec_detail in details.get("executions", []):
                    exec_info = {
                        "command": exec_detail.get("command"),
                        "success": exec_detail.get("success"),
                        "exit_code": exec_detail.get("exit_code"),
                        "output_preview": exec_detail.get("stdout_preview", "")[:200]
                    }
                    stage_info["details"]["executions"].append(exec_info)
            
            elif entry["stage"] == "result_analysis" and entry["status"] == "completed":
                stage_info["details"] = {
                    "analysis_preview": details.get("analysis_preview", "")[:500]
                }
            
            elif entry["stage"] == "executor_error":
                stage_info["details"] = {
                    "error_type": details.get("error_type"),
                    "error_message": details.get("error_message")
                }
            
            summary["stages"].append(stage_info)
        
        # Determine overall execution success
        execution_stages = [s for s in summary["stages"] if s["stage"] == "code_execution"]
        if execution_stages:
            summary["execution_success"] = any(
                s["details"].get("overall_success", False) 
                for s in execution_stages 
                if s["status"] == "completed"
            )
        else:
            summary["execution_success"] = False
        
        return summary
    
    def format_execution_proof(self) -> str:
        """Format the proof of execution as a readable string"""
        summary = self.get_execution_summary()
        
        if not summary["found"]:
            return f"❌ No proof of execution found for session {self.session_id}"
        
        lines = [
            f"📄 PROOF OF EXECUTION",
            f"Session: {summary['session_id']}",
            f"Document: {summary['proof_path']}",
            f"Stages: {summary['total_stages']}",
            ""
        ]
        
        # Format each stage
        for stage in summary["stages"]:
            status_icon = "✅" if stage["status"] == "completed" else "❌"
            lines.append(f"{status_icon} {stage['stage']}")
            
            if stage["stage"] == "code_execution" and stage["details"]:
                overall = stage["details"].get("overall_success", False)
                lines.append(f"   Overall Success: {'✅' if overall else '❌'}")
                
                for exec_detail in stage["details"].get("executions", []):
                    exec_icon = "✅" if exec_detail["success"] else "❌"
                    lines.append(f"   {exec_icon} {exec_detail['command']} (exit: {exec_detail['exit_code']})")
                    if exec_detail.get("output_preview"):
                        preview = exec_detail["output_preview"][:100]
                        lines.append(f"      Output: {preview}...")
            
            elif stage["details"]:
                for key, value in stage["details"].items():
                    if value:
                        lines.append(f"   {key}: {value}")
            
            lines.append("")
        
        # Add overall execution result
        exec_result = "✅ PASSED" if summary.get("execution_success") else "❌ FAILED"
        lines.append(f"Execution Result: {exec_result}")
        
        return "\n".join(lines)


def extract_proof_from_executor_output(executor_output: str, session_id: str) -> str:
    """
    Extract proof of execution details from executor output.
    This can be called from workflows to include proof in the final output.
    """
    reader = ProofOfExecutionReader(session_id)
    return reader.format_execution_proof()