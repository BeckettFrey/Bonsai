# File: tests/unit/test_git_integration.py
"""
Tests for Git integration functionality in Bonsai
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile

from bonsai.utils import find_gitignore_files, parse_gitignore, matches_pattern
from bonsai.config import Config
from bonsai.processor import TreeProcessor


class TestGitIntegration:
    """Test Git repository integration"""
    
    def test_find_gitignore_in_git_repo(self):
        """Test finding .gitignore files in a Git repository structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Git repository structure
            git_dir = temp_path / ".git"
            git_dir.mkdir()
            
            # Create nested project structure
            src_dir = temp_path / "src" / "module"
            src_dir.mkdir(parents=True)
            
            # Create .gitignore files at different levels
            root_gitignore = temp_path / ".gitignore"
            src_gitignore = temp_path / "src" / ".gitignore"
            
            root_gitignore.write_text("*.log\n__pycache__/\n")
            src_gitignore.write_text("*.tmp\n")
            
            # Find gitignore files from nested directory
            gitignore_files = find_gitignore_files(src_dir)
            
            # Should find both .gitignore files
            assert len(gitignore_files) == 2
            assert root_gitignore in gitignore_files
            assert src_gitignore in gitignore_files
    
    def test_gitignore_hierarchy(self):
        """Test that .gitignore files are found in proper hierarchy"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create deep directory structure
            deep_dir = temp_path / "a" / "b" / "c" / "d"
            deep_dir.mkdir(parents=True)
            
            # Create .gitignore files at different levels
            gitignore_a = temp_path / "a" / ".gitignore"
            gitignore_c = temp_path / "a" / "b" / "c" / ".gitignore"
            
            gitignore_a.write_text("*.log\n")
            gitignore_c.write_text("*.tmp\n")
            
            # Find gitignore files from deepest directory
            gitignore_files = find_gitignore_files(deep_dir)
            
            # Should find both, ordered from deepest to shallowest
            assert len(gitignore_files) == 2
            assert gitignore_c in gitignore_files
            assert gitignore_a in gitignore_files
    
    def test_common_gitignore_patterns(self):
        """Test common .gitignore patterns used in real projects"""
        common_patterns = [
            # Python patterns
            ("__pycache__", "__pycache__/", True),
            ("src/__pycache__", "__pycache__/", True),
            ("test.pyc", "*.pyc", False),
            ("module.pyo", "*.pyo", False),
            
            # Node.js patterns  
            ("node_modules", "node_modules/", True),
            ("package-lock.json", "package-lock.json", False),
            ("dist", "dist/", True),
            
            # Build patterns
            ("build", "build/", True),
            ("target", "target/", True),
            ("out", "out/", True),
            
            # IDE patterns
            (".vscode", ".vscode/", True),
            (".idea", ".idea/", True),
            ("*.swp", "*.swp", False),
            
            # OS patterns
            (".DS_Store", ".DS_Store", False),
            ("Thumbs.db", "Thumbs.db", False),
            
            # Log patterns
            ("debug.log", "*.log", False),
            ("logs", "logs/", True),
        ]
        
        for path, pattern, is_dir in common_patterns:
            assert matches_pattern(path, pattern, is_dir), f"Pattern '{pattern}' should match '{path}'"
    
    def test_gitignore_negation_patterns(self):
        """Test .gitignore negation patterns (!) work correctly"""
        gitignore_content = """
# Ignore all .log files
*.log

# But keep important.log
!important.log

# Ignore temp directory
temp/

# But keep temp/important/
!temp/important/

# Ignore all .env files
.env*

# But keep .env.example
!.env.example
"""
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("test/.gitignore"))
        
        config = Config(respect_gitignore=False)
        processor = TreeProcessor(config)
        processor.ignore_patterns = set(ignore_patterns)
        processor.include_patterns = set(include_patterns)
        
        # Test that negation patterns work
        assert processor.should_ignore(Path("debug.log"), "debug.log")
        assert not processor.should_ignore(Path("important.log"), "important.log")
        
        assert processor.should_ignore(Path("temp"), "temp")
        assert not processor.should_ignore(Path("temp/important"), "temp/important")
        
        assert processor.should_ignore(Path(".env"), ".env")
        assert processor.should_ignore(Path(".env.local"), ".env.local")
        assert not processor.should_ignore(Path(".env.example"), ".env.example")
    
    def test_gitignore_with_subdirectories(self):
        """Test .gitignore patterns with subdirectories"""
        patterns_and_tests = [
            # Pattern, path, is_dir, should_match
            ("src/", "src", True, True),
            ("src/", "src/file.py", False, False),
            ("src/", "other/src", True, False),
            
            ("*.py", "test.py", False, True),
            ("*.py", "src/test.py", False, True),
            ("*.py", "deep/nested/test.py", False, True),
            
            ("src/*.py", "src/test.py", False, True),
            ("src/*.py", "test.py", False, False),
            ("src/*.py", "src/nested/test.py", False, False),
            
            ("src/**/*.py", "src/test.py", False, True),
            ("src/**/*.py", "src/nested/test.py", False, True),
            ("src/**/*.py", "other/test.py", False, False),
            
            ("/config.json", "config.json", False, True),
            ("/config.json", "src/config.json", False, False),
        ]
        
        for pattern, path, is_dir, should_match in patterns_and_tests:
            result = matches_pattern(path, pattern, is_dir)
            assert result == should_match, f"Pattern '{pattern}' vs path '{path}' (dir={is_dir}): expected {should_match}, got {result}"
    
    def test_processor_with_complex_gitignore(self):
        """Test TreeProcessor with complex .gitignore patterns"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create complex directory structure
            dirs_to_create = [
                "src/main",
                "src/tests", 
                "build/debug",
                "build/release",
                "node_modules/package",
                "dist/js",
                "dist/css",
                ".git/hooks",
                "docs/api",
                "temp/cache"
            ]
            
            for dir_path in dirs_to_create:
                (temp_path / dir_path).mkdir(parents=True)
            
            # Create various files
            files_to_create = [
                "src/main/app.py",
                "src/main/config.py",
                "src/tests/test_app.py",
                "build/debug/app.js",
                "build/release/app.min.js",
                "node_modules/package/index.js",
                "dist/js/bundle.js",
                "dist/css/style.css",
                "docs/api/README.md",
                "temp/cache/data.json",
                "package.json",
                "requirements.txt",
                ".env",
                ".env.example",
                "debug.log",
                "important.log"
            ]
            
            for file_path in files_to_create:
                (temp_path / file_path).write_text("content")
            
            # Create comprehensive .gitignore
            gitignore_content = """
# Dependencies
node_modules/

# Build outputs
build/
dist/

# Environment variables
.env
.env.local
.env.*.local

# Keep example env file
!.env.example

# Logs
*.log

# Keep important logs
!important.log

# Temporary files
temp/
*.tmp
*.cache

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
"""
            
            gitignore_path = temp_path / ".gitignore"
            gitignore_path.write_text(gitignore_content)
            
            # Test with GitIgnore enabled
            config = Config(
                root_path=str(temp_path),
                respect_gitignore=True,
                show_hidden=False
            )
            processor = TreeProcessor(config)
            tree = processor.build_tree(temp_path)
            
            # Get all paths in the tree
            def collect_paths(node, paths=None):
                if paths is None:
                    paths = []
                paths.append(node.name)
                for child in node.children:
                    collect_paths(child, paths)
                return paths
            
            all_paths = collect_paths(tree)
            
            # Should not include ignored directories
            assert "node_modules" not in all_paths
            assert "build" not in all_paths
            assert "dist" not in all_paths
            assert "temp" not in all_paths
            
            # Should include source files
            assert "src" in all_paths
            assert "docs" in all_paths
            
            # Should include allowed files
            assert "package.json" in all_paths
            assert "requirements.txt" in all_paths
            assert ".env.example" in all_paths
            assert "important.log" in all_paths
            
            # Should not include ignored files
            assert ".env" not in all_paths
            assert "debug.log" not in all_paths
    
    def test_no_gitignore_fallback(self):
        """Test behavior when no .gitignore files exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create structure without .gitignore
            (temp_path / "src").mkdir()
            (temp_path / "build").mkdir()
            (temp_path / "src" / "main.py").write_text("print('hello')")
            (temp_path / "build" / "output.js").write_text("console.log('built')")
            
            config = Config(
                root_path=str(temp_path),
                respect_gitignore=True
            )
            processor = TreeProcessor(config)
            tree = processor.build_tree(temp_path)
            
            # Should include all directories since no .gitignore
            child_names = [child.name for child in tree.children]
            assert "src" in child_names
            assert "build" in child_names
    
    def test_gitignore_with_custom_patterns(self):
        """Test combining .gitignore with custom ignore patterns"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test structure
            (temp_path / "src").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "custom").mkdir()
            
            (temp_path / "src" / "main.py").write_text("code")
            (temp_path / "tests" / "test.py").write_text("test")
            (temp_path / "custom" / "file.txt").write_text("custom")
            (temp_path / "temp.log").write_text("log")
            
            # Create .gitignore
            gitignore_content = "*.log\n"
            (temp_path / ".gitignore").write_text(gitignore_content)
            
            # Test with additional custom patterns
            config = Config(
                root_path=str(temp_path),
                respect_gitignore=True,
                custom_ignore_patterns=["custom/"]
            )
            processor = TreeProcessor(config)
            tree = processor.build_tree(temp_path)
            
            child_names = [child.name for child in tree.children]
            
            # Should include src and tests
            assert "src" in child_names
            assert "tests" in child_names
            
            # Should exclude custom (custom pattern) and temp.log (.gitignore)
            assert "custom" not in child_names
            
            # Check that temp.log is not in any child files
            def has_file(node, filename):
                if node.name == filename:
                    return True
                return any(has_file(child, filename) for child in node.children)
            
            assert not has_file(tree, "temp.log")
    
    def test_gitignore_force_include_override(self):
        """Test that force include patterns override .gitignore"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test structure
            (temp_path / "logs").mkdir()
            (temp_path / "logs" / "debug.log").write_text("debug")
            (temp_path / "logs" / "important.log").write_text("important")
            (temp_path / "logs" / "error.log").write_text("error")
            
            # Create .gitignore that ignores all logs
            gitignore_content = "logs/\n*.log\n"
            (temp_path / ".gitignore").write_text(gitignore_content)
            
            # Test with force include for important.log
            config = Config(
                root_path=str(temp_path),
                respect_gitignore=True,
                force_include_patterns=["logs/important.log"]
            )
            processor = TreeProcessor(config)
            tree = processor.build_tree(temp_path)
            
            child_names = [child.name for child in tree.children]
            
            # Should still ignore logs directory due to .gitignore
            assert "logs" not in child_names
            
            # But processor should know not to ignore important.log
            assert not processor.should_ignore(
                Path("logs/important.log"), 
                "logs/important.log"
            )
    
    def test_multiple_gitignore_files_precedence(self):
        """Test precedence when multiple .gitignore files exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested structure
            src_dir = temp_path / "src" / "module"
            src_dir.mkdir(parents=True)
            
            # Create test files
            (temp_path / "test.tmp").write_text("temp")
            (temp_path / "debug.log").write_text("log")
            (src_dir / "test.tmp").write_text("temp")
            (src_dir / "debug.log").write_text("log")
            
            # Create .gitignore at root
            root_gitignore = temp_path / ".gitignore"
            root_gitignore.write_text("*.tmp\n")
            
            # Create .gitignore in src
            src_gitignore = temp_path / "src" / ".gitignore"
            src_gitignore.write_text("*.log\n")
            
            config = Config(
                root_path=str(temp_path),
                respect_gitignore=True
            )
            processor = TreeProcessor(config)
            
            # Both patterns should be active
            assert "*.tmp" in processor.ignore_patterns
            assert "*.log" in processor.ignore_patterns
            
            # Test that both patterns are applied
            assert processor.should_ignore(Path("test.tmp"), "test.tmp")
            assert processor.should_ignore(Path("debug.log"), "debug.log")
            assert processor.should_ignore(Path("src/module/test.tmp"), "src/module/test.tmp")
            assert processor.should_ignore(Path("src/module/debug.log"), "src/module/debug.log")


class TestGitignoreEdgeCases:
    """Test edge cases and special scenarios in .gitignore handling"""
    
    def test_empty_gitignore(self):
        """Test handling of empty .gitignore file"""
        with patch("builtins.open", mock_open(read_data="")):
            ignore_patterns, include_patterns = parse_gitignore(Path("empty/.gitignore"))
        
        assert ignore_patterns == []
        assert include_patterns == []
    
    def test_gitignore_only_comments(self):
        """Test .gitignore with only comments"""
        gitignore_content = """
# This is a comment
# Another comment

# Yet another comment
"""
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("comments/.gitignore"))
        
        assert ignore_patterns == []
        assert include_patterns == []
    
    def test_gitignore_with_trailing_spaces(self):
        """Test .gitignore with trailing spaces"""
        gitignore_content = "*.tmp   \n  *.log\n*.bak  \n"
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("spaces/.gitignore"))
        
        # Should strip trailing spaces
        assert ignore_patterns == ["*.tmp", "*.log", "*.bak"]
    
    def test_gitignore_with_unicode(self):
        """Test .gitignore with unicode characters"""
        gitignore_content = "файл.txt\n测试.log\n🦄.tmp\n"
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("unicode/.gitignore"))
        
        assert "файл.txt" in ignore_patterns
        assert "测试.log" in ignore_patterns
        assert "🦄.tmp" in ignore_patterns
    
    def test_gitignore_with_very_long_patterns(self):
        """Test .gitignore with very long patterns"""
        long_pattern = "a" * 1000 + ".txt"
        gitignore_content = f"{long_pattern}\n"
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("long/.gitignore"))
        
        assert long_pattern in ignore_patterns
    
    def test_gitignore_permission_error(self):
        """Test handling of permission errors when reading .gitignore"""
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            ignore_patterns, include_patterns = parse_gitignore(Path("protected/.gitignore"))
        
        # Should handle gracefully
        assert ignore_patterns == []
        assert include_patterns == []
    
    def test_gitignore_encoding_error(self):
        """Test handling of encoding errors in .gitignore"""
        with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            ignore_patterns, include_patterns = parse_gitignore(Path("encoding/.gitignore"))
        
        # Should handle gracefully
        assert ignore_patterns == []
        assert include_patterns == []
    
    def test_complex_negation_patterns(self):
        """Test complex negation patterns in .gitignore"""
        gitignore_content = """
# Ignore everything in temp
temp/*

# But not temp/important
!temp/important/

# Ignore everything in temp/important
temp/important/*

# But not temp/important/keep.txt
!temp/important/keep.txt

# Ignore all .log files
*.log

# But not in logs/important/
!logs/important/*.log
"""
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("complex/.gitignore"))
        
        expected_ignore = ["temp/*", "temp/important/*", "*.log"]
        expected_include = ["temp/important/", "temp/important/keep.txt", "logs/important/*.log"]
        
        assert ignore_patterns == expected_ignore
        assert include_patterns == expected_include
    
    def test_case_sensitivity(self):
        """Test case sensitivity in pattern matching"""
        # Test case-sensitive matching
        assert matches_pattern("Test.TXT", "*.txt", False) == False
        assert matches_pattern("test.txt", "*.txt", False) == True
        assert matches_pattern("README.MD", "*.md", False) == False
        assert matches_pattern("readme.md", "*.md", False) == True
        
        # Test directory matching
        assert matches_pattern("Build", "build/", True) == False
        assert matches_pattern("build", "build/", True) == True
    
    def test_symlink_handling(self):
        """Test handling of symbolic links"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a real directory and file
            real_dir = temp_path / "real_dir"
            real_dir.mkdir()
            real_file = real_dir / "real_file.txt"
            real_file.write_text("content")
            
            # Create symbolic links (if supported)
            try:
                symlink_dir = temp_path / "symlink_dir"
                symlink_file = temp_path / "symlink_file.txt"
                
                symlink_dir.symlink_to(real_dir)
                symlink_file.symlink_to(real_file)
                
                # Create .gitignore that ignores symlinks
                gitignore_content = "symlink_*\n"
                (temp_path / ".gitignore").write_text(gitignore_content)
                
                config = Config(
                    root_path=str(temp_path),
                    respect_gitignore=True
                )
                processor = TreeProcessor(config)
                
                # Should ignore symlinked files/directories
                assert processor.should_ignore(symlink_dir, "symlink_dir")
                assert processor.should_ignore(symlink_file, "symlink_file.txt")
                
                # Should not ignore real files
                assert not processor.should_ignore(real_file, "real_dir/real_file.txt")
                
            except OSError:
                # Symlinks not supported on this platform, skip test
                pytest.skip("Symbolic links not supported on this platform")


class TestGitignorePerformance:
    """Test performance aspects of .gitignore handling"""
    
    def test_large_gitignore_file(self):
        """Test handling of large .gitignore files"""
        # Create a large .gitignore content
        patterns = []
        for i in range(10000):
            patterns.append(f"pattern_{i:05d}.txt")
            patterns.append(f"dir_{i:05d}/")
        
        gitignore_content = "\n".join(patterns)
        
        with patch("builtins.open", mock_open(read_data=gitignore_content)):
            ignore_patterns, include_patterns = parse_gitignore(Path("large/.gitignore"))
        
        # Should handle large files
        assert len(ignore_patterns) == 20000
        assert "pattern_00000.txt" in ignore_patterns
        assert "dir_09999/" in ignore_patterns
    
    def test_many_gitignore_files(self):
        """Test handling of many .gitignore files in hierarchy"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create deep directory structure with .gitignore at each level
            current_path = temp_path
            for i in range(50):  # 50 levels deep
                current_path = current_path / f"level_{i}"
                current_path.mkdir()
                
                # Create .gitignore at each level
                gitignore = current_path / ".gitignore"
                gitignore.write_text(f"pattern_{i}.txt\n")
            
            # Find all .gitignore files
            gitignore_files = find_gitignore_files(current_path)
            
            # Should find all .gitignore files
            assert len(gitignore_files) == 50
    
    def test_pattern_matching_performance(self):
        """Test pattern matching performance with many patterns"""
        # Create many patterns
        patterns = []
        for i in range(1000):
            patterns.append(f"*.{i:03d}")
            patterns.append(f"dir_{i:03d}/")
        
        config = Config(
            custom_ignore_patterns=patterns,
            respect_gitignore=False
        )
        processor = TreeProcessor(config)
        
        # Test matching against many patterns
        test_paths = [
            ("test.001", "test.001"),
            ("test.999", "test.999"),
            ("test.xyz", "test.xyz"),
            ("dir_500", "dir_500"),
            ("regular_file.txt", "regular_file.txt")
        ]
        
        for path, relative_path in test_paths:
            # This should complete reasonably quickly
            result = processor.should_ignore(Path(path), relative_path)
            # We don't care about the result, just that it completes
            assert isinstance(result, bool)


# Fixtures for Git integration tests
@pytest.fixture
def git_repo_structure():
    """Create a realistic Git repository structure for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create .git directory
        git_dir = temp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]\nrepositoryformatversion = 0")
        
        # Create typical project structure
        directories = [
            "src",
            "tests",
            "docs",
            "build",
            "dist",
            "node_modules/package",
            ".vscode",
            "logs",
            "__pycache__"
        ]
        
        for dir_path in directories:
            (temp_path / dir_path).mkdir(parents=True)
        
        # Create typical files
        files = [
            "README.md",
            "package.json",
            "requirements.txt",
            "setup.py",
            ".env",
            ".env.example",
            "src/main.py",
            "src/config.py",
            "tests/test_main.py",
            "docs/api.md",
            "build/output.js",
            "dist/bundle.js",
            "node_modules/package/index.js",
            ".vscode/settings.json",
            "logs/debug.log",
            "logs/error.log",
            "__pycache__/main.cpython-39.pyc"
        ]
        
        for file_path in files:
            file_obj = temp_path / file_path
            file_obj.parent.mkdir(parents=True, exist_ok=True)
            file_obj.write_text(f"Content of {file_path}")
        
        # Create comprehensive .gitignore
        gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Keep important files
!.env.example
!logs/important.log
"""
        
        (temp_path / ".gitignore").write_text(gitignore_content)
        
        yield temp_path


@pytest.fixture
def sample_gitignore_patterns():
    """Provide sample .gitignore patterns for testing"""
    return {
        "python": [
            "__pycache__/",
            "*.py[cod]",
            "*.so",
            ".Python",
            "build/",
            "dist/",
            "*.egg-info/",
            ".env",
            ".venv/",
            "venv/"
        ],
        "node": [
            "node_modules/",
            "npm-debug.log*",
            "yarn-debug.log*",
            "yarn-error.log*",
            ".env.local",
            ".env.*.local",
            "dist/",
            "build/"
        ],
        "java": [
            "*.class",
            "*.jar",
            "*.war",
            "*.ear",
            "target/",
            ".gradle/",
            "build/",
            "gradle-wrapper.jar"
        ],
        "general": [
            "*.log",
            "*.tmp",
            "*.temp",
            ".DS_Store",
            "Thumbs.db",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo"
        ]
    }


class TestRealWorldScenarios:
    """Test real-world scenarios with Git integration"""
    
    def test_python_project_gitignore(self, git_repo_structure, sample_gitignore_patterns):
        """Test with a typical Python project .gitignore"""
        repo_path = git_repo_structure
        
        # Use Python-specific patterns
        python_patterns = sample_gitignore_patterns["python"]
        gitignore_content = "\n".join(python_patterns)
        (repo_path / ".gitignore").write_text(gitignore_content)
        
        config = Config(
            root_path=str(repo_path),
            respect_gitignore=True
        )
        processor = TreeProcessor(config)
        tree = processor.build_tree(repo_path)
        
        # Collect all paths
        def collect_all_paths(node, paths=None):
            if paths is None:
                paths = []
            paths.append(node.name)
            for child in node.children:
                collect_all_paths(child, paths)
            return paths
        
        all_paths = collect_all_paths(tree)
        
        # Should exclude Python-specific ignored items
        assert "__pycache__" not in all_paths
        assert "build" not in all_paths
        assert "dist" not in all_paths
        
        # Should include source code
        assert "src" in all_paths
        assert "tests" in all_paths
        assert "README.md" in all_paths
    
    def test_mixed_project_gitignore(self, git_repo_structure):
        """Test with a mixed project (Python + Node.js) .gitignore"""
        repo_path = git_repo_structure
        
        # Mixed project .gitignore
        gitignore_content = """
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
dist/
*.egg-info/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*

# General
.env
.vscode/
.idea/
*.log
*.tmp

# OS
.DS_Store
Thumbs.db

# Keep examples
!.env.example
!examples/
"""
        
        (repo_path / ".gitignore").write_text(gitignore_content)
        
        config = Config(
            root_path=str(repo_path),
            respect_gitignore=True
        )
        processor = TreeProcessor(config)
        tree = processor.build_tree(repo_path)
        
        def collect_all_paths(node, paths=None):
            if paths is None:
                paths = []
            paths.append(node.name)
            for child in node.children:
                collect_all_paths(child, paths)
            return paths
        
        all_paths = collect_all_paths(tree)
        
        # Should exclude both Python and Node.js artifacts
        assert "__pycache__" not in all_paths
        assert "node_modules" not in all_paths
        assert "build" not in all_paths
        assert "dist" not in all_paths
        
        # Should include source directories
        assert "src" in all_paths
        assert "tests" in all_paths
        
        # Should include config files
        assert "package.json" in all_paths
        assert "requirements.txt" in all_paths