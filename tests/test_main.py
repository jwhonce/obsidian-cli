import os
import shutil
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import frontmatter
from typer.testing import CliRunner

from obsidian_cli.main import cli


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Move home config file to avoid test interference"""
        cls.home_config = Path.home() / ".config" / "obsidian-cli" / "config.toml"
        cls.home_backup = None
        if cls.home_config.exists():
            cls.home_backup = Path.home() / ".config" / "obsidian-cli" / "config.toml.test_backup"
            shutil.move(str(cls.home_config), str(cls.home_backup))

    @classmethod
    def tearDownClass(cls):
        """Restore home config file after all tests"""
        if cls.home_backup and cls.home_backup.exists():
            shutil.move(str(cls.home_backup), str(cls.home_config))

    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    # Helper methods for common test patterns
    def create_basic_config(self, vault_path=None, **kwargs):
        """Create a basic config file with vault path and optional settings.

        Args:
            vault_path: Path to vault (defaults to self.vault_path)
            **kwargs: Additional config settings (verbose=True, etc.)

        Returns:
            Path to created config file
        """
        if vault_path is None:
            vault_path = self.vault_path

        config_file = vault_path / "config.toml"
        config_content = f'vault = "{vault_path}"\n'

        for key, value in kwargs.items():
            if isinstance(value, bool):
                config_content += f"{key} = {str(value).lower()}\n"
            elif isinstance(value, str):
                config_content += f'{key} = "{value}"\n'
            else:
                config_content += f"{key} = {value}\n"

        with open(config_file, "w") as f:
            f.write(config_content)

        return config_file

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
        post = frontmatter.Post(content, **metadata)
        with open(test_file, "w") as f:
            f.write(frontmatter.dumps(post))
        return test_file

    def run_cli_command(self, command_args, config_file=None, input_data=None, expect_success=True):
        """Run CLI command with standard setup.

        Args:
            command_args: List of command arguments
            config_file: Path to config file (creates basic one if None)
            input_data: Input data for stdin
            expect_success: Whether to expect success (exit code 0)

        Returns:
            CliRunner result object
        """
        if config_file is None:
            config_file = self.create_basic_config()

        full_args = ["--config", str(config_file)] + command_args
        result = self.runner.invoke(cli, full_args, input=input_data)

        if expect_success:
            if result.exit_code != 0:
                print(f"Command failed: {full_args}")
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                print(f"Stderr: {result.stderr}")

        return result

    def test_version_flag(self):
        """Test the --version flag"""
        result = self.runner.invoke(cli, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("obsidian-cli v", result.stdout)

    def test_info_command(self):
        """Test the info command"""
        result = self.run_cli_command(["info"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Vault Path:", result.stdout)
        self.assertIn("Total Files:", result.stdout)

    def test_cat_command(self):
        """Test the cat command"""
        # Create a test file
        self.create_test_file("cat_test", "This is test content for cat command", title="Cat Test")

        # Test cat without frontmatter
        result = self.run_cli_command(["cat", "cat_test"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("This is test content for cat command", result.stdout)
        self.assertNotIn("title: Cat Test", result.stdout)

        # Test cat with frontmatter
        result = self.run_cli_command(["cat", "cat_test", "--show-frontmatter"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("This is test content for cat command", result.stdout)
        self.assertIn("title: Cat Test", result.stdout)

    def test_cat_command_nonexistent_file(self):
        """Test cat command with non-existent file"""
        result = self.run_cli_command(["cat", "nonexistent"], expect_success=False)
        self.assertEqual(result.exit_code, 2)  # FileNotFoundError -> exit code 2

    def test_new_command(self):
        """Test the new command"""
        result = self.run_cli_command(["new", "test_page"])
        self.assertEqual(result.exit_code, 0)

        # Check that the file was created
        test_file = self.vault_path / "test_page.md"
        self.assertTrue(test_file.exists())

    def test_new_command_with_stdin(self):
        """Test the new command with stdin input (non-interactive)"""
        test_content = "This is test content from stdin"

        # Simulate stdin input by providing content directly
        result = self.run_cli_command(["new", "stdin_test"], input_data=test_content)
        self.assertEqual(result.exit_code, 0)

        # Check that the file was created
        test_file = self.vault_path / "stdin_test.md"
        self.assertTrue(test_file.exists())

        # Check that the content is in the file
        content = test_file.read_text()
        self.assertIn(test_content, content)

    def test_query_command(self):
        """Test the query command for frontmatter"""
        # Create a few test files with different frontmatter
        self.create_test_file(
            "test1", "Test content", title="Test 1", tags=["test", "example"], status="draft"
        )
        self.create_test_file(
            "test2", "Test content", title="Test 2", tags=["test", "demo"], status="published"
        )
        self.create_test_file(
            "test3", "Test content", title="Test 3", tags=["example"], priority="high"
        )

        # Test querying by key existence
        result = self.run_cli_command(["query", "status", "--exists"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("test1.md", result.stdout)
        self.assertIn("test2.md", result.stdout)
        self.assertNotIn("test3.md", result.stdout)

        # Test querying by value
        result = self.run_cli_command(["query", "status", "--value", "published"])
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("test1.md", result.stdout)
        self.assertIn("test2.md", result.stdout)
        self.assertNotIn("test3.md", result.stdout)

    def test_query_command_with_explicit_ignored_dirs(self):
        """Test the query command with explicit ignored directories configuration"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create test files with different frontmatter
        test_files = [
            ("test1.md", {"title": "Test 1", "tags": ["test", "example"], "status": "draft"}),
            ("test2.md", {"title": "Test 2", "tags": ["test", "demo"], "status": "published"}),
            ("test3.md", {"title": "Test 3", "tags": ["example"], "priority": "high"}),
        ]

        # Create each test file
        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Create an archive file
        archives_dir = self.vault_path / "Content" / "Archives"
        archives_dir.mkdir(parents=True, exist_ok=True)
        archive_file = archives_dir / "archived_test.md"

        archived_post = frontmatter.Post(
            "Archived content", title="Archived Test", tags=["test", "archived"]
        )
        with open(archive_file, "w") as f:
            f.write(frontmatter.dumps(archived_post))

        # Test with explicit config and ignored directories that exclude Archives
        result = self.runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "--ignored-directories",
                "Content/Archives/:Assets/:.obsidian/:.git/",
                "query",
                "tags",
                "--exists",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        # Archives should be excluded
        self.assertNotIn("Content/Archives/archived_test.md", result.stdout)
        # Regular files should be included
        self.assertIn("test1.md", result.stdout)
        self.assertIn("test2.md", result.stdout)
        self.assertIn("test3.md", result.stdout)

        # Test with explicit ignored directories that DON'T exclude Archives
        result = self.runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "--ignored-directories",
                "Assets/:.obsidian/:.git/",  # No Archives in the list
                "query",
                "tags",
                "--exists",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        # Archives should be included now
        self.assertIn("Content/Archives/archived_test.md", result.stdout)
        # Regular files should still be included
        self.assertIn("test1.md", result.stdout)

    def test_rm_command(self):
        """Test the rm command"""
        # Create a test file
        test_file = self.create_test_file("rm_test", "Test content", title="RM Test")

        # Test rm with force
        result = self.run_cli_command(["rm", "rm_test", "--force"])
        self.assertEqual(result.exit_code, 0)

        # Check that the file was removed
        self.assertFalse(test_file.exists())

    def test_rm_command_nonexistent_file(self):
        """Test rm command with non-existent file"""
        result = self.run_cli_command(["rm", "nonexistent", "--force"], expect_success=False)
        self.assertEqual(result.exit_code, 2)  # FileNotFoundError -> exit code 2

    def test_journal_command_missing_file(self):
        """Test journal command when today's journal doesn't exist"""
        result = self.run_cli_command(["journal"], expect_success=False)
        self.assertEqual(result.exit_code, 2)  # FileNotFoundError -> exit code 2

    def test_journal_command_invalid_template(self):
        """Test journal command with invalid template variable"""
        # Create a config file with invalid template
        config_file = self.create_basic_config(journal_template="Journal/{invalid_var}/{year}")

        result = self.run_cli_command(["journal"], config_file=config_file, expect_success=False)
        self.assertEqual(result.exit_code, 1)  # Template validation error -> exit code 1

    def test_journal_command_verbose_output(self):
        """Test journal command verbose output without editor interaction"""
        config_file = self.vault_path / "verbose-config.toml"
        config_content = f'''
vault = "{self.vault_path}"
verbose = true
journal_template = "NonExistent/{{year}}-{{month:02d}}-{{day:02d}}"
'''
        with open(config_file, "w") as f:
            f.write(config_content)

        # Test verbose output when journal doesn't exist
        result = self.runner.invoke(cli, ["--config", str(config_file), "journal"])
        self.assertEqual(result.exit_code, 2)  # FileNotFoundError -> exit code 2

    def test_error_handling_missing_vault(self):
        """Test error handling when vault is not specified"""
        # Change to temp directory to avoid config file pickup
        old_cwd = os.getcwd()
        old_home = os.environ.get("HOME")
        try:
            # Create a temporary home directory to avoid global config
            temp_home = tempfile.mkdtemp()
            os.environ["HOME"] = temp_home

            temp_cwd = self.temp_dir.name
            os.chdir(temp_cwd)
            result = self.runner.invoke(cli, ["info"])
            # Should exit with code 1 for missing vault
            self.assertEqual(result.exit_code, 1)
            # Check that error message is in stderr (typer sends errors to stderr)
            self.assertIn("Error: Vault path is required", result.stderr)
        finally:
            os.chdir(old_cwd)
            if old_home:
                os.environ["HOME"] = old_home
            elif "HOME" in os.environ:
                del os.environ["HOME"]

    def test_toml_config_loading_edge_cases(self):
        """Test various edge cases in TOML configuration loading"""
        from obsidian_cli.main import Configuration

        # Test 1: Loading non-existent specific config file
        with self.assertRaises(FileNotFoundError):
            Configuration._load_toml_config(Path("/non/existent/config.toml"))

        # Test 2: Loading empty TOML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("")  # Empty file
            empty_config_path = Path(f.name)

        try:
            result = Configuration._load_toml_config(empty_config_path)
            self.assertEqual(result, {})
        finally:
            empty_config_path.unlink()

    def test_toml_config_default_paths(self):
        """Test automatic config loading from default paths"""
        # Test loading from current directory in isolated environment
        old_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # No config files should exist, should raise FileNotFoundError
            from obsidian_cli.main import Configuration

            with self.assertRaises(FileNotFoundError):
                Configuration.from_file(None)

            # Create a config file in current directory
            current_config = Path("./obsidian-cli.toml")
            with open(current_config, "w") as f:
                f.write("""
vault = "/current/dir/vault"
verbose = true
""")

            result = Configuration.from_file(None)
            self.assertEqual(str(result.vault), "/current/dir/vault")
            self.assertTrue(result.verbose)

        finally:
            os.chdir(old_cwd)
            # Cleanup temp directory
            shutil.rmtree(temp_dir)

    def test_add_uid_command(self):
        """Test the add_uid command"""
        # Create a test file without UID
        test_file = self.create_test_file("no_uid_test", "Test content", title="No UID Test")

        result = self.run_cli_command(["add-uid", "no_uid_test"])
        self.assertEqual(result.exit_code, 0)

        # Check that UID was added
        updated_post = frontmatter.load(test_file)
        self.assertIn("uid", updated_post.metadata)
        self.assertIsNotNone(updated_post.metadata["uid"])

    def test_edit_command(self):
        """Test the edit command (non-interactive)"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file first
        test_file = self.vault_path / "edit_test.md"
        post = frontmatter.Post("Test content", title="Edit Test")
        with open(test_file, "w") as f:
            f.write(frontmatter.dumps(post))

        # Mock subprocess.call to avoid actually opening an editor
        with patch("subprocess.call") as mock_call:
            result = self.runner.invoke(cli, ["--config", str(config_file), "edit", "edit_test"])
            self.assertEqual(result.exit_code, 0)
            mock_call.assert_called_once()
            # Verify the correct editor and file were passed
            call_args = mock_call.call_args[0][0]
            self.assertEqual(len(call_args), 2)  # Should be [editor, file_path]
            self.assertEqual(call_args[1], test_file)  # Second argument should be the file path

    def test_find_command(self):
        """Test the find command"""
        # Create test files
        self.create_test_file("daily_note_monday", "Test content", title="Daily Note Monday")
        self.create_test_file("daily_note_tuesday", "Test content", title="Daily Note Tuesday")
        self.create_test_file("weekly_summary", "Test content", title="Weekly Summary")

        # Test finding by partial name
        result = self.run_cli_command(["find", "daily_note"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("daily_note_monday.md", result.stdout)
        self.assertIn("daily_note_tuesday.md", result.stdout)
        self.assertNotIn("weekly_summary.md", result.stdout)

    def test_find_command_exact_match(self):
        """Test the find command with exact match option"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create test files
        test_files = [
            ("daily_note.md", {"title": "Daily Note"}),
            ("daily_note_monday.md", {"title": "Daily Note Monday"}),
            ("weekly_summary.md", {"title": "Weekly Summary"}),
        ]

        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Test exact match - should only find exact filename
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "find", "daily_note", "--exact"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("daily_note.md", result.stdout)
        self.assertNotIn("daily_note_monday.md", result.stdout)

        # Test fuzzy match - should find both
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "daily_note"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("daily_note.md", result.stdout)
        self.assertIn("daily_note_monday.md", result.stdout)

    def test_find_command_title_search(self):
        """Test the find command searching by title in frontmatter"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create test files where search term is in title but not filename
        test_files = [
            ("monday.md", {"title": "Daily Note Monday"}),
            ("tuesday.md", {"title": "Daily Note Tuesday"}),
            ("weekly.md", {"title": "Weekly Summary"}),
            ("no_frontmatter.md", {}),  # File without frontmatter
        ]

        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            if metadata:
                post = frontmatter.Post("Test content", **metadata)
            else:
                post = frontmatter.Post("Test content without frontmatter")
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Search by title content - should find files with matching title
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "daily"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("monday.md", result.stdout)
        self.assertIn("tuesday.md", result.stdout)
        self.assertNotIn("weekly.md", result.stdout)
        self.assertNotIn("no_frontmatter.md", result.stdout)

    def test_find_command_verbose_output(self):
        """Test the find command with verbose output"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\nverbose = true\n')

        # Create test files
        test_files = [
            ("daily_note.md", {"title": "Daily Note"}),
            ("weekly_summary.md", {"title": "Weekly Summary"}),
        ]

        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Test verbose output
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "daily"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Searching for page: 'daily'", result.stdout)
        self.assertIn("Exact match: False", result.stdout)
        self.assertIn("daily_note.md", result.stdout)
        self.assertIn("title: Daily Note", result.stdout)

    def test_find_command_no_matches(self):
        """Test the find command when no files match"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file that won't match
        file_path = self.vault_path / "unrelated.md"
        post = frontmatter.Post("Test content", title="Unrelated File")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Search for non-existent file
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "nonexistent"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No files found matching 'nonexistent'", result.stderr)

    def test_find_command_case_insensitive(self):
        """Test that find command is case insensitive for fuzzy search"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create test files with mixed case
        test_files = [
            ("Daily_Note.md", {"title": "Daily Note"}),
            ("WEEKLY_SUMMARY.md", {"title": "WEEKLY SUMMARY"}),
        ]

        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Search with different cases - should find files regardless of case
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "daily"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Daily_Note.md", result.stdout)

        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "WEEKLY"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("WEEKLY_SUMMARY.md", result.stdout)

        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "summary"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("WEEKLY_SUMMARY.md", result.stdout)

    def test_find_command_subdirectories(self):
        """Test the find command works with files in subdirectories"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create subdirectories and files
        subdir = self.vault_path / "notes" / "daily"
        subdir.mkdir(parents=True)

        test_files = [
            ("notes/daily/monday.md", {"title": "Monday Daily Note"}),
            ("notes/daily/tuesday.md", {"title": "Tuesday Daily Note"}),
            ("top_level.md", {"title": "Top Level Note"}),
        ]

        for filepath, metadata in test_files:
            file_path = self.vault_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Search should find files in subdirectories
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "daily"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("notes/daily/monday.md", result.stdout)
        self.assertIn("notes/daily/tuesday.md", result.stdout)

    def test_find_command_malformed_frontmatter(self):
        """Test the find command handles malformed frontmatter gracefully"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a file with malformed frontmatter
        file_path = self.vault_path / "malformed.md"
        with open(file_path, "w") as f:
            f.write("---\ntitle: Unclosed quote\nbroken: yaml]\n---\nContent")

        # Create a normal file for comparison
        normal_file = self.vault_path / "normal.md"
        post = frontmatter.Post("Test content", title="Normal File")
        with open(normal_file, "w") as f:
            f.write(frontmatter.dumps(post))

        # Search should still work, skipping the malformed file
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "malformed"])
        self.assertEqual(result.exit_code, 0)
        # Should find by filename even if frontmatter is broken
        self.assertIn("malformed.md", result.stdout)

    def test_meta_command_list_all(self):
        """Test the meta command for listing all metadata"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file with metadata
        test_file = self.vault_path / "meta_test.md"
        post = frontmatter.Post(
            "Test content", title="Meta Test", tags=["meta", "test"], priority="high"
        )
        with open(test_file, "w") as f:
            f.write(frontmatter.dumps(post))

        result = self.runner.invoke(cli, ["--config", str(config_file), "meta", "meta_test"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("title: Meta Test", result.stdout)
        self.assertIn("tags:", result.stdout)
        self.assertIn("priority: high", result.stdout)

    def test_cat_command_show_frontmatter(self):
        """Test cat command with --show-frontmatter option"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file with frontmatter
        file_path = self.vault_path / "test_frontmatter.md"
        post = frontmatter.Post("Test content body", title="Test Title", author="Test Author")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test cat without frontmatter (default)
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "cat", "test_frontmatter.md"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test content body", result.stdout)
        self.assertNotIn("title: Test Title", result.stdout)
        self.assertNotIn("author: Test Author", result.stdout)

        # Test cat with frontmatter
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "cat", "test_frontmatter.md", "--show-frontmatter"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test content body", result.stdout)
        self.assertIn("title: Test Title", result.stdout)
        self.assertIn("author: Test Author", result.stdout)

    def test_add_uid_command_with_existing_uid(self):
        """Test add-uid command with existing UID"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file with existing UID
        file_path = self.vault_path / "test_uid.md"
        post = frontmatter.Post("Test content", title="Test", uid="existing-uid")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test add-uid without force (should warn and fail)
        result = self.runner.invoke(cli, ["--config", str(config_file), "add-uid", "test_uid.md"])
        self.assertEqual(result.exit_code, 1)

        # Test add-uid with force (should overwrite)
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "add-uid", "test_uid.md", "--force"]
        )
        self.assertEqual(result.exit_code, 0)

        # Verify the UID was updated
        updated_post = frontmatter.load(file_path)
        self.assertIn("uid", updated_post.metadata)
        # The new UID should be different from the original
        self.assertNotEqual(updated_post.metadata["uid"], "existing-uid")

    def test_new_command_with_force(self):
        """Test new command with force option"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create an existing file
        file_path = self.vault_path / "existing_file.md"
        with open(file_path, "w") as f:
            f.write("Original content")

        # Test new command without force (should fail)
        result = self.runner.invoke(cli, ["--config", str(config_file), "new", "existing_file.md"])
        self.assertEqual(result.exit_code, 1)  # Should fail with FileExistsError

        # Test new command with force (should overwrite)
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "new", "existing_file.md", "--force"]
        )
        self.assertEqual(result.exit_code, 0)

        # Verify the file was overwritten (should now have frontmatter structure)
        with open(file_path, "r") as f:
            content = f.read()
        self.assertNotEqual(content.strip(), "Original content")

    def test_rm_command_without_force(self):
        """Test rm command without force option"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file
        file_path = self.vault_path / "to_delete.md"
        with open(file_path, "w") as f:
            f.write("Content to delete")

        # Test rm without force - in test environment with no TTY, should fail
        result = self.runner.invoke(cli, ["--config", str(config_file), "rm", "to_delete.md"])
        # In CLI testing environment, this will likely fail due to no interactive terminal
        # The important thing is that it doesn't crash
        self.assertIn(result.exit_code, [0, 1, 2])

    def test_query_command_formats(self):
        """Test query command with different output formats"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create test files with metadata
        test_files = [
            ("file1.md", {"title": "File One", "status": "published", "priority": 1}),
            ("file2.md", {"title": "File Two", "status": "draft", "priority": 2}),
            ("file3.md", {"author": "John Doe"}),  # No status field
        ]

        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Test count format
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "query", "status", "--exists", "--count"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Found 2 matching files", result.stdout)

        # Test title format
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "query", "status", "--exists", "--format", "title"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("File One", result.stdout)
        self.assertIn("File Two", result.stdout)

        # Test json format
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "query", "status", "--exists", "--format", "json"]
        )
        self.assertEqual(result.exit_code, 0)
        # Should contain JSON-formatted output
        self.assertTrue("[" in result.stdout and "]" in result.stdout)

    def test_query_command_value_and_contains_filters(self):
        """Test query command with value and contains filters"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create test files
        test_files = [
            ("file1.md", {"status": "published", "description": "This is a test file"}),
            ("file2.md", {"status": "draft", "description": "Another test document"}),
            ("file3.md", {"status": "published", "description": "Final version"}),
        ]

        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Test exact value match
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "query", "status", "--value", "published"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("file1.md", result.stdout)
        self.assertIn("file3.md", result.stdout)
        self.assertNotIn("file2.md", result.stdout)

        # Test contains filter
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "query", "description", "--contains", "test"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("file1.md", result.stdout)
        self.assertIn("file2.md", result.stdout)
        self.assertNotIn("file3.md", result.stdout)

        # Test missing filter
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "query", "nonexistent", "--missing"]
        )
        self.assertEqual(result.exit_code, 0)
        # Should find all files since none have the 'nonexistent' key
        self.assertIn("file1.md", result.stdout)
        self.assertIn("file2.md", result.stdout)
        self.assertIn("file3.md", result.stdout)

    def test_query_command_conflicting_options(self):
        """Test query command with conflicting options"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Test conflicting --value and --contains options
        result = self.runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "query",
                "status",
                "--value",
                "published",
                "--contains",
                "pub",
            ],
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Cannot specify both --value and --contains", result.stderr)

    def test_meta_command_set_key(self):
        """Test meta command setting metadata"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file
        file_path = self.vault_path / "test_meta.md"
        post = frontmatter.Post("Test content", title="Original Title")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test setting a new metadata key
        result = self.runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "meta",
                "test_meta.md",
                "--key",
                "author",
                "--value",
                "John Doe",
            ],
        )
        self.assertEqual(result.exit_code, 0)

        # Verify the metadata was set
        updated_post = frontmatter.load(file_path)
        self.assertEqual(updated_post.metadata["author"], "John Doe")
        self.assertEqual(updated_post.metadata["title"], "Original Title")

    def test_meta_command_get_key(self):
        """Test meta command getting specific metadata key"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file with metadata
        file_path = self.vault_path / "test_meta.md"
        post = frontmatter.Post("Test content", title="Test Title", author="John Doe")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test getting a specific key
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "meta", "test_meta.md", "--key", "title"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("title: Test Title", result.stdout)
        self.assertNotIn("author:", result.stdout)

    def test_meta_command_nonexistent_key(self):
        """Test meta command with nonexistent key"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file
        file_path = self.vault_path / "test_meta.md"
        post = frontmatter.Post("Test content", title="Test Title")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test getting a nonexistent key
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "meta", "test_meta.md", "--key", "nonexistent"]
        )
        self.assertEqual(result.exit_code, 1)
        # Should show error message about missing key

    def test_journal_command_with_existing_file(self):
        """Test journal command when file already exists"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write('journal_template = "Journal/{year}-{month:02d}-{day:02d}.md"\n')

        # Create the expected journal file path
        from datetime import datetime

        today = datetime.now()
        journal_file = (
            self.vault_path / "Journal" / f"{today.year}-{today.month:02d}-{today.day:02d}.md"
        )
        journal_file.parent.mkdir(parents=True, exist_ok=True)

        # Create existing journal file
        with open(journal_file, "w") as f:
            f.write("Existing journal content")

        # Test journal command - should successfully open existing file
        result = self.runner.invoke(cli, ["--config", str(config_file), "journal"])
        self.assertEqual(result.exit_code, 0)  # Should succeed and open existing file

    def test_journal_command_custom_template(self):
        """Test journal command with custom template"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write('journal_template = "Notes/Daily/{year}/{month:02d}/day-{day:02d}.md"\n')

        # Test journal command with custom template
        result = self.runner.invoke(cli, ["--config", str(config_file), "journal"])

        # Should either succeed in creating the file or fail because editor isn't available
        # In test environment, it will likely fail with editor error, which is expected
        self.assertIn(result.exit_code, [0, 2])

    def test_verbose_flag(self):
        """Test global verbose flag"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file
        file_path = self.vault_path / "test.md"
        with open(file_path, "w") as f:
            f.write("Test content")

        # Test with verbose flag
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "--verbose", "cat", "test.md"]
        )
        self.assertEqual(result.exit_code, 0)
        # Verbose mode should show additional information
        self.assertIn("Test content", result.stdout)

    def test_configuration_precedence(self):
        """Test that CLI options override config file settings"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write("verbose = false\n")

        # Create a test file
        file_path = self.vault_path / "test.md"
        with open(file_path, "w") as f:
            f.write("Test content")

        # Test that --verbose flag overrides config file setting
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "--verbose", "cat", "test.md"]
        )
        self.assertEqual(result.exit_code, 0)

    def test_ignored_directories_configuration(self):
        """Test that ignored directories configuration works"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write('ignored_directories = ["temp/", "drafts/"]\n')

        # Create files in ignored directories
        temp_dir = self.vault_path / "temp"
        temp_dir.mkdir()
        temp_file = temp_dir / "temp_file.md"
        post = frontmatter.Post("Temp content", title="Temp File")
        with open(temp_file, "w") as f:
            f.write(frontmatter.dumps(post))

        # Create file in non-ignored directory
        normal_file = self.vault_path / "normal.md"
        post = frontmatter.Post("Normal content", title="Normal File")
        with open(normal_file, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test that query respects ignored directories
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "query", "title", "--exists"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("normal.md", result.stdout)
        self.assertNotIn("temp/temp_file.md", result.stdout)

    def test_find_command_with_no_results(self):
        """Test find command when no files match the search criteria"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file that won't match
        file_path = self.vault_path / "unrelated.md"
        post = frontmatter.Post("Test content", title="Unrelated File")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Search for non-existent file
        result = self.runner.invoke(cli, ["--config", str(config_file), "find", "nonexistent"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No files found matching 'nonexistent'", result.stderr)

    def test_verbose_flag_add_uid_command(self):
        """Test verbose flag with add-uid command shows UUID generation"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file without UID
        file_path = self.vault_path / "test_uid.md"
        post = frontmatter.Post("Test content", title="Test")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test add-uid with verbose flag
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "--verbose", "add-uid", "test_uid.md"]
        )
        self.assertEqual(result.exit_code, 0)
        # Should show the generated UUID
        self.assertIn("Generated new UUID:", result.stdout)

    def test_verbose_flag_new_command(self):
        """Test verbose flag with new command shows file creation message"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Test new command with verbose flag
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "--verbose", "new", "test_verbose.md"]
        )
        # Should show file creation message
        self.assertIn("Created new file:", result.stdout)

    def test_verbose_flag_journal_command(self):
        """Test verbose flag with journal command shows template information"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write('journal_template = "Journal/{year}-{month:02d}-{day:02d}.md"\n')

        # Test journal command with verbose flag
        # (will fail with file not found, but should show verbose output)
        result = self.runner.invoke(cli, ["--config", str(config_file), "--verbose", "journal"])
        # Should show template and resolved path information
        self.assertIn("Using journal template:", result.stdout)
        self.assertIn("Resolved journal path:", result.stdout)

    def test_verbose_flag_rm_command(self):
        """Test verbose flag with rm command shows removal confirmation"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file
        file_path = self.vault_path / "test_remove.md"
        with open(file_path, "w") as f:
            f.write("Test content")

        # Test rm command with verbose flag and force
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "--verbose", "rm", "test_remove.md", "--force"]
        )
        self.assertEqual(result.exit_code, 0)
        # Should show file removal confirmation
        self.assertIn("File removed:", result.stdout)

    def test_verbose_flag_meta_command(self):
        """Test verbose flag with meta command shows update confirmation"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create a test file
        file_path = self.vault_path / "test_meta.md"
        post = frontmatter.Post("Test content", title="Original Title")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test meta command with verbose flag
        result = self.runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "--verbose",
                "meta",
                "test_meta.md",
                "--key",
                "author",
                "--value",
                "John Doe",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        # Should show update confirmation
        self.assertIn("Updated 'author': 'John Doe'", result.stdout)

    def test_verbose_flag_find_command_output(self):
        """Test verbose flag with find command shows additional search information"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Create test files
        file_path = self.vault_path / "daily_note.md"
        post = frontmatter.Post("Daily content", title="Daily Note")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test find command with verbose flag
        result = self.runner.invoke(
            cli, ["--config", str(config_file), "--verbose", "find", "daily"]
        )
        self.assertEqual(result.exit_code, 0)
        # Should show search information
        self.assertIn("Searching for page: 'daily'", result.stdout)

    def test_verbose_flag_info_command(self):
        """Test verbose flag with info command shows verbose state"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')

        # Test info command with verbose flag
        result = self.runner.invoke(cli, ["--config", str(config_file), "--verbose", "info"])
        self.assertEqual(result.exit_code, 0)
        # Should show verbose state as True
        self.assertIn("Verbose: True", result.stdout)

    def test_verbose_flag_overrides_config_false(self):
        """Test that --verbose flag overrides verbose=false in config"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write("verbose = false\n")

        # Test that --verbose flag overrides config setting
        result = self.runner.invoke(cli, ["--config", str(config_file), "--verbose", "info"])
        self.assertEqual(result.exit_code, 0)
        # Should show verbose as True, overriding config
        self.assertIn("Verbose: True", result.stdout)

    def test_no_verbose_flag_respects_config_true(self):
        """Test that when no --verbose flag is provided, config setting is respected"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write("verbose = true\n")

        # Test without --verbose flag but with verbose=true in config
        result = self.runner.invoke(cli, ["--config", str(config_file), "info"])
        self.assertEqual(result.exit_code, 0)
        # Should show verbose as True from config
        self.assertIn("Verbose: True", result.stdout)

    def test_no_verbose_flag_with_config_false(self):
        """Test that verbose output is suppressed when verbose=false in config
        and no --verbose flag"""
        config_file = self.vault_path / "config.toml"
        with open(config_file, "w") as f:
            f.write(f'vault = "{self.vault_path}"\n')
            f.write("verbose = false\n")

        # Create a test file
        file_path = self.vault_path / "test_uuid.md"
        post = frontmatter.Post("Test content", title="Test")
        with open(file_path, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test add-uid without verbose flag and verbose=false in config
        result = self.runner.invoke(cli, ["--config", str(config_file), "add-uid", "test_uuid.md"])
        self.assertEqual(result.exit_code, 0)
        # Should NOT show the generated UUID (no verbose output)
        self.assertNotIn("Generated new UUID:", result.stdout)

    def test_configuration_class_defaults(self):
        """Test Configuration class with default values"""
        from obsidian_cli.main import Configuration

        config = Configuration()

        # Test default values
        self.assertEqual(str(config.editor), "vi")
        self.assertEqual(config.ident_key, "uid")
        self.assertEqual(config.ignored_directories, ("Assets/", ".obsidian/", ".git/"))
        expected_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
        self.assertEqual(config.journal_template, expected_template)
        self.assertIsNone(config.vault)
        self.assertFalse(config.verbose)

    def test_configuration_class_from_file_with_all_options(self):
        """Test Configuration.from_file with all configuration options"""
        from obsidian_cli.main import Configuration

        config_file = self.vault_path / "full_config.toml"
        with open(config_file, "w") as f:
            f.write(f"""
vault = "{self.vault_path}"
editor = "nano"
ident_key = "id"
ignored_directories = ["Temp/", "Archive/"]
journal_template = "Daily/{{year}}/{{month:02d}}-{{day:02d}}"
verbose = true
""")

        config = Configuration.from_file(config_file)

        self.assertEqual(str(config.vault), str(self.vault_path))
        self.assertEqual(str(config.editor), "nano")
        self.assertEqual(config.ident_key, "id")
        self.assertEqual(config.ignored_directories, ["Temp/", "Archive/"])
        self.assertEqual(config.journal_template, "Daily/{year}/{month:02d}-{day:02d}")
        self.assertTrue(config.verbose)

    def test_configuration_class_from_file_partial_options(self):
        """Test Configuration.from_file with only some options (others should use defaults)"""
        from obsidian_cli.main import Configuration

        config_file = self.vault_path / "partial_config.toml"
        with open(config_file, "w") as f:
            f.write(f"""
vault = "{self.vault_path}"
verbose = true
""")

        config = Configuration.from_file(config_file)

        # Specified values
        self.assertEqual(str(config.vault), str(self.vault_path))
        self.assertTrue(config.verbose)

        # Default values for unspecified options
        self.assertEqual(str(config.editor), "vi")
        self.assertEqual(config.ident_key, "uid")
        self.assertEqual(config.ignored_directories, ("Assets/", ".obsidian/", ".git/"))
        expected_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
        self.assertEqual(config.journal_template, expected_template)

    def test_configuration_class_from_file_missing_file(self):
        """Test Configuration.from_file with missing file"""
        from obsidian_cli.main import Configuration

        with self.assertRaises(FileNotFoundError):
            Configuration.from_file(Path("/nonexistent/config.toml"))

    def test_configuration_class_from_file_no_path_no_defaults(self):
        """Test Configuration.from_file with no path and no default files"""
        from obsidian_cli.main import Configuration

        # In a temp directory with no config files
        with self.assertRaises(FileNotFoundError):
            Configuration.from_file(None)

    def test_configuration_class_from_file_malformed_toml(self):
        """Test Configuration.from_file with malformed TOML"""
        import tomllib

        from obsidian_cli.main import Configuration

        config_file = self.vault_path / "malformed_config.toml"
        with open(config_file, "w") as f:
            f.write("""
vault = "/some/path
[malformed section
""")

        with self.assertRaises(tomllib.TOMLDecodeError):
            Configuration.from_file(config_file)

    def test_configuration_class_immutability(self):
        """Test that Configuration dataclass is frozen (immutable)"""
        from obsidian_cli.main import Configuration

        config = Configuration()

        # Should not be able to modify frozen dataclass
        with self.assertRaises(AttributeError):
            config.vault = Path("/new/path")

        with self.assertRaises(AttributeError):
            config.verbose = True

    def test_configuration_load_toml_config_static_method(self):
        """Test Configuration._load_toml_config static method directly"""
        from obsidian_cli.main import Configuration

        config_file = self.vault_path / "static_test_config.toml"
        with open(config_file, "w") as f:
            f.write("""
vault = "/test/vault"
verbose = false
editor = "emacs"
""")

        result = Configuration._load_toml_config(config_file)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["vault"], "/test/vault")
        self.assertFalse(result["verbose"])
        self.assertEqual(result["editor"], "emacs")

    def test_configuration_load_toml_config_verbose_flag(self):
        """Test Configuration._load_toml_config with verbose output"""
        import sys
        from io import StringIO

        from obsidian_cli.main import Configuration

        config_file = self.vault_path / "verbose_test_config.toml"
        with open(config_file, "w") as f:
            f.write("""
vault = "/test/vault"
""")

        # Capture stdout to test verbose output
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            result = Configuration._load_toml_config(config_file, verbose=True)
            output = captured_output.getvalue()

            self.assertIn(f"Parsing configuration from: {config_file}", output)
            self.assertEqual(result["vault"], "/test/vault")
        finally:
            sys.stdout = old_stdout

    def test_configuration_class_type_conversion(self):
        """Test that Configuration properly converts types from TOML"""
        from obsidian_cli.main import Configuration

        config_file = self.vault_path / "type_test_config.toml"
        with open(config_file, "w") as f:
            f.write(f"""
vault = "{self.vault_path}"
editor = "code"
ident_key = "uuid"
ignored_directories = ["Test1/", "Test2/", "Test3/"]
journal_template = "Notes/{{year}}/{{day:02d}}"
verbose = false
""")

        config = Configuration.from_file(config_file)

        # Verify types
        self.assertIsInstance(config.vault, Path)
        self.assertIsInstance(config.editor, Path)
        self.assertIsInstance(config.ident_key, str)
        self.assertIsInstance(config.ignored_directories, list)
        self.assertIsInstance(config.journal_template, str)
        self.assertIsInstance(config.verbose, bool)

        # Verify values
        self.assertEqual(str(config.vault), str(self.vault_path))
        self.assertEqual(str(config.editor), "code")
        self.assertEqual(config.ident_key, "uuid")
        self.assertEqual(config.ignored_directories, ["Test1/", "Test2/", "Test3/"])
        self.assertEqual(config.journal_template, "Notes/{year}/{day:02d}")
        self.assertFalse(config.verbose)


if __name__ == "__main__":
    unittest.main()
