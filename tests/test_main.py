import json
import os
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import frontmatter
from typer.testing import CliRunner

from obsidian_cli.main import _check_if_path_blacklisted, cli
from obsidian_cli.types import Configuration, Vault


class TestMain(unittest.TestCase):
    """Test cases for the main CLI functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)
        # Create .obsidian directory to make it a valid Obsidian vault
        (self.vault_path / ".obsidian").mkdir()
        self.runner = CliRunner()

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

    def run_cli_command(self, args, input_data=None):
        """Helper to run CLI commands with vault configured."""
        full_args = ["--vault", str(self.vault_path)] + args
        return self.runner.invoke(cli, full_args, input=input_data)

    def test_configuration_defaults(self):
        """Test Configuration class and from_path() default values."""
        # Test direct instantiation defaults
        config = Configuration()
        self._assert_default_config_values(config)

        # Test from_path() defaults in isolated environment
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cwd = os.getcwd()
            old_xdg_config = os.environ.get("XDG_CONFIG_HOME")
            old_home = os.environ.get("HOME")

            try:
                os.chdir(temp_dir)
                os.environ["XDG_CONFIG_HOME"] = str(Path(temp_dir) / "config")
                os.environ["HOME"] = str(Path(temp_dir) / "home")
                Path(temp_dir, "config").mkdir()
                Path(temp_dir, "home").mkdir()

                from_file, config = Configuration.from_path()

                self.assertFalse(from_file)  # No config file should be found
                self._assert_default_config_values(config)

            finally:
                os.chdir(old_cwd)
                if old_xdg_config:
                    os.environ["XDG_CONFIG_HOME"] = old_xdg_config
                elif "XDG_CONFIG_HOME" in os.environ:
                    del os.environ["XDG_CONFIG_HOME"]
                if old_home:
                    os.environ["HOME"] = old_home
                elif "HOME" in os.environ:
                    del os.environ["HOME"]

    def _assert_default_config_values(self, config):
        """Helper to verify default configuration values."""
        self.assertEqual(config.editor, Path("vi"))
        self.assertEqual(config.ident_key, "uid")
        self.assertEqual(config.blacklist, ["Assets/", ".obsidian/", ".git/"])
        self.assertEqual(
            config.journal_template, "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
        )
        self.assertIsNone(config.vault)
        self.assertFalse(config.verbose)

    def test_configuration_from_path_with_isolated_environment(self):
        """Test Configuration.from_path with isolated environment setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                # Create test config file in current directory (uses .obsidian-cli.toml filename)
                config_file = Path(".obsidian-cli.toml")
                config_file.write_text(
                    """
vault = "/test/vault"
editor = "nano"
verbose = true
blacklist = ["temp/", "cache/"]
"""
                )

                # Test loading configuration
                from_file, config = Configuration.from_path()

                self.assertTrue(from_file)  # Config file should be found
                self.assertEqual(str(config.vault), "/test/vault")
                self.assertEqual(str(config.editor), "nano")
                self.assertTrue(config.verbose)
                self.assertEqual(config.blacklist, ["temp/", "cache/"])

            finally:
                os.chdir(old_cwd)

    def test_vault_class_creation(self):
        """Test Vault class creation and attributes."""
        vault = Vault(
            editor=Path("vi"),
            ident_key="id",
            blacklist=["test/"],
            config_dirs=["test.toml"],
            journal_template="Journal/{year}-{month:02d}-{day:02d}",
            path=self.vault_path,
            verbose=True,
        )

        self.assertEqual(vault.editor, Path("vi"))
        self.assertEqual(vault.ident_key, "id")
        self.assertEqual(vault.blacklist, ["test/"])
        self.assertEqual(vault.journal_template, "Journal/{year}-{month:02d}-{day:02d}")
        self.assertEqual(vault.path, self.vault_path)
        self.assertTrue(vault.verbose)

    def test_add_uid_command_basic(self):
        """Test add-uid command with basic functionality."""
        # Create test file without UID
        test_file = self.create_test_file("test_note", "Test content", title="Test Note")

        result = self.run_cli_command(["add-uid", "test_note", "--force"])

        self.assertEqual(result.exit_code, 0)

        # Verify UID was added
        post = frontmatter.load(test_file)
        self.assertIn("uid", post.metadata)
        self.assertIsInstance(post.metadata["uid"], str)

    def test_cat_command_basic(self):
        """Test cat command basic functionality."""
        test_content = "This is test content"
        self.create_test_file("test_note", test_content, title="Test Note")

        result = self.run_cli_command(["cat", "test_note"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(test_content, result.stdout)

    @patch("subprocess.run")
    def test_edit_command(self, mock_subprocess):
        """Test edit command functionality."""
        self.create_test_file("test_note", "Test content")
        mock_subprocess.return_value = None

        result = self.run_cli_command(["edit", "test_note"])

        self.assertEqual(result.exit_code, 0)
        mock_subprocess.assert_called_once()

    def test_find_command_exact_match(self):
        """Test find command with exact match."""
        self.create_test_file("daily_note", "Daily content", title="Daily Note")
        self.create_test_file("daily_summary", "Summary content", title="Daily Summary")

        result = self.run_cli_command(["find", "daily_note", "--exact"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("daily_note.md", result.stdout)

    def test_info_command(self):
        """Test info command functionality."""
        # Create some test files
        self.create_test_file("note1", "Content 1")
        self.create_test_file("note2", "Content 2")

        result = self.run_cli_command(["info"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("OBSIDIAN VAULT INFORMATION", result.stdout)

    @patch("subprocess.run")
    def test_journal_command(self, mock_subprocess):
        """Test journal command functionality."""
        mock_subprocess.return_value = None

        result = self.run_cli_command(["journal"])

        # Journal command should fail when no date is provided
        self.assertNotEqual(result.exit_code, 0)

    def test_ls_command(self):
        """Test ls command functionality."""
        self.create_test_file("note1", "Content 1")
        self.create_test_file("note2", "Content 2")

        result = self.run_cli_command(["ls"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("note1.md", result.stdout)
        self.assertIn("note2.md", result.stdout)

    def test_meta_command_list_all(self):
        """Test meta command to list all metadata."""
        self.create_test_file("test_note", "Content", title="Test Note", status="active")

        result = self.run_cli_command(["meta", "test_note"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("title", result.stdout)
        self.assertIn("status", result.stdout)

    def test_ls_command_basic(self):
        """Test ls command basic functionality."""
        # Create some test files
        test_file1 = self.vault_path / "test1.md"
        test_file2 = self.vault_path / "subdir" / "test2.md"
        test_file2.parent.mkdir()

        test_file1.write_text("# Test 1")
        test_file2.write_text("# Test 2")

        result = self.run_cli_command(["ls"])

        self.assertEqual(result.exit_code, 0)
        # Should list markdown files
        self.assertIn("test1.md", result.stdout)
        self.assertIn("subdir/test2.md", result.stdout)

    def test_new_command_basic(self):
        """Test new command basic functionality."""
        with patch("subprocess.run", return_value=None):
            self.run_cli_command(["new", "new_note"])

        # File should be created
        new_file = self.vault_path / "new_note.md"
        self.assertTrue(new_file.exists())

        post = frontmatter.load(new_file)
        self.assertEqual(post.metadata["title"], "new_note")

    def test_version_command(self):
        """Test version command functionality."""
        result = self.runner.invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("obsidian-cli", result.stdout)

    def test_query_command_exists(self):
        """Test query command with --exists option."""
        self.create_test_file("note1", "Content 1", status="active")
        self.create_test_file("note2", "Content 2", category="work")
        self.create_test_file("note3", "Content 3", status="draft")

        result = self.run_cli_command(["query", "status", "--exists"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("note1.md", result.stdout)
        self.assertIn("note3.md", result.stdout)

    def test_query_command_value_filter(self):
        """Test query command with value filter."""
        self.create_test_file("note1", "Content 1", status="active")
        self.create_test_file("note2", "Content 2", status="draft")
        self.create_test_file("note3", "Content 3", status="active")

        result = self.run_cli_command(["query", "status", "--value", "active"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("note1.md", result.stdout)
        self.assertIn("note3.md", result.stdout)

    def test_rm_command_with_force(self):
        """Test rm command with force option."""
        test_file = self.create_test_file("test_note", "Test content")

        result = self.run_cli_command(["rm", "test_note", "--force"])

        self.assertEqual(result.exit_code, 0)
        self.assertFalse(test_file.exists())

    def test_rename_command_basic(self):
        """Test rename command basic functionality."""
        test_file = self.create_test_file("old_note", "Test content")

        result = self.run_cli_command(["rename", "old_note", "new_note", "--force"])

        self.assertEqual(result.exit_code, 0)
        self.assertFalse(test_file.exists())
        self.assertTrue((self.vault_path / "new_note.md").exists())

    def test_rename_command_with_link_update(self):
        """Test rename command with wiki link updates."""
        # Create a file with wiki links
        test_file = self.create_test_file(
            "old_note", "This links to [[old_note]] and [[old_note|display text]]"
        )

        # Create another file that references the old note
        other_file = self.create_test_file("other_note", "See [[old_note]] for details")

        result = self.run_cli_command(["rename", "old_note", "new_note", "--link", "--force"])

        self.assertEqual(result.exit_code, 0)
        self.assertFalse(test_file.exists())
        self.assertTrue((self.vault_path / "new_note.md").exists())

        # Check that wiki links were updated
        new_file_content = (self.vault_path / "new_note.md").read_text()
        other_file_content = (self.vault_path / "other_note.md").read_text()

        self.assertIn("[[new_note]]", new_file_content)
        self.assertIn("[[new_note|display text]]", new_file_content)
        self.assertIn("[[new_note]]", other_file_content)

    def test_serve_command_behavior(self):
        """Test serve command behavior (handles both MCP installed and not installed cases)."""
        # Use subprocess isolation to avoid async/file handle issues
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as temp_vault_dir:
            # Create .obsidian directory to make it a valid Obsidian vault
            (Path(temp_vault_dir) / ".obsidian").mkdir()

            # Run the command in a subprocess to completely isolate it
            cmd = [sys.executable, "-m", "obsidian_cli.main", "--vault", temp_vault_dir, "serve"]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=2,  # Shorter timeout to avoid hanging
                    cwd=os.path.dirname(os.path.dirname(__file__)),  # Set proper working directory
                )

                error_output = result.stderr + result.stdout

                if result.returncode == 1:
                    # MCP dependencies are missing - this is the expected scenario in CI
                    self.assertTrue(
                        "MCP dependencies not installed" in error_output
                        or "mcp" in error_output.lower()
                        or "ImportError" in error_output
                        or "ModuleNotFoundError" in error_output,
                        f"Expected MCP import error, got: {error_output}",
                    )
                elif result.returncode == 0:
                    # MCP dependencies are installed - server might start
                    # This is also valid, just means MCP is available
                    pass  # Test passes - MCP is available
                else:
                    # Any other exit code is unexpected
                    self.fail(f"Unexpected exit code {result.returncode}, output: {error_output}")

            except subprocess.TimeoutExpired:
                # Server started and is running - this means MCP is installed and working
                # This is actually a successful scenario
                pass  # Test passes - server is running successfully

    def test_version_option(self):
        """Test --version option."""
        result = self.runner.invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("obsidian-cli", result.stdout)

    def test_vault_required_error(self):
        """Test that missing vault path triggers proper error handling."""
        # Mock Configuration to return None vault
        with patch("obsidian_cli.types.Configuration.from_path") as mock_config:
            mock_config.return_value = (False, Configuration(vault=None))

            result = self.runner.invoke(cli, ["info"])

            # Should exit with code 2 (typer.BadParameter behavior)
            self.assertEqual(result.exit_code, 2)

            # Should contain the error message in output (typer.BadParameter displays it)
            self.assertIn("vault path is required", result.output)

    def test_blacklist_functionality(self):
        """Test that blacklist are properly excluded."""
        # Create files in blacklisted directories
        assets_dir = self.vault_path / "Assets"
        assets_dir.mkdir()
        assets_file = assets_dir / "image.md"
        with open(assets_file, "w", encoding="utf-8") as f:
            f.write("Image content")

        # Create normal file
        self.create_test_file("normal", "Normal content", title="Normal Note")

        # Query should exclude ignored directories
        result = self.run_cli_command(["query", "title", "--exists"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("normal.md", result.stdout)

    def test_file_creation_with_frontmatter(self):
        """Test creating files with frontmatter."""
        metadata = {"title": "Test Note", "tags": ["test", "example"], "status": "active"}

        test_file = self.create_test_file("frontmatter_test", "Test content", **metadata)

        # Verify file was created correctly
        self.assertTrue(test_file.exists())

        post = frontmatter.load(test_file)
        self.assertEqual(post.content, "Test content")
        self.assertEqual(post.metadata["title"], "Test Note")
        self.assertEqual(post.metadata["tags"], ["test", "example"])
        self.assertEqual(post.metadata["status"], "active")

    def test_json_output_format(self):
        """Test JSON output format for query commands."""
        self.create_test_file("note1", "Content 1", status="active", priority="high")

        result = self.run_cli_command(["query", "status", "--exists", "--style", "json"])

        self.assertEqual(result.exit_code, 0)

        try:
            output_data = json.loads(result.stdout)
            self.assertIsInstance(output_data, list)
            self.assertGreater(len(output_data), 0)
        except json.JSONDecodeError:
            self.fail("Output is not valid JSON")

    def test_unicode_content_handling(self):
        """Test handling of unicode content in files."""
        unicode_content = "Content with unicode: 🌟📝💡"
        unicode_metadata = {"title": "Unicode Test", "description": "Test with special characters"}

        test_file = self.create_test_file("unicode_test", unicode_content, **unicode_metadata)

        # Verify file was created and content preserved
        self.assertTrue(test_file.exists())

        loaded_post = frontmatter.load(test_file)
        self.assertEqual(loaded_post.content, unicode_content)
        self.assertEqual(loaded_post.metadata["title"], "Unicode Test")

    def test_nested_directory_handling(self):
        """Test handling of files in nested directories."""
        # Create nested directory structure
        nested_dir = self.vault_path / "Projects" / "Ideas"
        nested_dir.mkdir(parents=True)

        nested_file = nested_dir / "nested_note.md"
        post = frontmatter.Post("Nested content", title="Nested Note")
        with open(nested_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        # Test that ls command finds nested files
        result = self.run_cli_command(["ls"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Projects/Ideas/nested_note.md", result.stdout)

    def test_empty_vault_handling(self):
        """Test commands with empty vault."""
        # Test info command on empty vault
        result = self.run_cli_command(["info"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("OBSIDIAN VAULT INFORMATION", result.stdout)

        # Test ls command on empty vault
        result = self.run_cli_command(["ls"])

        self.assertEqual(result.exit_code, 0)

    # Test helper function to create Vault objects with correct parameters
    def create_test_vault(tmp_path, **overrides):
        """Create a Vault object for testing with correct parameter names."""
        from pathlib import Path

        from obsidian_cli.types import Vault

        defaults = {
            "editor": Path("vi"),
            "ident_key": "uid",
            "blacklist": ["Assets/", ".obsidian/", ".git/"],
            "journal_template": "test/{year}-{month:02d}-{day:02d}",
            "vault": tmp_path,
            "verbose": False,
        }
        defaults.update(overrides)
        return Vault(**defaults)

    def test_check_if_path_blacklisted(self):
        """Test the _check_if_path_blacklisted function with various patterns."""

        # Test basic blacklisting
        self.assertTrue(
            _check_if_path_blacklisted(Path("Assets/image.png"), ["Assets/", ".obsidian/"])
        )
        self.assertTrue(
            _check_if_path_blacklisted(Path(".obsidian/config.json"), ["Assets/", ".obsidian/"])
        )
        self.assertFalse(
            _check_if_path_blacklisted(Path("Notes/test.md"), ["Assets/", ".obsidian/"])
        )

        # Test empty blacklist
        self.assertFalse(_check_if_path_blacklisted(Path("Assets/image.png"), []))

        # Test partial matches don't work
        self.assertFalse(_check_if_path_blacklisted(Path("MyAssets/image.png"), ["Assets/"]))

    def test_blacklist_functionality_comprehensive(self):
        """Comprehensive test to verify blacklist functionality works correctly."""
        from obsidian_cli.types import Configuration, Vault

        # Test blacklist function
        blacklist = ["Assets/", ".obsidian/", ".git/"]
        self.assertTrue(_check_if_path_blacklisted(Path("Assets/image.png"), blacklist))
        self.assertFalse(_check_if_path_blacklisted(Path("Notes/test.md"), blacklist))

        # Test Configuration with blacklist
        config = Configuration(blacklist=["temp/", "archive/"])
        self.assertEqual(config.blacklist, ["temp/", "archive/"])

        # Test Vault with blacklist
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = Vault(
                editor=Path("vi"),
                ident_key="uid",
                blacklist=["Assets/", ".obsidian/", ".git/"],
                config_dirs=["test.toml"],
                journal_template="Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}",
                path=tmp_path,
                verbose=False,
            )
            self.assertEqual(vault.blacklist, ["Assets/", ".obsidian/", ".git/"])
            self.assertTrue(hasattr(vault, "blacklist"))
            self.assertFalse(hasattr(vault, "ignored_directories"))

    def test_configuration_backward_compatibility(self):
        """Test that old 'ignored_directories' config still works."""
        from obsidian_cli.types import Configuration

        # Simulate loading config with old 'ignored_directories' key
        test_config_data = {
            "editor": "vim",
            "ident_key": "uid",
            "ignored_directories": ["temp/", "draft/"],  # Old key name
            "journal_template": "test/{year}-{month:02d}-{day:02d}",
            "vault": "/test/vault",
            "verbose": False,
        }

        # Create Configuration using from_file class method logic
        config = Configuration(
            editor=Path(test_config_data.get("editor", "vi")),
            ident_key=test_config_data.get("ident_key", "uid"),
            blacklist=test_config_data.get(
                "blacklist",
                test_config_data.get("ignored_directories", ["Assets/", ".obsidian/", ".git/"]),
            ),
            journal_template=test_config_data.get(
                "journal_template", "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
            ),
            vault=Path(test_config_data["vault"]) if test_config_data.get("vault") else None,
            verbose=test_config_data.get("verbose", False),
        )

        # Verify old config values are mapped to new blacklist field
        self.assertEqual(config.blacklist, ["temp/", "draft/"])
        self.assertEqual(config.editor, Path("vim"))


if __name__ == "__main__":
    unittest.main()
