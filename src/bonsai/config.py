# File: src/bonsai/config.py
"""
Configuration management for Bonsai
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class Config:
    """Configuration settings for Bonsai"""
    
    # Basic settings
    root_path: str = "."
    max_depth: Optional[int] = None
    show_hidden: bool = False
    
    # Display settings
    use_icons: bool = False
    show_size: bool = False
    color_output: bool = True
    
    # Filtering settings
    respect_gitignore: bool = True
    custom_ignore_patterns: List[str] = field(default_factory=list)
    force_include_patterns: List[str] = field(default_factory=list)
    
    # Output settings
    output_file: Optional[str] = None
    output_format: str = "tree"  # tree, json, yaml
    
    @classmethod
    def from_args(cls, args):
        """Create config from command line arguments"""
        return cls(
            root_path=args.path,
            max_depth=args.max_depth,
            show_hidden=args.show_hidden,
            use_icons=args.icons,
            show_size=args.size,
            color_output=not args.no_color,
            respect_gitignore=not args.no_gitignore,
            custom_ignore_patterns=args.ignore or [],
            force_include_patterns=args.include or [],
            output_file=args.output,
            output_format=args.format,
        )
    
    def get_root_path(self) -> Path:
        """Get root path as Path object"""
        return Path(self.root_path).resolve()
    
    def should_show_file(self, file_path: Path) -> bool:
        """Check if file should be shown based on config"""
        if not self.show_hidden and file_path.name.startswith('.'):
            return False
        return True
