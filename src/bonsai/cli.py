
# File: src/bonsai/cli.py
"""
Command line interface for Bonsai
"""

import argparse
import sys
import json
from pathlib import Path

from .config import Config
from .processor import TreeProcessor


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Bonsai - Elegant directory tree visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bonsai                   # Show current directory
  bonsai /path/to/project   # Show specific directory
  bonsai --max-depth 3      # Limit depth
  bonsai --show-hidden      # Show hidden files
  bonsai --no-gitignore     # Don't respect .gitignore
  bonsai --format json      # Output as JSON
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory path to visualize (default: current directory)"
    )
    
    # Display options
    parser.add_argument(
        "--max-depth", "-d",
        type=int,
        help="Maximum depth to recurse into directories"
    )
    
    parser.add_argument(
        "--show-hidden", "-a",
        action="store_true",
        help="Show hidden files and directories"
    )
    
    parser.add_argument(
        "--icons", "-i",
        action="store_true",
        help="Show file type icons"
    )
    
    parser.add_argument(
        "--size", "-s",
        action="store_true",
        help="Show file sizes"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    # Filtering options
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Don't respect .gitignore patterns"
    )
    
    parser.add_argument(
        "--ignore",
        action="append",
        help="Additional ignore patterns (can be used multiple times)"
    )
    
    parser.add_argument(
        "--include",
        action="append",
        help="Force include patterns (can be used multiple times)"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["tree", "json"],
        default="tree",
        help="Output format (default: tree)"
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0.dev0"
    )
    
    return parser


def cli():
    """Main entry point for the CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate path
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not path.is_dir():
        print(f"Error: Path '{args.path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Create config
    config = Config.from_args(args)
    
    # Create processor
    processor = TreeProcessor(config)
    
    try:
        # Generate output
        if args.format == "json":
            output = json.dumps(processor.generate_json(), indent=2)
        else:
            output = "\n".join(processor.generate_tree())
        
        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Output written to {args.output}")
        else:
            print(output)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Alias for cli() for backward compatibility"""
    cli()


if __name__ == "__main__":
    cli()
