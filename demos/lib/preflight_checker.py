"""
Preflight checker for verifying system requirements.
"""
import subprocess
import sys
from typing import List, Tuple, Optional


class PreflightChecker:
    """Checks system requirements before running workflows."""
    
    def __init__(self):
        self.checks = [
            ("Python Version", self._check_python_version, True),
            ("Virtual Environment", self._check_venv, False),
            ("Required Packages", self._check_packages, True),
            ("Docker", self._check_docker, False),
            ("Orchestrator Server", self._check_orchestrator, False),
            ("API Server", self._check_api_server, False)
        ]
        
    def run_all_checks(self, skip_optional: bool = False) -> List[Tuple[str, bool, str]]:
        """Run all preflight checks."""
        results = []
        
        for name, check_func, required in self.checks:
            if skip_optional and not required:
                continue
                
            try:
                success, message = check_func()
                results.append((name, success, message))
            except Exception as e:
                results.append((name, False, str(e)))
                
        return results
        
    def _check_python_version(self) -> Tuple[bool, str]:
        """Check Python version."""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python 3.8+ required (found {version.major}.{version.minor})"
        
    def _check_venv(self) -> Tuple[bool, str]:
        """Check if running in virtual environment."""
        if sys.prefix != sys.base_prefix:
            return True, "Virtual environment active"
        return False, "Not in virtual environment (recommended)"
        
    def _check_packages(self) -> Tuple[bool, str]:
        """Check required packages."""
        required = ['aiohttp', 'pytest', 'pydantic']
        missing = []
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
                
        if not missing:
            return True, "All required packages installed"
        return False, f"Missing packages: {', '.join(missing)}"
        
    def _check_docker(self) -> Tuple[bool, str]:
        """Check Docker availability."""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                return True, "Docker available"
            return False, "Docker not responding"
        except:
            return False, "Docker not installed"
            
    def _check_orchestrator(self) -> Tuple[bool, str]:
        """Check orchestrator server."""
        try:
            import aiohttp
            import asyncio
            
            async def check():
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8080/health', 
                                         timeout=aiohttp.ClientTimeout(total=2)) as resp:
                        return resp.status == 200
                        
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(check())
            loop.close()
            
            if result:
                return True, "Orchestrator server running on port 8080"
            return False, "Orchestrator server not responding"
        except:
            return False, "Orchestrator server not running"
            
    def _check_api_server(self) -> Tuple[bool, str]:
        """Check API server."""
        try:
            import requests
            resp = requests.get('http://localhost:8000/health', timeout=2)
            if resp.status_code == 200:
                return True, "API server running on port 8000"
            return False, "API server not responding"
        except:
            return False, "API server not running"