"""
Utility Helper Functions
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import re
import hashlib
import json


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_hash(data: str) -> str:
    """
    Generate SHA256 hash of string data
    
    Args:
        data: String to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(data.encode()).hexdigest()


def parse_datetime(date_string: str) -> Optional[datetime]:
    """
    Parse datetime string with multiple format support
    
    Args:
        date_string: Date string to parse
        
    Returns:
        Datetime object or None if parsing fails
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return None


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def sanitize_string(text: str) -> str:
    """
    Sanitize string by removing special characters
    
    Args:
        text: String to sanitize
        
    Returns:
        Sanitized string
    """
    return re.sub(r'[^\w\s-]', '', text).strip()


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def format_duration(minutes: int) -> str:
    """
    Format duration in minutes to human readable string
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        Formatted duration string
    """
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def calculate_time_slots(
    start_time: datetime,
    end_time: datetime,
    slot_duration: int
) -> List[datetime]:
    """
    Calculate time slots between start and end time
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        slot_duration: Duration of each slot in minutes
        
    Returns:
        List of datetime slots
    """
    slots = []
    current_time = start_time
    
    while current_time < end_time:
        slots.append(current_time)
        current_time += timedelta(minutes=slot_duration)
    
    return slots


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text (simple implementation)
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords
        
    Returns:
        List of keywords
    """
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'
    }
    
    # Extract words
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    # Filter stop words and count occurrences
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely load JSON string with fallback
    
    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix