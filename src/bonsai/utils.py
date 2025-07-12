
# File: src/bonsai/utils.py
"""
Utility functions for Bonsai
"""

import fnmatch
from pathlib import Path
from typing import List, Tuple


def find_gitignore_files(root_path: Path) -> List[Path]:
    """Find all .gitignore files in the directory tree"""
    gitignore_files = []
    
    for current_path in [root_path] + list(root_path.parents):
        gitignore_path = current_path / ".gitignore"
        if gitignore_path.exists():
            gitignore_files.append(gitignore_path)
    
    return gitignore_files


def parse_gitignore(gitignore_path: Path) -> Tuple[List[str], List[str]]:
    """Parse .gitignore file and return (ignore_patterns, include_patterns)"""
    ignore_patterns = []
    include_patterns = []
    
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Handle negation patterns
                if line.startswith('!'):
                    include_patterns.append(line[1:])
                else:
                    ignore_patterns.append(line)
    
    except Exception:
        # Silently ignore errors reading .gitignore
        pass
    
    return ignore_patterns, include_patterns


def matches_pattern(path_str: str, pattern: str, is_dir: bool = False) -> bool:
    """Check if path matches a gitignore pattern"""
    # Handle directory patterns
    if pattern.endswith('/'):
        if not is_dir:
            return False
        pattern = pattern[:-1]
    
    # Handle absolute patterns (starting with /)
    if pattern.startswith('/'):
        pattern = pattern[1:]
        return fnmatch.fnmatch(path_str, pattern)
    
    # Handle patterns with path separators
    if '/' in pattern:
        return fnmatch.fnmatch(path_str, pattern)
    
    # Match against any part of the path
    path_parts = path_str.split('/')
    return any(fnmatch.fnmatch(part, pattern) for part in path_parts)


def get_file_size(path: Path) -> int:
    """Get file size in bytes"""
    try:
        return path.stat().st_size
    except (OSError, IOError):
        return 0


def format_file_size(size: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"


def get_file_icon(path: Path) -> str:
    """Get icon for file based on extension"""
    if path.is_dir():
        return "📁"
    
    extension = path.suffix.lower()
    icon_map = {
        '.py': '🐍',
        '.js': '📜',
        '.ts': '📘',
        '.html': '🌐',
        '.css': '🎨',
        '.json': '📋',
        '.md': '📝',
        '.txt': '📄',
        '.yml': '⚙️',
        '.yaml': '⚙️',
        '.xml': '📰',
        '.png': '🖼️',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.gif': '🖼️',
        '.svg': '🖼️',
    }
    
    return icon_map.get(extension, '📄')


def is_text_file(path: Path) -> bool:
    """Check if file is likely a text file"""
    if not path.is_file():
        return False
    
    # Check by extension first
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json',
        '.xml', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.log',
        '.sql', '.sh', '.bat', '.ps1', '.c', '.cpp', '.h', '.hpp',
        '.java', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'
    }
    
    if path.suffix.lower() in text_extensions:
        return True
    
    # Check by reading first few bytes
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            if not chunk:
                return True
            
            # Check for null bytes (binary indicator)
            if b'\x00' in chunk:
                return False
            
            # Try to decode as UTF-8
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False
    
    except Exception:
        return False


def colorize_output(text: str, color: str) -> str:
    """Add ANSI color codes to text"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'gray': '\033[90m',
        'reset': '\033[0m'
    }
    
    return f"{colors.get(color, '')}{text}{colors['reset']}"
