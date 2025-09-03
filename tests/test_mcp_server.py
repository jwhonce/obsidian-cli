import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import frontmatter

from obsidian_cli.main import State


class TestMCPServerComponents(unittest.TestCase):
    """Test cases for MCP server related functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)
        self.state = State(
            vault=self.vault_path,
            editor=Path("vi"),
            ident_key="uid",
            ignored_directories=["Assets/", ".obsidian/", ".git/"],
            journal_template="Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}",
            verbose=False,
        )

    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def create_test_file(self, name, content="Test content", **metadata):
        """Create a test markdown file with frontmatter.

        Args:
            name: Filename (without .md extension)
            content: File content
            **metadata: Frontmatter metadata

        Returns:
            Path to created file
        """
        test_file = self.vault_path / f"{name}.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        post = frontmatter.Post(content, **metadata)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
        return test_file

    def test_mcp_server_imports_available(self):
        """Test that MCP server imports are available (if dependencies are installed)."""
        import importlib.util

        # Check if the mcp_server module can be imported
        spec = importlib.util.find_spec("obsidian_cli.mcp_server")

        if spec is not None:
            try:
                # Try to actually import it to verify dependencies
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # If we get here, MCP dependencies are installed
                self.assertTrue(True)  # Test passes - MCP is available
            except ImportError as e:
                # Module exists but dependencies are missing
                self.assertIn("mcp", str(e).lower(), f"Expected MCP-related import error, got: {e}")
                # Test passes - we successfully detected missing MCP dependencies
        else:
            # Module doesn't exist at all
            self.fail("obsidian_cli.mcp_server module not found")

    def test_state_object_creation(self):
        """Test that State object is properly created for MCP server."""
        self.assertIsInstance(self.state.vault, Path)
        self.assertEqual(self.state.vault, self.vault_path)
        self.assertEqual(self.state.ident_key, "uid")
        self.assertEqual(self.state.ignored_directories, ["Assets/", ".obsidian/", ".git/"])
        self.assertFalse(self.state.verbose)

    def test_vault_path_exists(self):
        """Test that the vault path exists and is accessible."""
        self.assertTrue(self.vault_path.exists())
        self.assertTrue(self.vault_path.is_dir())

    def test_create_test_file_helper(self):
        """Test the create_test_file helper method."""
        test_file = self.create_test_file("helper_test", "Helper content", title="Helper Test")

        self.assertTrue(test_file.exists())
        post = frontmatter.load(test_file)
        self.assertEqual(post.content, "Helper content")
        self.assertEqual(post.metadata["title"], "Helper Test")

    def test_frontmatter_handling(self):
        """Test frontmatter creation and parsing."""
        test_content = "This is test content"
        test_metadata = {"title": "Test Note", "tags": ["test", "example"], "status": "draft"}

        # Create a post
        post = frontmatter.Post(test_content, **test_metadata)

        # Verify post structure
        self.assertEqual(post.content, test_content)
        self.assertEqual(post.metadata["title"], "Test Note")
        self.assertEqual(post.metadata["tags"], ["test", "example"])
        self.assertEqual(post.metadata["status"], "draft")

    def test_file_creation_basic(self):
        """Test basic file creation without MCP dependencies."""
        test_file = self.create_test_file(
            "basic_note", "Basic content", title="Basic Note", status="active"
        )

        # Verify file exists
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.name, "basic_note.md")

        # Verify content
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Basic content", content)
        self.assertIn("title: Basic Note", content)
        self.assertIn("status: active", content)

    def test_nested_directory_creation(self):
        """Test creating files in nested directories."""
        nested_path = "Projects/Ideas"
        test_file = self.vault_path / nested_path / "nested_note.md"

        # Create the directories and file
        test_file.parent.mkdir(parents=True, exist_ok=True)
        post = frontmatter.Post("Nested content", title="Nested Note")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        # Verify structure
        self.assertTrue(test_file.exists())
        self.assertTrue(test_file.parent.exists())

        # Verify content
        loaded_post = frontmatter.load(test_file)
        self.assertEqual(loaded_post.content, "Nested content")
        self.assertEqual(loaded_post.metadata["title"], "Nested Note")

    def test_json_serialization(self):
        """Test JSON serialization of note data."""
        note_data = {
            "path": "test_note.md",
            "content": "Test content",
            "metadata": {"title": "Test Note", "tags": ["test"], "status": "active"},
        }

        # Test JSON serialization
        json_str = json.dumps(note_data)
        parsed_data = json.loads(json_str)

        # Verify data integrity
        self.assertEqual(parsed_data["path"], "test_note.md")
        self.assertEqual(parsed_data["content"], "Test content")
        self.assertEqual(parsed_data["metadata"]["title"], "Test Note")
        self.assertEqual(parsed_data["metadata"]["tags"], ["test"])

    def test_vault_info_structure(self):
        """Test vault information data structure."""
        # Create some test files
        self.create_test_file("note1", "Content 1", tags=["tag1", "tag2"])
        self.create_test_file("note2", "Content 2", tags=["tag2", "tag3"])

        # Create a non-markdown file
        txt_file = self.vault_path / "readme.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("This is a text file")

        # Test basic vault structure
        vault_info = {
            "vault_path": str(self.vault_path),
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "tags": {},
        }

        # Count files manually
        all_files = list(self.vault_path.rglob("*"))
        files_only = [f for f in all_files if f.is_file()]
        vault_info["total_files"] = len(files_only)

        # Verify structure
        self.assertIsInstance(vault_info["vault_path"], str)
        self.assertIsInstance(vault_info["total_files"], int)
        self.assertIsInstance(vault_info["file_types"], dict)
        self.assertIsInstance(vault_info["tags"], dict)
        self.assertGreaterEqual(vault_info["total_files"], 2)

    def test_ignored_directories_logic(self):
        """Test logic for ignoring directories."""
        # Create files in ignored directories
        for ignored_dir in self.state.ignored_directories:
            ignored_path = self.vault_path / ignored_dir.rstrip("/")
            ignored_path.mkdir(exist_ok=True)
            ignored_file = ignored_path / "ignored.md"
            with open(ignored_file, "w", encoding="utf-8") as f:
                f.write("This should be ignored")

        # Create normal file
        normal_file = self.create_test_file("normal", "Normal content")

        # Test filtering logic
        all_files = list(self.vault_path.rglob("*.md"))

        # Filter out ignored directories
        filtered_files = []
        for file_path in all_files:
            relative_path = file_path.relative_to(self.vault_path)
            should_ignore = any(
                str(relative_path).startswith(ignored_dir.rstrip("/"))
                for ignored_dir in self.state.ignored_directories
            )
            if not should_ignore:
                filtered_files.append(file_path)

        # Should only have the normal file
        self.assertEqual(len(filtered_files), 1)
        self.assertEqual(filtered_files[0], normal_file)

    def test_unicode_content_handling(self):
        """Test handling of unicode content."""
        unicode_content = "Content with unicode: 🌟📝💡 and special chars: àáâãäå"
        unicode_metadata = {"title": "Unicode Test", "description": "Test with special characters"}

        test_file = self.create_test_file("unicode_test", unicode_content, **unicode_metadata)

        # Verify file was created and content preserved
        self.assertTrue(test_file.exists())

        loaded_post = frontmatter.load(test_file)
        self.assertEqual(loaded_post.content, unicode_content)
        self.assertEqual(loaded_post.metadata["title"], "Unicode Test")
        self.assertEqual(loaded_post.metadata["description"], "Test with special characters")


if __name__ == "__main__":
    unittest.main()
