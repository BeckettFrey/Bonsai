# File: src/bonsai/__init__.py
"""
Bonsai - A lightweight directory tree visualization tool
"""

__version__ = "0.1.0.dev0"
__author__ = "Beckett Frey"
__email__ = "beckett.frey@gmail.com"

from .cli import cli
from .processor import TreeProcessor
from .config import Config

__all__ = ["cli", "TreeProcessor", "Config"]

