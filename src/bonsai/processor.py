# File: src/bonsai/processor.py
"""
Main processing logic for Bonsai
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .config import Config
from .utils import (
    find_gitignore_files, parse_gitignore, matches_pattern,
    get_file_size, format_file_size, get_file_icon, colorize_output
)


@dataclass
class TreeNode:
    """Represents a node in the file tree"""
    path: Path
    name: str
    is_dir: bool
    size: int = 0
    children: List['TreeNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class TreeProcessor:
    """Main processor for generating file trees"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ignore_patterns = set()
        self.include_patterns = set()
        self._load_ignore_patterns()
    
    def _load_ignore_patterns(self):
        """Load ignore patterns from .gitignore files"""
        if not self.config.respect_gitignore:
            return
        
        root_path = self.config.get_root_path()
        gitignore_files = find_gitignore_files(root_path)
        
        for gitignore_file in gitignore_files:
            ignore_pats, include_pats = parse_gitignore(gitignore_file)
            self.ignore_patterns.update(ignore_pats)
            self.include_patterns.update(include_pats)
        
        # Add custom patterns
        self.ignore_patterns.update(self.config.custom_ignore_patterns)
        self.include_patterns.update(self.config.force_include_patterns)
    
    def should_ignore(self, path: Path, relative_path: str) -> bool:
        """Check if path should be ignored"""
        # Check if hidden and not showing hidden files
        if not self.config.show_hidden and path.name.startswith('.'):
            return True
        
        # Check include patterns first (they override ignore patterns)
        for pattern in self.include_patterns:
            if matches_pattern(relative_path, pattern, path.is_dir()):
                return False
        
        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if matches_pattern(relative_path, pattern, path.is_dir()):
                return True
        
        return False
    
    def build_tree(self, root_path: Path, current_depth: int = 0) -> Optional[TreeNode]:
        """Build tree structure starting from root_path"""
        if not root_path.exists():
            return None
        
        # Check depth limit
        if self.config.max_depth is not None and current_depth > self.config.max_depth:
            return None
        
        # Create node
        node = TreeNode(
            path=root_path,
            name=root_path.name,
            is_dir=root_path.is_dir(),
            size=get_file_size(root_path) if root_path.is_file() else 0
        )
        
        # If it's a directory, process children
        if root_path.is_dir():
            try:
                children = []
                config_root = self.config.get_root_path()
                
                for child_path in sorted(root_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                    # Calculate relative path from config root
                    try:
                        relative_path = str(child_path.relative_to(config_root))
                    except ValueError:
                        # If child_path is not relative to config_root, use name
                        relative_path = child_path.name
                    
                    # Check if should ignore
                    if self.should_ignore(child_path, relative_path):
                        continue
                    
                    # Recursively process child
                    child_node = self.build_tree(child_path, current_depth + 1)
                    if child_node:
                        children.append(child_node)
                
                node.children = children
            
            except PermissionError:
                # Can't read directory, leave children empty
                pass
        
        return node
    
    def format_tree(self, node: TreeNode, prefix: str = "", is_last: bool = True) -> List[str]:
        lines = []
        
        connector = "└── " if is_last else "├── "
        display_name = f"{connector}{node.name}/" if node.is_dir else f"{connector}{node.name}"
        
        # Add icon if requested
        if self.config.use_icons:
            icon = get_file_icon(node.path)
            display_name = f"{connector}{icon} {node.name}/" if node.is_dir else f"{connector}{icon} {node.name}"
        
        # Add size if requested
        if self.config.show_size and not node.is_dir:
            size_str = format_file_size(node.size)
            display_name = f"{display_name} ({size_str})"
        
        # Color
        if self.config.color_output:
            if node.is_dir:
                display_name = colorize_output(display_name, 'blue')
            else:
                display_name = colorize_output(display_name, 'white')
        
        lines.append(f"{prefix}{display_name}")
        
        # Process children
        if node.children:
            for i, child in enumerate(node.children):
                is_child_last = (i == len(node.children) - 1)
                child_prefix = prefix + ("    " if is_last else "│   ")
                lines.extend(self.format_tree(child, child_prefix, is_child_last))
        
        return lines

    
    def generate_tree(self) -> List[str]:
        """Generate formatted tree output"""
        root_path = self.config.get_root_path()
        tree = self.build_tree(root_path)
        
        if not tree:
            return [f"Error: Could not access {root_path}"]
        
        return self.format_tree(tree)
    
    def generate_json(self) -> Dict[str, Any]:
        """Generate JSON representation of tree"""
        root_path = self.config.get_root_path()
        tree = self.build_tree(root_path)
        
        if not tree:
            return {"error": f"Could not access {root_path}"}
        
        return self._node_to_dict(tree)
    
    def _node_to_dict(self, node: TreeNode) -> Dict[str, Any]:
        """Convert tree node to dictionary"""
        result = {
            "name": node.name,
            "path": str(node.path),
            "is_dir": node.is_dir,
            "size": node.size
        }
        
        if node.children:
            result["children"] = [self._node_to_dict(child) for child in node.children]
        
        return result