"""
Validation Debugger for Executor Agent

Provides detailed logging and debugging information for validation decisions.
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

class ValidationDebugger:
    """Debug helper for understanding validation decisions"""
    
    def __init__(self, session_id: str, debug_enabled: bool = True):
        self.session_id = session_id
        self.debug_enabled = debug_enabled
        self.validation_log = []
        
    def log_validation_attempt(self, feature_id: str, input_data: Dict[str, Any]):
        """Log the start of a validation attempt"""
        if not self.debug_enabled:
            return
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "feature_id": feature_id,
            "event": "validation_start",
            "input_summary": {
                "files_count": len(input_data.get("files", [])),
                "has_tests": bool(input_data.get("tests")),
                "validation_criteria": input_data.get("validation_criteria", "")
            }
        }
        self.validation_log.append(entry)
        
    def log_executor_output(self, feature_id: str, raw_output: str):
        """Log raw executor output for analysis"""
        if not self.debug_enabled:
            return
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "feature_id": feature_id,
            "event": "executor_output",
            "output_length": len(raw_output),
            "output_preview": raw_output[:500],
            "contains_success_marker": "✅" in raw_output,
            "contains_failure_marker": "❌" in raw_output,
            "contains_docker_result": "DOCKER EXECUTION RESULT" in raw_output,
            "contains_error_word": "error" in raw_output.lower()
        }
        self.validation_log.append(entry)
        
    def log_parsing_decision(self, feature_id: str, parsing_details: Dict[str, Any]):
        """Log how the validation result was parsed"""
        if not self.debug_enabled:
            return
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "feature_id": feature_id,
            "event": "parsing_decision",
            "details": parsing_details
        }
        self.validation_log.append(entry)
        
    def log_final_result(self, feature_id: str, success: bool, feedback: str):
        """Log the final validation result"""
        if not self.debug_enabled:
            return
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "feature_id": feature_id,
            "event": "validation_result",
            "success": success,
            "feedback": feedback
        }
        self.validation_log.append(entry)
        
    def get_validation_report(self, feature_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a detailed validation report"""
        if feature_id:
            entries = [e for e in self.validation_log if e.get("feature_id") == feature_id]
        else:
            entries = self.validation_log
            
        # Analyze patterns
        total_validations = len([e for e in entries if e["event"] == "validation_start"])
        successful = len([e for e in entries if e["event"] == "validation_result" and e.get("success")])
        failed = len([e for e in entries if e["event"] == "validation_result" and not e.get("success")])
        
        # Find common failure patterns
        failure_patterns = {}
        for entry in entries:
            if entry["event"] == "validation_result" and not entry.get("success"):
                feedback = entry.get("feedback", "")
                if "timeout" in feedback.lower():
                    failure_patterns["timeout"] = failure_patterns.get("timeout", 0) + 1
                elif "syntax" in feedback.lower():
                    failure_patterns["syntax_error"] = failure_patterns.get("syntax_error", 0) + 1
                elif "import" in feedback.lower():
                    failure_patterns["import_error"] = failure_patterns.get("import_error", 0) + 1
                else:
                    failure_patterns["other"] = failure_patterns.get("other", 0) + 1
                    
        return {
            "session_id": self.session_id,
            "total_validations": total_validations,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_validations if total_validations > 0 else 0,
            "failure_patterns": failure_patterns,
            "detailed_log": entries
        }
        
    def save_debug_log(self, output_path: Optional[Path] = None):
        """Save debug log to file"""
        if not self.debug_enabled or not self.validation_log:
            return
            
        if output_path is None:
            from workflows.workflow_config import GENERATED_CODE_PATH
            output_path = Path(GENERATED_CODE_PATH) / f"validation_debug_{self.session_id}.json"
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "validation_log": self.validation_log,
                "summary": self.get_validation_report()
            }, f, indent=2)
            
        print(f"📝 Validation debug log saved to: {output_path}")
        
    def print_summary(self):
        """Print a summary of validation decisions"""
        if not self.debug_enabled:
            return
            
        report = self.get_validation_report()
        
        print("\n" + "="*60)
        print("VALIDATION DEBUG SUMMARY")
        print("="*60)
        print(f"Session: {self.session_id}")
        print(f"Total Validations: {report['total_validations']}")
        print(f"Success Rate: {report['success_rate']:.1%}")
        print(f"Successful: {report['successful']}")
        print(f"Failed: {report['failed']}")
        
        if report['failure_patterns']:
            print("\nFailure Patterns:")
            for pattern, count in report['failure_patterns'].items():
                print(f"  - {pattern}: {count}")
                
        print("="*60)