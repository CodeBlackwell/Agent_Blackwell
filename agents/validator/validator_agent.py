"""
Validator Agent - Lightweight code validation with Docker execution
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
from agents.validator.container_manager import get_container_manager

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
    
    # Pattern to match code blocks with filename
    file_pattern = r'```(?:python|py|javascript|js)\s*\n#\s*filename:\s*(\S+)\n(.*?)```'
    matches = re.findall(file_pattern, input_text, re.DOTALL)
    
    if matches:
        for filename, content in matches:
            files[filename] = content.strip()
    
    return files


async def validator_agent(input: list[Message]) -> AsyncGenerator:
    """
    Lightweight code validator agent that executes code in Docker containers.
    Maintains session persistence for sequential validations.
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
        logger.info(f"🔑 Validator: Created new session: {session_id}")
    else:
        logger.info(f"♻️  Validator: Using existing session: {session_id}")
    
    # Get container manager
    container_manager = get_container_manager()
    
    try:
        # Get or create container for this session
        container = container_manager.get_or_create_container(session_id)
        
        if container:
            logger.info("✅ Validator: Docker connection established")
        else:
            logger.error("❌ Validator: Failed to establish Docker connection")
            yield Message(parts=[MessagePart(
                content=f"SESSION_ID: {session_id}\n\nVALIDATION_RESULT: FAIL\nDETAILS: Failed to establish Docker connection"
            )])
            return
        
        # Extract code files from input
        code_files = extract_code_files(input_text)
        
        if not code_files:
            yield Message(parts=[MessagePart(
                content=f"SESSION_ID: {session_id}\n\nVALIDATION_RESULT: FAIL\nDETAILS: No code found to validate"
            )])
            return
        
        # Execute each file in the container
        all_results = []
        all_errors = []
        
        # Execute all files at once
        try:
            success, stdout, stderr = container_manager.execute_code(
                session_id, 
                code_files
            )
            
            if success:
                all_results.append(f"✅ Code executed successfully")
                if stdout:
                    all_results.append(f"   Output: {stdout}")
            else:
                all_errors.append(f"❌ Execution failed: {stderr}")
        except Exception as e:
            all_errors.append(f"❌ Execution error: {str(e)}")
        
        # Determine overall validation result
        if all_errors:
            validation_result = "FAIL"
            details = "\n".join(all_errors)
        else:
            validation_result = "PASS"
            details = "\n".join(all_results)
        
        # Return validation result
        output = f"""SESSION_ID: {session_id}

VALIDATION_RESULT: {validation_result}
DETAILS: {details}"""
        
        yield Message(parts=[MessagePart(content=output)])
        
    except Exception as e:
        logger.error(f"❌ Validation error: {str(e)}")
        yield Message(parts=[MessagePart(
            content=f"SESSION_ID: {session_id}\n\nVALIDATION_RESULT: FAIL\nDETAILS: Validation error: {str(e)}"
        )])