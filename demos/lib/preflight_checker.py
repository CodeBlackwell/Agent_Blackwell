"""
Preflight checker for system validation.
Ensures all dependencies and services are ready before running demos.
"""

import sys
import os
import socket
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import importlib.util


class PreflightChecker:
    """Performs system checks before running demos."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the preflight checker.
        
        Args:
            verbose: Whether to show verbose output
        """
        self.verbose = verbose
        self.checks_passed = 0
        self.checks_failed = 0
        
    def check_python_version(self) -> Tuple[bool, str, Optional[str]]:
        """Check if Python version meets requirements.
        
        Returns:
            Tuple of (passed, message, suggestion)
        """
        version = sys.version_info
        min_version = (3, 8)
        
        if version >= min_version:
            return True, f"Python {version.major}.{version.minor}.{version.micro}", None
        else:
            return (False, 
                   f"Python {version.major}.{version.minor}.{version.micro} (3.8+ required)",
                   "Please upgrade Python to version 3.8 or higher")
            
    def check_virtual_env(self) -> Tuple[bool, str, Optional[str]]:
        """Check if running in a virtual environment.
        
        Returns:
            Tuple of (passed, message, suggestion)
        """
        # Multiple ways to detect virtual environment
        in_venv = (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None or
            '.venv' in sys.executable or
            'venv' in sys.executable
        )
        
        if in_venv:
            venv_path = os.environ.get('VIRTUAL_ENV', '')
            if venv_path:
                venv_name = os.path.basename(venv_path)
                return True, f"Virtual environment active ({venv_name})", None
            return True, "Virtual environment active", None
        else:
            return (False,
                   "Not in virtual environment",
                   "Activate virtual environment with: source .venv/bin/activate")
            
    def check_dependencies(self) -> Tuple[bool, str, Optional[str]]:
        """Check if required Python packages are installed.
        
        Returns:
            Tuple of (passed, message, suggestion)
        """
        required_packages = [
            'pydantic',
            'requests',
            'fastapi',
            'uvicorn',
            'yaml',
            'aiohttp',
            'docker',
            'mcp'
        ]
        
        missing = []
        for package in required_packages:
            spec = importlib.util.find_spec(package)
            if spec is None:
                missing.append(package)
                
        if not missing:
            return True, "All dependencies installed", None
        else:
            return (False,
                   f"Missing packages: {', '.join(missing)}",
                   "Install dependencies with: uv pip install -r requirements.txt")
            
    def check_orchestrator_server(self, port: int = 8080) -> Tuple[bool, str, Optional[str]]:
        """Check if orchestrator server is running.
        
        Args:
            port: Port to check (default 8080)
            
        Returns:
            Tuple of (passed, message, suggestion)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                return True, f"Orchestrator server running on port {port}", None
            else:
                return (False,
                       f"Orchestrator server not running on port {port}",
                       "Start orchestrator with: python orchestrator/orchestrator_agent.py")
        except Exception as e:
            return (False,
                   f"Cannot check orchestrator: {str(e)}",
                   "Ensure network connectivity and try again")
            
    def check_api_server(self, port: int = 8000) -> Tuple[bool, str, Optional[str]]:
        """Check if API server is running (optional).
        
        Args:
            port: Port to check (default 8000)
            
        Returns:
            Tuple of (passed, message, suggestion)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                return True, f"API server running on port {port} (optional)", None
            else:
                # API server is optional, so we don't fail
                return (True,
                       f"API server not running on port {port} (optional)",
                       "Start API server with: python api/orchestrator_api.py")
        except Exception:
            return True, "API server check skipped (optional)", None
            
    def check_docker(self) -> Tuple[bool, str, Optional[str]]:
        """Check if Docker is available (optional).
        
        Returns:
            Tuple of (passed, message, suggestion)
        """
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=5)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, f"Docker available ({version})", None
            else:
                return (True,  # Docker is optional
                       "Docker not available (optional)",
                       "Install Docker for container execution support")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return (True,  # Docker is optional
                   "Docker not found (optional)",
                   "Install Docker from https://docker.com")
            
    def check_project_structure(self) -> Tuple[bool, str, Optional[str]]:
        """Check if essential project directories exist.
        
        Returns:
            Tuple of (passed, message, suggestion)
        """
        required_dirs = [
            'agents',
            'workflows',
            'orchestrator',
            'shared',
            'api'
        ]
        
        missing = []
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                missing.append(dir_name)
                
        if not missing:
            return True, "Project structure intact", None
        else:
            return (False,
                   f"Missing directories: {', '.join(missing)}",
                   "Ensure you're in the project root directory")
            
    def check_generated_dir(self) -> Tuple[bool, str, Optional[str]]:
        """Check if generated directory exists and is writable.
        
        Returns:
            Tuple of (passed, message, suggestion)
        """
        generated_dir = Path('generated')
        
        try:
            # Create if doesn't exist
            generated_dir.mkdir(exist_ok=True)
            
            # Test write permissions
            test_file = generated_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
            
            return True, "Generated directory ready", None
            
        except Exception as e:
            return (False,
                   f"Cannot write to generated directory: {str(e)}",
                   "Check directory permissions or disk space")
    
    def is_orchestrator_running(self, port: int = 8080) -> bool:
        """Check if orchestrator server is running (convenience method).
        
        Args:
            port: Port to check (default 8080)
            
        Returns:
            True if orchestrator is running
        """
        passed, _, _ = self.check_orchestrator_server(port)
        return passed
            
    def run_all_checks(self, skip_optional: bool = False) -> Dict[str, Any]:
        """Run all preflight checks.
        
        Args:
            skip_optional: Whether to skip optional checks
            
        Returns:
            Dictionary with check results
        """
        checks = [
            ("Python Version", self.check_python_version),
            ("Virtual Environment", self.check_virtual_env),
            ("Dependencies", self.check_dependencies),
            ("Project Structure", self.check_project_structure),
            ("Generated Directory", self.check_generated_dir),
            ("Orchestrator Server", self.check_orchestrator_server),
        ]
        
        if not skip_optional:
            checks.extend([
                ("API Server", self.check_api_server),
                ("Docker", self.check_docker),
            ])
            
        results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "checks": []
        }
        
        for name, check_func in checks:
            passed, message, suggestion = check_func()
            
            # Determine status
            if passed:
                if "optional" in message.lower():
                    status = "warning"
                    results["warnings"] += 1
                else:
                    status = "passed"
                    results["passed"] += 1
            else:
                status = "failed"
                results["failed"] += 1
                
            results["checks"].append({
                "name": name,
                "status": status,
                "message": message,
                "suggestion": suggestion
            })
            
        results["all_passed"] = results["failed"] == 0
        return results
        
    def print_results(self, results: Dict[str, Any]):
        """Print check results in a formatted way.
        
        Args:
            results: Results from run_all_checks()
        """
        print("\n🔍 Preflight Checks")
        print("=" * 60)
        
        # Status symbols
        symbols = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️ "
        }
        
        # Print each check
        for check in results["checks"]:
            symbol = symbols.get(check["status"], "  ")
            name = check["name"].ljust(25, '.')
            print(f"{symbol} {name} {check['message']}")
            
        print("=" * 60)
        
        # Summary
        if results["all_passed"]:
            print(f"\n✅ All checks passed! ({results['passed']} passed, {results['warnings']} warnings)")
            print("Ready to run demos!\n")
        else:
            print(f"\n❌ Some checks failed!")
            print(f"   Passed: {results['passed']}")
            print(f"   Failed: {results['failed']}")
            print(f"   Warnings: {results['warnings']}")
            
            # Show suggestions
            print("\n💡 Suggestions:")
            for check in results["checks"]:
                if check["status"] == "failed" and check["suggestion"]:
                    print(f"   • {check['suggestion']}")
            print()


# Convenience function for quick checks
def run_preflight_checks(verbose: bool = False, skip_optional: bool = False) -> bool:
    """Run preflight checks and return success status.
    
    Args:
        verbose: Whether to show verbose output
        skip_optional: Whether to skip optional checks
        
    Returns:
        True if all required checks passed
    """
    checker = PreflightChecker(verbose=verbose)
    results = checker.run_all_checks(skip_optional=skip_optional)
    checker.print_results(results)
    return results["all_passed"]