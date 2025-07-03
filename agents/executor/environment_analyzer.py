"""
Environment Analyzer

Parses LLM analysis to determine Docker environment requirements.
"""

import re
from typing import Dict, List
from agents.executor.docker_manager import EnvironmentSpec

def parse_environment_spec(llm_analysis: str) -> EnvironmentSpec:
    """Parse LLM analysis into environment specification"""
    
    # Default values
    language = "python"
    version = "3.9"
    base_image = "python:3.9-slim"
    dependencies = []
    system_packages = []
    build_commands = []
    execution_commands = []
    
    analysis_lower = llm_analysis.lower()
    
    # Detect language
    if "python" in analysis_lower:
        language = "python"
        # Extract version if mentioned
        version_match = re.search(r'python[:\s]+(\d+\.\d+)', analysis_lower)
        if version_match:
            version = version_match.group(1)
        base_image = f"python:{version}-slim"
        
        # Default Python execution commands
        execution_commands = []
        if "pytest" in analysis_lower or "test_" in analysis_lower:
            execution_commands.append("python -m pytest -v")
        if "unittest" in analysis_lower:
            execution_commands.append("python -m unittest discover -v")
        if "app.py" in analysis_lower or "main.py" in analysis_lower:
            execution_commands.append("python app.py || python main.py")
            
    elif "node" in analysis_lower or "javascript" in analysis_lower:
        language = "nodejs"
        # Extract version if mentioned
        version_match = re.search(r'node[:\s]+(\d+)', analysis_lower)
        if version_match:
            version = version_match.group(1)
        else:
            version = "16"
        base_image = f"node:{version}-alpine"
        
        # Default Node.js execution commands
        execution_commands = []
        if "test" in analysis_lower:
            execution_commands.append("npm test")
        if "app.js" in analysis_lower or "index.js" in analysis_lower:
            execution_commands.append("node app.js || node index.js")
    
    elif "java" in analysis_lower:
        language = "java"
        version = "11"
        base_image = "openjdk:11-slim"
        build_commands = ["javac *.java"]
        execution_commands = ["java Main"]
        
    elif "go" in analysis_lower or "golang" in analysis_lower:
        language = "go"
        version = "1.19"
        base_image = "golang:1.19-alpine"
        build_commands = ["go mod init app || true", "go mod tidy || true", "go build -o app"]
        execution_commands = ["./app"]
    
    # Extract dependencies mentioned in analysis
    if "dependencies:" in analysis_lower:
        deps_section = llm_analysis.split("dependencies:")[1].split("\n")[0:10]
        for line in deps_section:
            if line.strip() and not line.strip().startswith('-'):
                break
            if line.strip().startswith('-'):
                dep = line.strip().lstrip('-').strip()
                if dep and len(dep) < 50:  # Sanity check
                    dependencies.append(dep)
    
    # Extract system packages
    if "system packages:" in analysis_lower:
        sys_section = llm_analysis.split("system packages:")[1].split("\n")[0:10]
        for line in sys_section:
            if line.strip() and not line.strip().startswith('-'):
                break
            if line.strip().startswith('-'):
                pkg = line.strip().lstrip('-').strip()
                if pkg and len(pkg) < 50:  # Sanity check
                    system_packages.append(pkg)
    
    # Common system packages for different scenarios
    if language == "python":
        if any(pkg in analysis_lower for pkg in ["numpy", "pandas", "scipy"]):
            system_packages.extend(["gcc", "g++", "gfortran", "libopenblas-dev"])
        if "pillow" in analysis_lower or "image" in analysis_lower:
            system_packages.extend(["libjpeg-dev", "libpng-dev"])
            
    # Extract custom commands if specified
    if "execution commands:" in analysis_lower:
        exec_section = llm_analysis.split("execution commands:")[1].split("\n")[0:10]
        custom_commands = []
        for line in exec_section:
            if line.strip() and not line.strip().startswith('-'):
                break
            if line.strip().startswith('-'):
                cmd = line.strip().lstrip('-').strip()
                if cmd and len(cmd) < 200:  # Sanity check
                    custom_commands.append(cmd)
        if custom_commands:
            execution_commands = custom_commands
    
    # Ensure we have at least one execution command
    if not execution_commands:
        if language == "python":
            execution_commands = ["python --version", "ls -la"]
        elif language == "nodejs":
            execution_commands = ["node --version", "ls -la"]
    
    return EnvironmentSpec(
        language=language,
        version=version,
        base_image=base_image,
        dependencies=dependencies,
        system_packages=system_packages,
        build_commands=build_commands,
        execution_commands=execution_commands
    )

def extract_code_language(code_content: str) -> str:
    """Extract programming language from code content"""
    # Check file extensions in FILENAME: patterns
    if "FILENAME:" in code_content:
        if ".py" in code_content:
            return "python"
        elif ".js" in code_content:
            return "nodejs"
        elif ".java" in code_content:
            return "java"
        elif ".go" in code_content:
            return "go"
    
    # Check code patterns
    code_lower = code_content.lower()
    if "def " in code_lower or "import " in code_lower or "print(" in code_lower:
        return "python"
    elif "function " in code_lower or "const " in code_lower or "require(" in code_lower:
        return "nodejs"
    elif "public class" in code_lower or "public static void main" in code_lower:
        return "java"
    elif "package main" in code_lower or "func main()" in code_lower:
        return "go"
    
    return "unknown"
