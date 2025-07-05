"""
Session utilities for executor agent.
"""

import hashlib
import os
from datetime import datetime
from typing import Optional

def extract_session_id(input_text: str) -> Optional[str]:
    """Extract session ID from input text if present"""
    lines = input_text.split('\n')
    for line in lines:
        if 'SESSION_ID:' in line:
            return line.split('SESSION_ID:')[1].strip()
    return None

def generate_session_id() -> str:
    """Generate a unique session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_hash = hashlib.md5(os.urandom(16)).hexdigest()[:8]
    return f"exec_{timestamp}_{random_hash}"