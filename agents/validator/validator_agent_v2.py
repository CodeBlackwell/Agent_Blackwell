"""
Validator Agent V2 - Enhanced validation with multi-container support
"""
import os
import sys
import re
import hashlib
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from acp_sdk import Message
from acp_sdk.models import MessagePart
from agents.agent_configs import validator_config
from agents.validator.enhanced_validator import create_validator

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_session_id(input_text: str) -> Optional[str]:
    """Extract session ID from input"""
    session_pattern = r'SESSION_ID:\s*([a-zA-Z0-9_\-]+)'
    match = re.search(session_pattern, input_text)
    return match.group(1) if match else None


def extract_code_files(input_text: str) -> Dict[str, str]:
    """Extract code files from input text"""
    files = {}
    
    # Pattern to match code blocks with filename (supporting directory paths)
    file_pattern = r'```(?:\w+)?\s*\n#\s*filename:\s*([^\n]+)\n(.*?)```'
    matches = re.findall(file_pattern, input_text, re.DOTALL)
    
    if matches:
        for filename, content in matches:
            # Clean filename and support paths
            filename = filename.strip()
            files[filename] = content.strip()
    
    return files


def extract_test_commands(input_text: str) -> List[str]:
    """Extract test commands from input"""
    commands = []
    
    # Look for TEST_COMMANDS section
    test_pattern = r'TEST_COMMANDS:\s*\n((?:- .*\n?)+)'
    match = re.search(test_pattern, input_text)
    
    if match:
        commands_text = match.group(1)
        # Extract individual commands
        for line in commands_text.split('\n'):
            if line.strip().startswith('-'):
                cmd = line.strip()[1:].strip()
                if cmd:
                    commands.append(cmd)
    
    return commands


async def validator_agent_v2(input: list[Message]) -> AsyncGenerator:
    """
    Enhanced validator agent with multi-container support.
    Automatically detects and uses docker-compose.yml if present.
    """
    # Extract input text properly from Message objects
    if input and len(input) > 0:
        if hasattr(input[0], 'parts') and len(input[0].parts) > 0:
            input_text = input[0].parts[0].content
        else:
            input_text = str(input[0])
    else:
        input_text = str(input)
    
    # Check for session ID
    session_id = extract_session_id(input_text)
    
    # If no session ID, generate one
    if not session_id:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"val_{timestamp}_{hashlib.md5(input_text.encode()).hexdigest()[:6]}"
        logger.info(f"🔑 Validator V2: Created new session: {session_id}")
    else:
        logger.info(f"♻️  Validator V2: Using existing session: {session_id}")
    
    # Create enhanced validator
    validator = create_validator(session_id)
    
    try:
        # Extract code files from input
        code_files = extract_code_files(input_text)
        
        if not code_files:
            yield Message(parts=[MessagePart(
                content=f"SESSION_ID: {session_id}\n\nVALIDATION_RESULT: FAIL\nDETAILS: No code found to validate"
            )])
            return
        
        # Extract test commands if provided
        test_commands = extract_test_commands(input_text)
        
        # Log what we're validating
        logger.info(f"📁 Files to validate: {list(code_files.keys())}")
        if test_commands:
            logger.info(f"🧪 Test commands: {test_commands}")
        
        # Check if docker-compose.yml is present
        has_compose = any('docker-compose' in f or 'compose.yml' in f for f in code_files.keys())
        if has_compose:
            logger.info("🐳 Docker Compose detected - using multi-container validation")
        
        # Validate code
        success, output = validator.validate_code(code_files, test_commands)
        
        # Determine validation result
        validation_result = "PASS" if success else "FAIL"
        
        # Format output
        result_output = f"""SESSION_ID: {session_id}

VALIDATION_RESULT: {validation_result}
MODE: {"Multi-Container" if has_compose else "Single-Container"}

DETAILS:
{output}"""
        
        yield Message(parts=[MessagePart(content=result_output)])
        
    except Exception as e:
        logger.error(f"❌ Validation error: {str(e)}")
        yield Message(parts=[MessagePart(
            content=f"SESSION_ID: {session_id}\n\nVALIDATION_RESULT: FAIL\nDETAILS: Validation error: {str(e)}"
        )])
    finally:
        # Cleanup session resources
        try:
            validator.cleanup_session()
        except:
            pass