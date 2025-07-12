# File: tests/unit/test_ignore_patterns.py
"""
Tests for ignore pattern functionality in Bonsai
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile

from bonsai.utils import (
    find_gitignore_files, parse_gitignore, matches_pattern,
    get_file_size, format_file_size, get_file_icon, is_text_file
)
from bonsai.config import Config
from bonsai.processor import TreeProcessor


class TestIgnorePatterns:
    """Test gitignore pattern matching"""
    
    def test_matches_pattern_simple(self):
        """Test simple pattern matching"""
        assert matches_pattern("test.txt", "*.txt", False)
        assert not matches_pattern("test.py", "*.txt", False)
        assert matches_pattern("node_modules", "node_modules", True)
        assert not matches_pattern("src", "node_modules", True)
    
    def test_matches_pattern_directory(self):
        """Test directory-specific patterns"""
        assert matches_pattern("build", "build/", True)
        assert not matches_pattern("build.txt", "build/", False)
        assert matches_pattern("dist", "dist/", True)
    
    def test_matches_pattern_absolute(self):
        """Test absolute patterns (starting with /)"""
        assert matches_pattern("config.json", "/config.json", False)
        assert not matches_pattern("src/config.json", "/config.json", False)
        assert matches_pattern("build", "/build", True)
    
    def test_matches_pattern_with_path_separator(self):
        """Test patterns with path separators"""
        assert matches_pattern("src/test.py", "src/*.py", False)
        assert matches_pattern("tests/unit/test_utils.py", "tests/*/test_*.py", False)
        assert not matches_pattern("test.py", "src/*.py", False)
    
    def test_matches_pattern_any_part(self):
        """Test patterns that match any part of the path"""
        assert matches_pattern("src/node_modules/package", "node_modules", True)
        assert matches_pattern("deep/nested/temp/file.txt", "temp", True)
        assert matches_pattern("project/build/output.js", "build", True)


class TestGitignoreParser:
    """Test .gitignore file parsing"""
    
    def test_parse_gitignore_basic(self):
        """Test basic .gitignore parsing"""
        gitignore_content = """
# Comments should be ignored
*.pyc
__pycache__/
.env

# More comments
build/
dist/
"""
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("test/.gitignore"))
        
        expected_ignore = ["*.pyc", "__pycache__/", ".env", "build/", "dist/"]
        assert ignore_patterns == expected_ignore
        assert include_patterns == []
    
    def test_parse_gitignore_with_negation(self):
        """Test .gitignore parsing with negation patterns"""
        gitignore_content = """
*.log
!important.log
temp/
!temp/keep.txt
"""
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("test/.gitignore"))
        
        expected_ignore = ["*.log", "temp/"]
        expected_include = ["important.log", "temp/keep.txt"]
        assert ignore_patterns == expected_ignore
        assert include_patterns == expected_include
    
    def test_parse_gitignore_empty_and_whitespace(self):
        """Test .gitignore parsing with empty lines and whitespace"""
        gitignore_content = """

   
*.tmp
   
# Comment with spaces
   *.bak   

"""
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("test/.gitignore"))
        
        expected_ignore = ["*.tmp", "*.bak"]
        assert ignore_patterns == expected_ignore
        assert include_patterns == []
    
    def test_parse_gitignore_file_not_found(self):
        """Test .gitignore parsing when file doesn't exist"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            ignore_patterns, include_patterns = parse_gitignore(Path("nonexistent/.gitignore"))
        
        assert ignore_patterns == []
        assert include_patterns == []


class TestTreeProcessor:
    """Test TreeProcessor ignore functionality"""
    
    def test_should_ignore_hidden_files(self):
        """Test ignoring hidden files when show_hidden is False"""
        config = Config(show_hidden=False)
        processor = TreeProcessor(config)
        
        assert processor.should_ignore(Path(".hidden"), ".hidden")
        assert not processor.should_ignore(Path("visible.txt"), "visible.txt")
    
    def test_should_show_hidden_files(self):
        """Test showing hidden files when show_hidden is True"""
        config = Config(show_hidden=True)
        processor = TreeProcessor(config)
        
        # Should not ignore hidden files due to show_hidden setting
        # But might still ignore due to other patterns
        processor.ignore_patterns = set()
        assert not processor.should_ignore(Path(".hidden"), ".hidden")
    
    def test_custom_ignore_patterns(self):
        """Test custom ignore patterns"""
        config = Config(
            custom_ignore_patterns=["*.tmp", "cache/"],
            respect_gitignore=False
        )
        processor = TreeProcessor(config)
        
        assert processor.should_ignore(Path("temp.tmp"), "temp.tmp")
        assert processor.should_ignore(Path("cache"), "cache")
        assert not processor.should_ignore(Path("source.py"), "source.py")
    
    def test_force_include_patterns(self):
        """Test force include patterns override ignore patterns"""
        config = Config(
            custom_ignore_patterns=["*.log"],
            force_include_patterns=["important.log"],
            respect_gitignore=False
        )
        processor = TreeProcessor(config)
        
        # Should ignore regular log files
        assert processor.should_ignore(Path("debug.log"), "debug.log")
        
        # Should not ignore important.log due to force include
        assert not processor.should_ignore(Path("important.log"), "important.log")
    
    @patch('bonsai.utils.find_gitignore_files')
    @patch('bonsai.utils.parse_gitignore')
    def test_load_ignore_patterns_from_gitignore(self, mock_parse, mock_find):
        """Test loading ignore patterns from .gitignore files"""
        mock_find.return_value = [Path("/project/.gitignore")]
        mock_parse.return_value = (["*.pyc", "__pycache__/"], ["!important.pyc"])
        
        config = Config(respect_gitignore=True)
        processor = TreeProcessor(config)
        
        assert "*.pyc" in processor.ignore_patterns
        assert "__pycache__/" in processor.ignore_patterns
        assert "!important.pyc" in processor.include_patterns
    
    def test_respect_gitignore_disabled(self):
        """Test that .gitignore is not loaded when respect_gitignore is False"""
        config = Config(respect_gitignore=False)
        processor = TreeProcessor(config)
        
        # Should only have custom patterns, not .gitignore patterns
        assert len(processor.ignore_patterns) == 0
        assert len(processor.include_patterns) == 0


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_file_icon(self):
        """Test file icon detection"""
        assert get_file_icon(Path("test.py")) == "🐍"
        assert get_file_icon(Path("test.js")) == "📜"
        assert get_file_icon(Path("test.md")) == "📝"
        assert get_file_icon(Path("test.unknown")) == "📄"
        
        # Test directory
        with patch.object(Path, 'is_dir', return_value=True):
            assert get_file_icon(Path("folder")) == "📁"
    
    def test_format_file_size(self):
        """Test file size formatting"""
        assert format_file_size(0) == "0.0B"
        assert format_file_size(1024) == "1.0KB"
        assert format_file_size(1024 * 1024) == "1.0MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0GB"
        assert format_file_size(500) == "500.0B"
        assert format_file_size(1536) == "1.5KB"
    
    def test_get_file_size(self):
        """Test getting file size"""
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value = Mock(st_size=1024)
            assert get_file_size(Path("test.txt")) == 1024
    
    def test_get_file_size_error(self):
        """Test getting file size when file doesn't exist"""
        with patch.object(Path, 'stat', side_effect=OSError()):
            assert get_file_size(Path("nonexistent.txt")) == 0
    
    def test_is_text_file_by_extension(self):
        """Test text file detection by extension"""
        assert is_text_file(Path("test.txt"))
        assert is_text_file(Path("test.py"))
        assert is_text_file(Path("test.md"))
        assert is_text_file(Path("test.json"))
        
        # Non-text extensions should check content
        with patch.object(Path, 'is_file', return_value=False):
            assert not is_text_file(Path("test.unknown"))
    
    def test_is_text_file_by_content(self):
        """Test text file detection by content"""
        # Mock a file that doesn't have a text extension
        with patch.object(Path, 'is_file', return_value=True):
            with patch.object(Path, 'suffix', ".unknown"):
                with patch("builtins.open", mock_open(read_data=b"Hello World")):
                    assert is_text_file(Path("test.unknown"))
                
                # Test binary content
                with patch("builtins.open", mock_open(read_data=b"\x00\x01\x02")):
                    assert not is_text_file(Path("test.unknown"))
    
    def test_find_gitignore_files(self):
        """Test finding .gitignore files in directory hierarchy"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested directory structure
            nested_dir = temp_path / "project" / "src"
            nested_dir.mkdir(parents=True)
            
            # Create .gitignore files
            root_gitignore = temp_path / ".gitignore"
            project_gitignore = temp_path / "project" / ".gitignore"
            
            root_gitignore.write_text("*.tmp\n")
            project_gitignore.write_text("*.log\n")
            
            # Test finding gitignore files
            gitignore_files = find_gitignore_files(nested_dir)
            
            # Should find both .gitignore files
            assert len(gitignore_files) == 2
            assert project_gitignore in gitignore_files
            assert root_gitignore in gitignore_files


class TestConfig:
    """Test configuration handling"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.root_path == "."
        assert config.max_depth is None
        assert config.show_hidden is False
        assert config.use_icons is False
        assert config.show_size is False
        assert config.color_output is True
        assert config.respect_gitignore is True
        assert config.custom_ignore_patterns == []
        assert config.force_include_patterns == []
        assert config.output_file is None
        assert config.output_format == "tree"
    
    def test_config_from_args(self):
        """Test creating config from command line arguments"""
        # Mock arguments object
        args = Mock()
        args.path = "/test/path"
        args.max_depth = 5
        args.show_hidden = True
        args.icons = True
        args.size = True
        args.no_color = False
        args.no_gitignore = False
        args.ignore = ["*.tmp"]
        args.include = ["important.txt"]
        args.output = "output.txt"
        args.format = "json"
        
        config = Config.from_args(args)
        
        assert config.root_path == "/test/path"
        assert config.max_depth == 5
        assert config.show_hidden is True
        assert config.use_icons is True
        assert config.show_size is True
        assert config.color_output is True
        assert config.respect_gitignore is True
        assert config.custom_ignore_patterns == ["*.tmp"]
        assert config.force_include_patterns == ["important.txt"]
        assert config.output_file == "output.txt"
        assert config.output_format == "json"
    
    def test_get_root_path(self):
        """Test getting root path as Path object"""
        config = Config(root_path="/test/path")
        root_path = config.get_root_path()
        
        assert isinstance(root_path, Path)
        assert root_path.is_absolute()
    
    def test_should_show_file_hidden(self):
        """Test should_show_file with hidden files"""
        config = Config(show_hidden=False)
        
        assert not config.should_show_file(Path(".hidden"))
        assert config.should_show_file(Path("visible.txt"))
        
        config = Config(show_hidden=True)
        assert config.should_show_file(Path(".hidden"))
        assert config.should_show_file(Path("visible.txt"))


# Integration test fixtures
@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create directory structure
        (temp_path / "src").mkdir()
        (temp_path / "tests").mkdir()
        (temp_path / "build").mkdir()
        (temp_path / ".git").mkdir()
        
        # Create files
        (temp_path / "README.md").write_text("# Test Project")
        (temp_path / "requirements.txt").write_text("pytest")
        (temp_path / "src" / "main.py").write_text("print('hello')")
        (temp_path / "tests" / "test_main.py").write_text("def test_main(): pass")
        (temp_path / "build" / "output.js").write_text("console.log('built')")
        (temp_path / ".gitignore").write_text("build/\n*.pyc\n__pycache__/")
        
        yield temp_path


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing"""
    return Config(
        root_path=".",
        max_depth=3,
        show_hidden=False,
        respect_gitignore=True
    )


class TestIntegration:
    """Integration tests using real file system"""
    
    def test_tree_processor_with_gitignore(self, temp_project_dir):
        """Test TreeProcessor respects .gitignore patterns"""
        config = Config(
            root_path=str(temp_project_dir),
            respect_gitignore=True
        )
        processor = TreeProcessor(config)
        
        tree = processor.build_tree(temp_project_dir)
        
        # Should have tree structure
        assert tree is not None
        assert tree.is_dir
        
        # Should not include build directory (ignored by .gitignore)
        child_names = [child.name for child in tree.children]
        assert "build" not in child_names
        assert "src" in child_names
        assert "tests" in child_names
    
    def test_tree_processor_ignore_gitignore(self, temp_project_dir):
        """Test TreeProcessor ignores .gitignore when disabled"""
        config = Config(
            root_path=str(temp_project_dir),
            respect_gitignore=False
        )
        processor = TreeProcessor(config)
        
        tree = processor.build_tree(temp_project_dir)
        
        # Should include build directory (not respecting .gitignore)
        child_names = [child.name for child in tree.children]
        assert "build" in child_names
        assert "src" in child_names
        assert "tests" in child_names
    
    def test_tree_processor_max_depth(self, temp_project_dir):
        """Test TreeProcessor respects max depth"""
        config = Config(
            root_path=str(temp_project_dir),
            max_depth=1,
            respect_gitignore=False
        )
        processor = TreeProcessor(config)
        
        tree = processor.build_tree(temp_project_dir)
        
        # Should have children at depth 1
        assert len(tree.children) > 0
        
        # But children should not have their own children (depth 2)
        for child in tree.children:
            if child.is_dir:
                assert len(child.children) == 0
    
    def test_tree_formatting(self, temp_project_dir):
        """Test tree formatting output"""
        config = Config(
            root_path=str(temp_project_dir),
            respect_gitignore=True
        )
        processor = TreeProcessor(config)
        
        output_lines = processor.generate_tree()
        
        # Should have output
        assert len(output_lines) > 0
        
        # First line should be the root directory
        assert output_lines[0].endswith("/")
        
        # Should contain tree structure symbols
        tree_content = "\n".join(output_lines)
        assert "├──" in tree_content or "└──" in tree_content
    
    def test_json_output(self, temp_project_dir):
        """Test JSON output format"""
        config = Config(
            root_path=str(temp_project_dir),
            respect_gitignore=True
        )
        processor = TreeProcessor(config)
        
        json_output = processor.generate_json()
        
        # Should be a dictionary
        assert isinstance(json_output, dict)
        
        # Should have required keys
        assert "name" in json_output
        assert "path" in json_output
        assert "is_dir" in json_output
        
        # Should have children
        if "children" in json_output:
            assert isinstance(json_output["children"], list)