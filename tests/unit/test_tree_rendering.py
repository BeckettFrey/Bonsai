# File: tests/unit/test_header_insertion.py
"""
Tests for header insertion and file content features in Bonsai
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from bonsai.config import Config
from bonsai.processor import TreeProcessor, TreeNode
from bonsai.utils import is_text_file, get_file_size, format_file_size, colorize_output


class TestHeaderInsertion:
    """Test header insertion functionality"""
    
    def test_tree_node_creation(self):
        """Test TreeNode creation with proper attributes"""
        path = Path("/test/file.txt")
        node = TreeNode(
            path=path,
            name="file.txt",
            is_dir=False,
            size=1024
        )
        
        assert node.path == path
        assert node.name == "file.txt"
        assert node.is_dir is False
        assert node.size == 1024
        assert node.children == []
    
    def test_tree_node_directory(self):
        """Test TreeNode for directory"""
        path = Path("/test/dir")
        node = TreeNode(
            path=path,
            name="dir",
            is_dir=True,
            size=0
        )
        
        assert node.path == path
        assert node.name == "dir"
        assert node.is_dir is True
        assert node.size == 0
        assert node.children == []
    
    def test_tree_node_with_children(self):
        """Test TreeNode with children"""
        parent = TreeNode(
            path=Path("/test"),
            name="test",
            is_dir=True
        )
        
        child1 = TreeNode(
            path=Path("/test/file1.txt"),
            name="file1.txt",
            is_dir=False,
            size=100
        )
        
        child2 = TreeNode(
            path=Path("/test/file2.txt"),
            name="file2.txt",
            is_dir=False,
            size=200
        )
        
        parent.children = [child1, child2]
        
        assert len(parent.children) == 2
        assert parent.children[0].name == "file1.txt"
        assert parent.children[1].name == "file2.txt"


class TestTreeFormatting:
    """Test tree formatting and display features"""
    
    def test_format_tree_basic(self):
        """Test basic tree formatting"""
        # Create a simple tree structure
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        file1 = TreeNode(
            path=Path("/project/file1.txt"),
            name="file1.txt",
            is_dir=False,
            size=100
        )
        
        subdir = TreeNode(
            path=Path("/project/subdir"),
            name="subdir",
            is_dir=True
        )
        
        file2 = TreeNode(
            path=Path("/project/subdir/file2.txt"),
            name="file2.txt",
            is_dir=False,
            size=200
        )
        
        subdir.children = [file2]
        root.children = [file1, subdir]
        
        config = Config(use_icons=False, show_size=False, color_output=False)
        processor = TreeProcessor(config)
        
        lines = processor.format_tree(root)
        
        # Should have proper tree structure
        assert len(lines) > 0
        assert "project/" in lines[0]
        assert any("file1.txt" in line for line in lines)
        assert any("subdir/" in line for line in lines)
        assert any("file2.txt" in line for line in lines)
    
    def test_format_tree_with_icons(self):
        """Test tree formatting with icons"""
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        python_file = TreeNode(
            path=Path("/project/main.py"),
            name="main.py",
            is_dir=False,
            size=1024
        )
        
        root.children = [python_file]
        
        config = Config(use_icons=True, color_output=False)
        processor = TreeProcessor(config)
        
        lines = processor.format_tree(root)
        
        # Should include Python icon
        tree_content = "\n".join(lines)
        assert "🐍" in tree_content
        assert "main.py" in tree_content
    
    def test_format_tree_with_sizes(self):
        """Test tree formatting with file sizes"""
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        large_file = TreeNode(
            path=Path("/project/large.txt"),
            name="large.txt",
            is_dir=False,
            size=1048576  # 1MB
        )
        
        root.children = [large_file]
        
        config = Config(show_size=True, color_output=False)
        processor = TreeProcessor(config)
        
        lines = processor.format_tree(root)
        
        # Should include file size
        tree_content = "\n".join(lines)
        assert "1.0MB" in tree_content
        assert "large.txt" in tree_content
    
    def test_format_tree_with_colors(self):
        """Test tree formatting with colors"""
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        directory = TreeNode(
            path=Path("/project/subdir"),
            name="subdir",
            is_dir=True
        )
        
        file = TreeNode(
            path=Path("/project/file.txt"),
            name="file.txt",
            is_dir=False,
            size=100
        )
        
        root.children = [directory, file]
        
        config = Config(color_output=True)
        processor = TreeProcessor(config)
        
        lines = processor.format_tree(root)
        
        # Should include ANSI color codes
        tree_content = "\n".join(lines)
        assert "\033[" in tree_content  # ANSI color codes
        assert "\033[0m" in tree_content  # Reset code
    
    def test_format_tree_structure_symbols(self):
        """Test tree formatting uses proper tree structure symbols"""
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        # Create multiple children to test different symbols
        child1 = TreeNode(
            path=Path("/project/file1.txt"),
            name="file1.txt",
            is_dir=False
        )
        
        child2 = TreeNode(
            path=Path("/project/file2.txt"),
            name="file2.txt",
            is_dir=False
        )
        
        child3 = TreeNode(
            path=Path("/project/file3.txt"),
            name="file3.txt",
            is_dir=False
        )
        
        root.children = [child1, child2, child3]
        
        config = Config(color_output=False)
        processor = TreeProcessor(config)
        
        lines = processor.format_tree(root)
        tree_content = "\n".join(lines)
        
        # Should use proper tree symbols
        assert "├──" in tree_content  # Branch symbol
        assert "└──" in tree_content  # Last item symbol
    
    def test_format_tree_deep_nesting(self):
        """Test tree formatting with deep nesting"""
        # Create deeply nested structure
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        current = root
        for i in range(5):
            child = TreeNode(
                path=Path(f"/project/level{i}"),
                name=f"level{i}",
                is_dir=True
            )
            current.children = [child]
            current = child
        
        # Add final file
        final_file = TreeNode(
            path=Path("/project/final.txt"),
            name="final.txt",
            is_dir=False,
            size=100
        )
        current.children = [final_file]
        
        config = Config(color_output=False)
        processor = TreeProcessor(config)
        
        lines = processor.format_tree(root)
        
        # Should have proper depth and structure
        assert len(lines) > 5  # At least root + 5 levels + final file
        tree_content = "\n".join(lines)
        assert "final.txt" in tree_content
        assert "level0" in tree_content
        assert "level4" in tree_content
    
    def test_format_tree_empty_directory(self):
        """Test formatting of empty directory"""
        root = TreeNode(
            path=Path("/empty"),
            name="empty",
            is_dir=True
        )
        
        config = Config(color_output=False)
        processor = TreeProcessor(config)
        
        lines = processor.format_tree(root)
        
        # Should just show the directory name
        assert len(lines) == 1
        assert "empty/" in lines[0]


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_format_file_size(self):
        """Test file size formatting"""
        assert format_file_size(0) == "0.0B"
        assert format_file_size(512) == "512.0B"
        assert format_file_size(1024) == "1.0KB"
        assert format_file_size(1048576) == "1.0MB"
        assert format_file_size(1073741824) == "1.0GB"
        assert format_file_size(1099511627776) == "1.0TB"
    
    def test_colorize_output(self):
        """Test output colorization"""
        colored = colorize_output("test", "red")
        assert "\033[91m" in colored  # Red color code
        assert "\033[0m" in colored   # Reset code
        assert "test" in colored
        
        # Test unknown color
        colored_unknown = colorize_output("test", "unknown")
        assert "test" in colored_unknown
        assert "\033[0m" in colored_unknown
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'Hello World')
    def test_is_text_file_by_extension(self, mock_file):
        """Test text file detection by extension"""
        assert is_text_file(Path("test.txt")) is True
        assert is_text_file(Path("test.py")) is True
        assert is_text_file(Path("test.js")) is True
        assert is_text_file(Path("test.md")) is True
        assert is_text_file(Path("test.json")) is True
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'\x00\x01\x02')
    def test_is_text_file_binary(self, mock_file):
        """Test binary file detection"""
        # Mock Path.is_file to return True
        with patch.object(Path, 'is_file', return_value=True):
            assert is_text_file(Path("test.unknown")) is False
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'Valid UTF-8 text')
    def test_is_text_file_utf8(self, mock_file):
        """Test UTF-8 text file detection"""
        # Mock Path.is_file to return True and suffix to return unknown
        with patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'suffix', return_value='.unknown'):
            assert is_text_file(Path("test.unknown")) is True
    
    def test_get_file_size_nonexistent(self):
        """Test file size for non-existent file"""
        assert get_file_size(Path("/nonexistent/file.txt")) == 0


class TestConfigFunctionality:
    """Test configuration functionality"""
    
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
        """Test config creation from command line arguments"""
        # Mock arguments
        args = Mock()
        args.path = "/test/path"
        args.max_depth = 3
        args.show_hidden = True
        args.icons = True
        args.size = True
        args.no_color = False
        args.no_gitignore = False
        args.ignore = ["*.log", "*.tmp"]
        args.include = ["important.log"]
        args.output = "output.txt"
        args.format = "json"
        
        config = Config.from_args(args)
        
        assert config.root_path == "/test/path"
        assert config.max_depth == 3
        assert config.show_hidden is True
        assert config.use_icons is True
        assert config.show_size is True
        assert config.color_output is True
        assert config.respect_gitignore is True
        assert config.custom_ignore_patterns == ["*.log", "*.tmp"]
        assert config.force_include_patterns == ["important.log"]
        assert config.output_file == "output.txt"
        assert config.output_format == "json"
    
    def test_config_get_root_path(self):
        """Test root path resolution"""
        config = Config(root_path="/test/path")
        root_path = config.get_root_path()
        
        assert isinstance(root_path, Path)
        assert root_path.is_absolute()
    
    def test_config_should_show_file_hidden(self):
        """Test hidden file visibility logic"""
        config = Config(show_hidden=False)
        assert config.should_show_file(Path(".hidden")) is False
        assert config.should_show_file(Path("visible.txt")) is True
        
        config = Config(show_hidden=True)
        assert config.should_show_file(Path(".hidden")) is True
        assert config.should_show_file(Path("visible.txt")) is True


class TestTreeProcessor:
    """Test tree processor functionality"""
    
    def test_tree_processor_init(self):
        """Test TreeProcessor initialization"""
        config = Config()
        processor = TreeProcessor(config)
        
        assert processor.config == config
        assert isinstance(processor.ignore_patterns, set)
        assert isinstance(processor.include_patterns, set)
    
    def test_should_ignore_hidden_files(self):
        """Test hidden file ignoring logic"""
        config = Config(show_hidden=False)
        processor = TreeProcessor(config)
        
        hidden_file = Path(".hidden")
        visible_file = Path("visible.txt")
        
        assert processor.should_ignore(hidden_file, ".hidden") is True
        assert processor.should_ignore(visible_file, "visible.txt") is False
    
    def test_should_ignore_custom_patterns(self):
        """Test custom ignore patterns"""
        config = Config(custom_ignore_patterns=["*.log", "temp/*"])
        processor = TreeProcessor(config)
        
        log_file = Path("debug.log")
        temp_file = Path("temp/cache.txt")
        normal_file = Path("main.py")
        
        assert processor.should_ignore(log_file, "debug.log") is True
        assert processor.should_ignore(temp_file, "temp/cache.txt") is True
        assert processor.should_ignore(normal_file, "main.py") is False
    
    def test_should_ignore_include_patterns_override(self):
        """Test that include patterns override ignore patterns"""
        config = Config(
            custom_ignore_patterns=["*.log"],
            force_include_patterns=["important.log"]
        )
        processor = TreeProcessor(config)
        
        ignored_log = Path("debug.log")
        included_log = Path("important.log")
        
        assert processor.should_ignore(ignored_log, "debug.log") is True
        assert processor.should_ignore(included_log, "important.log") is False
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=False)
    @patch('pathlib.Path.is_file', return_value=True)
    def test_build_tree_file(self, mock_is_file, mock_is_dir, mock_exists):
        """Test building tree for a single file"""
        config = Config()
        processor = TreeProcessor(config)
        
        file_path = Path("/test/file.txt")
        
        with patch('bonsai_tree.utils.get_file_size', return_value=1024):
            node = processor.build_tree(file_path)
        
        assert node is not None
        assert node.name == "file.txt"
        assert node.is_dir is False
        assert node.size == 1024
        assert node.children == []
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.is_file', return_value=False)
    def test_build_tree_directory(self, mock_is_file, mock_is_dir, mock_exists):
        """Test building tree for a directory"""
        config = Config()
        processor = TreeProcessor(config)
        
        dir_path = Path("/test/dir")
        
        # Mock iterdir to return empty list (empty directory)
        with patch.object(Path, 'iterdir', return_value=[]):
            node = processor.build_tree(dir_path)
        
        assert node is not None
        assert node.name == "dir"
        assert node.is_dir is True
        assert node.size == 0
        assert node.children == []
    
    def test_build_tree_max_depth(self):
        """Test max depth limiting"""
        config = Config(max_depth=0)
        processor = TreeProcessor(config)
        
        # Should return None if current_depth > max_depth
        node = processor.build_tree(Path("/test"), current_depth=1)
        assert node is None
    
    def test_build_tree_nonexistent_path(self):
        """Test building tree for non-existent path"""
        config = Config()
        processor = TreeProcessor(config)
        
        nonexistent_path = Path("/nonexistent/path")
        
        with patch.object(Path, 'exists', return_value=False):
            node = processor.build_tree(nonexistent_path)
        
        assert node is None
    
    def test_generate_json_output(self):
        """Test JSON output generation"""
        # Create a mock tree structure
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        file_node = TreeNode(
            path=Path("/project/file.txt"),
            name="file.txt",
            is_dir=False,
            size=100
        )
        
        root.children = [file_node]
        
        config = Config()
        processor = TreeProcessor(config)
        
        # Mock build_tree to return our test structure
        with patch.object(processor, 'build_tree', return_value=root):
            json_output = processor.generate_json()
        
        assert isinstance(json_output, dict)
        assert json_output["name"] == "project"
        assert json_output["is_dir"] is True
        assert "children" in json_output
        assert len(json_output["children"]) == 1
        assert json_output["children"][0]["name"] == "file.txt"
        assert json_output["children"][0]["is_dir"] is False
        assert json_output["children"][0]["size"] == 100
    
    def test_generate_json_error(self):
        """Test JSON output generation with error"""
        config = Config()
        processor = TreeProcessor(config)
        
        # Mock build_tree to return None (error case)
        with patch.object(processor, 'build_tree', return_value=None):
            json_output = processor.generate_json()
        
        assert isinstance(json_output, dict)
        assert "error" in json_output


class TestGitignoreHandling:
    """Test gitignore pattern handling"""
    
    def test_gitignore_disabled(self):
        """Test when gitignore is disabled"""
        config = Config(respect_gitignore=False)
        processor = TreeProcessor(config)
        
        # Should not load any patterns
        assert len(processor.ignore_patterns) == 0
        assert len(processor.include_patterns) == 0
    
    @patch('bonsai_tree.utils.find_gitignore_files')
    @patch('bonsai_tree.utils.parse_gitignore')
    def test_gitignore_loading(self, mock_parse, mock_find):
        """Test gitignore file loading"""
        # Mock finding gitignore files
        mock_find.return_value = [Path("/.gitignore")]
        
        # Mock parsing gitignore
        mock_parse.return_value = (["*.log", "node_modules/"], ["!important.log"])
        
        config = Config(respect_gitignore=True)
        processor = TreeProcessor(config)
        
        # Should have loaded patterns
        assert "*.log" in processor.ignore_patterns
        assert "node_modules/" in processor.ignore_patterns
        assert "!important.log" in processor.include_patterns
    
    def test_custom_patterns_added(self):
        """Test custom patterns are added to processor"""
        config = Config(
            custom_ignore_patterns=["*.tmp", "cache/"],
            force_include_patterns=["keep.tmp"]
        )
        processor = TreeProcessor(config)
        
        assert "*.tmp" in processor.ignore_patterns
        assert "cache/" in processor.ignore_patterns
        assert "keep.tmp" in processor.include_patterns


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_permission_error_directory(self):
        """Test handling of permission errors when accessing directories"""
        config = Config()
        processor = TreeProcessor(config)
        
        # Mock a directory that raises PermissionError
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.iterdir', side_effect=PermissionError("Access denied")):
            
            node = processor.build_tree(Path("/restricted"))
        
        # Should create node but with empty children
        assert node is not None
        assert node.is_dir is True
        assert node.children == []
    
    def test_file_size_error_handling(self):
        """Test handling of file size errors"""
        with patch('pathlib.Path.stat', side_effect=OSError("File not found")):
            size = get_file_size(Path("/nonexistent/file.txt"))
        
        assert size == 0
    
    def test_generate_tree_error(self):
        """Test error handling in tree generation"""
        config = Config()
        processor = TreeProcessor(config)
        
        # Mock build_tree to return None (error case)
        with patch.object(processor, 'build_tree', return_value=None):
            lines = processor.generate_tree()
        
        assert len(lines) == 1
        assert "Error:" in lines[0]


class TestIntegration:
    """Integration tests for complete functionality"""
    
    def test_full_tree_generation_workflow(self):
        """Test complete tree generation workflow"""
        # Create a mock directory structure
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        # Add various file types
        python_file = TreeNode(
            path=Path("/project/main.py"),
            name="main.py",
            is_dir=False,
            size=2048
        )
        
        readme = TreeNode(
            path=Path("/project/README.md"),
            name="README.md",
            is_dir=False,
            size=1024
        )
        
        src_dir = TreeNode(
            path=Path("/project/src"),
            name="src",
            is_dir=True
        )
        
        util_file = TreeNode(
            path=Path("/project/src/utils.py"),
            name="utils.py",
            is_dir=False,
            size=512
        )
        
        src_dir.children = [util_file]
        root.children = [python_file, readme, src_dir]
        
        # Test with various configurations
        config = Config(
            use_icons=True,
            show_size=True,
            color_output=True,
            max_depth=10
        )
        
        processor = TreeProcessor(config)
        
        # Mock build_tree to return our test structure
        with patch.object(processor, 'build_tree', return_value=root):
            lines = processor.generate_tree()
        
        tree_content = "\n".join(lines)
        
        # Verify all elements are present
        assert "project/" in tree_content
        assert "main.py" in tree_content
        assert "README.md" in tree_content
        assert "src/" in tree_content
        assert "utils.py" in tree_content
        
        # Verify formatting features
        assert "🐍" in tree_content  # Python icon
        assert "📝" in tree_content  # Markdown icon
        assert "2.0KB" in tree_content  # File size
        assert "├──" in tree_content or "└──" in tree_content  # Tree structure
        assert "\033[" in tree_content  # Color codes
    
    def test_json_output_complete(self):
        """Test complete JSON output generation"""
        root = TreeNode(
            path=Path("/project"),
            name="project",
            is_dir=True
        )
        
        file_node = TreeNode(
            path=Path("/project/test.txt"),
            name="test.txt",
            is_dir=False,
            size=256
        )
        
        root.children = [file_node]
        
        config = Config(output_format="json")
        processor = TreeProcessor(config)
        
        with patch.object(processor, 'build_tree', return_value=root):
            json_output = processor.generate_json()
        
        # Verify JSON structure
        assert json_output["name"] == "project"
        assert json_output["is_dir"] is True
        assert json_output["path"] == "/project"
        assert "children" in json_output
        assert len(json_output["children"]) == 1
        
        child = json_output["children"][0]
        assert child["name"] == "test.txt"
        assert child["is_dir"] is False
        assert child["size"] == 256
        assert child["path"] == "/project/test.txt"
    
    def test_filtering_integration(self):
        """Test complete filtering workflow"""
        config = Config(
            show_hidden=False,
            custom_ignore_patterns=["*.log", "temp/"],
            force_include_patterns=["important.log"]
        )
        
        processor = TreeProcessor(config)
        
        # Test various files
        test_cases = [
            (Path(".hidden"), ".hidden", True),  # Hidden file - should ignore
            (Path("visible.txt"), "visible.txt", False),  # Normal file - should not ignore
            (Path("debug.log"), "debug.log", True),  # Log file - should ignore
            (Path("important.log"), "important.log", False),  # Important log - should not ignore
            (Path("temp/cache.txt"), "temp/cache.txt", True),  # Temp file - should ignore
        ]
        
        for file_path, relative_path, expected_ignore in test_cases:
            result = processor.should_ignore(file_path, relative_path)
            assert result == expected_ignore, f"File {relative_path} should {'be ignored' if expected_ignore else 'not be ignored'}"


if __name__ == "__main__":
    pytest.main([__file__])