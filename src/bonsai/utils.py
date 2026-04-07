
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

    # Search root_path and its parents
    for current_path in [root_path] + list(root_path.parents):
        gitignore_path = current_path / ".gitignore"
        if gitignore_path.exists():
            gitignore_files.append(gitignore_path)

    # Also search subdirectories of root_path
    if root_path.is_dir():
        for gitignore_path in root_path.rglob(".gitignore"):
            if gitignore_path not in gitignore_files:
                # Skip .gitignore files inside hidden directories
                try:
                    rel = gitignore_path.parent.relative_to(root_path)
                    if not any(part.startswith('.') for part in rel.parts):
                        gitignore_files.append(gitignore_path)
                except ValueError:
                    pass

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


def _path_match(path_str: str, pattern: str) -> bool:
    """Match path against pattern, respecting that * should not match /"""
    if '**' in pattern:
        # ** matches zero or more directories
        # Try matching with ** expanded to different depths
        pat_parts = pattern.split('/')
        path_parts = path_str.split('/')
        return _match_parts(path_parts, pat_parts)
    # For patterns with /, match component by component so * doesn't cross /
    pat_parts = pattern.split('/')
    path_parts = path_str.split('/')
    if len(pat_parts) != len(path_parts):
        return False
    return all(fnmatch.fnmatch(p, pp) for p, pp in zip(path_parts, pat_parts))


def _match_parts(path_parts: list, pat_parts: list) -> bool:
    """Recursively match path parts against pattern parts with ** support"""
    if not pat_parts and not path_parts:
        return True
    if not pat_parts:
        return False
    if pat_parts[0] == '**':
        # ** matches zero or more path components
        rest_pat = pat_parts[1:]
        for i in range(len(path_parts) + 1):
            if _match_parts(path_parts[i:], rest_pat):
                return True
        return False
    if not path_parts:
        return False
    if fnmatch.fnmatch(path_parts[0], pat_parts[0]):
        return _match_parts(path_parts[1:], pat_parts[1:])
    return False


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
        return _path_match(path_str, pattern)

    # Handle patterns with path separators
    if '/' in pattern:
        return _path_match(path_str, pattern)

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
