"""
Session utilities for executor agent.
"""

import hashlib
import os
import re
from datetime import datetime
from typing import Optional

def extract_session_id(input_text: str) -> Optional[str]:
    """Extract session ID from input text if present"""
    lines = input_text.split('\n')
    for line in lines:
        if 'SESSION_ID:' in line:
            return line.split('SESSION_ID:')[1].strip()
    return None

def extract_generated_code_path(input_text: str) -> Optional[str]:
    """Extract generated code path from input text if present"""
    lines = input_text.split('\n')
    for line in lines:
        if 'GENERATED_CODE_PATH:' in line:
            return line.split('GENERATED_CODE_PATH:')[1].strip()
    return None

def generate_dynamic_name(requirements: str, max_length: int = 30) -> str:
    """Generate a dynamic name based on requirements text
    
    Args:
        requirements: The project requirements text
        max_length: Maximum length of the generated name
        
    Returns:
        A cleaned, descriptive name derived from requirements
    """
    # Extract key words from requirements
    # Remove common words and clean up
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                  'before', 'after', 'above', 'below', 'between', 'under', 'create', 'make',
                  'build', 'implement', 'develop', 'write', 'that', 'this', 'these', 'those',
                  'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    # Convert to lowercase and extract words
    words = re.findall(r'\b[a-zA-Z]+\b', requirements.lower())
    
    # Filter out stop words and short words
    meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Get the most relevant words (first few unique words)
    seen = set()
    unique_words = []
    for word in meaningful_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)
            if len(unique_words) >= 3:  # Take up to 3 words
                break
    
    # If no meaningful words found, use a default
    if not unique_words:
        unique_words = ['app']
    
    # Join words with underscores
    name = '_'.join(unique_words)
    
    # Truncate if too long
    if len(name) > max_length:
        name = name[:max_length]
    
    # Clean up any trailing underscores
    name = name.rstrip('_')
    
    return name

def generate_session_id(requirements: Optional[str] = None) -> str:
    """Generate a unique session ID with timestamp prefix and dynamic suffix
    
    Args:
        requirements: Optional requirements text to generate dynamic name from
        
    Returns:
        Session ID in format: YYYYMMDD_HHMMSS_<dynamic_name>_<hash>
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate dynamic name if requirements provided
    if requirements:
        dynamic_name = generate_dynamic_name(requirements)
    else:
        dynamic_name = "app"
    
    # Add a short hash for uniqueness
    random_hash = hashlib.md5(os.urandom(16)).hexdigest()[:6]
    
    return f"{timestamp}_{dynamic_name}_{random_hash}"