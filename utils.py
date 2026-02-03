# utils.py - Helper functions for the AI Study Assistant

import os
import json
import re
from datetime import datetime

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:-]', '', text)
    
    return text.strip()

def format_timestamp(timestamp=None):
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = datetime.now()
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            return timestamp
    
    return timestamp.strftime("%Y-%m-%d %H:%M")

def calculate_progress_score(correct, total):
    """Calculate progress score (0-100)"""
    if total == 0:
        return 0
    return round((correct / total) * 100, 1)

def safe_json_loads(text, default=None):
    """Safely parse JSON text"""
    if default is None:
        default = {}
    
    try:
        return json.loads(text)
    except:
        return default

def get_file_type(filename):
    """Determine file type from extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    file_types = {
        '.pdf': 'pdf',
        '.ppt': 'ppt',
        '.pptx': 'ppt',
        '.docx': 'docx',
        '.txt': 'txt',
        '.json': 'json'
    }
    
    return file_types.get(ext, 'unknown')