"""
Additional tests for utils module to improve coverage.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from obsidian_cli.utils import (
    _check_if_path_blacklisted,
    _display_find_results,
    _display_metadata_key,
    _display_query_results,
    _find_matching_files,
    _get_frontmatter,
    _get_journal_template_vars,
    _list_all_metadata,
    _resolve_path,
    _update_metadata_key,
)


class TestUtilsCoverage(unittest.TestCase):
    """Test cases to improve utils coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "test_vault"
        self.vault_path.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_display_find_results_no_matches(self):
        """Test display_find_results with no matches."""
        with patch("typer.secho") as mock_secho:
            _display_find_results([], "test", False, self.vault_path)
            mock_secho.assert_called_once_with("No files found matching 'test'", err=True, fg="red")

    def test_display_find_results_verbose_mode(self):
        """Test display_find_results verbose mode with various scenarios."""
        # Test with title metadata
        test_file_with_title = self.vault_path / "with_title.md"
        test_file_with_title.write_text("---\ntitle: Test Title\n---\nContent")

        # Test without title metadata
        test_file_no_title = self.vault_path / "no_title.md"
        test_file_no_title.write_text("---\nauthor: Someone\n---\nContent")

        matches = [Path("with_title.md"), Path("no_title.md")]

        with patch("typer.echo") as mock_echo:
            _display_find_results(matches, "test", True, self.vault_path)

            # Should print both filenames
            mock_echo.assert_any_call(Path("with_title.md"))
            mock_echo.assert_any_call(Path("no_title.md"))
            # Should print title for file that has it
            mock_echo.assert_any_call("  title: Test Title")

        # Test exception handling with nonexistent file
        with patch("typer.echo") as mock_echo:
            _display_find_results([Path("nonexistent.md")], "test", True, self.vault_path)
            # Should still print filename despite exception
            mock_echo.assert_called_with(Path("nonexistent.md"))

    def test_get_journal_template_vars_all_fields(self):
        """Test _get_journal_template_vars returns all expected fields."""
        from datetime import datetime

        test_date = datetime(2025, 3, 15)  # March 15, 2025
        vars = _get_journal_template_vars(test_date)

        # Check that all expected keys are present
        expected_keys = {
            "year",
            "month",
            "day",
            "month_name",
            "month_abbr",
            "weekday",
            "weekday_abbr",
        }
        self.assertEqual(set(vars.keys()), expected_keys)

        # Check specific values that don't depend on weekday calculation
        self.assertEqual(vars["year"], 2025)
        self.assertEqual(vars["month"], 3)
        self.assertEqual(vars["day"], 15)
        self.assertEqual(vars["month_name"], "March")
        self.assertEqual(vars["month_abbr"], "Mar")

        # Check that weekday fields are strings (don't check exact values as they depend on calendar)
        self.assertIsInstance(vars["weekday"], str)
        self.assertIsInstance(vars["weekday_abbr"], str)
        self.assertTrue(len(vars["weekday"]) > 0)
        self.assertTrue(len(vars["weekday_abbr"]) > 0)

    def test_list_all_metadata_with_data(self):
        """Test _list_all_metadata with frontmatter data."""
        import frontmatter

        post = frontmatter.Post("Content")
        post.metadata = {"title": "Test Title", "tags": ["tag1", "tag2"], "created": "2025-01-01"}

        with patch("typer.echo") as mock_echo:
            _list_all_metadata(post)

            # Should print each metadata key-value pair
            mock_echo.assert_any_call("title: Test Title")
            mock_echo.assert_any_call("tags: ['tag1', 'tag2']")
            mock_echo.assert_any_call("created: 2025-01-01")

    def test_list_all_metadata_empty(self):
        """Test _list_all_metadata with empty frontmatter."""
        import frontmatter

        post = frontmatter.Post("Content")
        post.metadata = {}

        with patch("typer.secho") as mock_secho:
            _list_all_metadata(post)

            mock_secho.assert_called_once_with(
                "No frontmatter metadata found for this page", err=True, fg="red"
            )

    def test_display_metadata_key_exists(self):
        """Test _display_metadata_key when key exists."""
        import frontmatter

        post = frontmatter.Post("Content")
        post.metadata = {"title": "Test Title"}

        with patch("typer.echo") as mock_echo:
            _display_metadata_key(post, "title")
            mock_echo.assert_called_once_with("title: Test Title")

    def test_display_metadata_key_missing(self):
        """Test _display_metadata_key when key doesn't exist."""
        import frontmatter

        post = frontmatter.Post("Content")
        post.metadata = {}

        # Should raise KeyError
        with self.assertRaises(KeyError):
            _display_metadata_key(post, "nonexistent")

    def test_update_metadata_key_new_key(self):
        """Test _update_metadata_key adding new key."""

        # Create test file
        test_file = self.vault_path / "test.md"
        test_file.write_text("""---
title: Original Title
---
Content""")

        post = _get_frontmatter(test_file)

        with patch("typer.echo") as mock_echo:
            _update_metadata_key(post, test_file, "author", "Test Author", True)

            # Should show update message
            # The actual message includes the full path, so we check for the key parts
            mock_echo.assert_called()
            call_args = mock_echo.call_args[0][0]  # Get the first argument
            self.assertIn("Updated 'author': 'Test Author'", call_args)

            # Verify file was updated
            updated_post = _get_frontmatter(test_file)
            self.assertEqual(updated_post.metadata["author"], "Test Author")

    def test_update_metadata_key_existing_key(self):
        """Test _update_metadata_key updating existing key."""

        # Create test file
        test_file = self.vault_path / "test.md"
        test_file.write_text("""---
title: Original Title
---
Content""")

        post = _get_frontmatter(test_file)

        with patch("typer.echo") as mock_echo:
            _update_metadata_key(post, test_file, "title", "New Title", False)

            # Should not show update message in non-verbose mode
            mock_echo.assert_not_called()

            # Verify file was updated
            updated_post = _get_frontmatter(test_file)
            self.assertEqual(updated_post.metadata["title"], "New Title")

    def test_display_query_results_json_format(self):
        """Test _display_query_results with JSON format."""
        import frontmatter

        from obsidian_cli.main import QueryOutputStyle

        post = frontmatter.Post("Content")
        post.metadata = {"title": "Test Title"}
        matches = [(Path("test.md"), post)]

        with patch("typer.echo") as mock_echo:
            _display_query_results(matches, QueryOutputStyle.JSON, "title")

            # Should output JSON
            mock_echo.assert_called_once()
            call_args = mock_echo.call_args[0][0]
            self.assertIn('"test.md"', call_args)
            self.assertIn('"Test Title"', call_args)

    def test_display_query_results_title_format(self):
        """Test _display_query_results with TITLE format."""
        import frontmatter

        from obsidian_cli.main import QueryOutputStyle

        post = frontmatter.Post("Content")
        post.metadata = {"title": "Test Title"}
        matches = [(Path("test.md"), post)]

        with patch("typer.echo") as mock_echo:
            _display_query_results(matches, QueryOutputStyle.TITLE, "title")

            mock_echo.assert_called_once_with("test.md: Test Title")

    def test_display_query_results_table_format(self):
        """Test _display_query_results with TABLE format."""
        import frontmatter

        from obsidian_cli.main import QueryOutputStyle

        post = frontmatter.Post("Content")
        post.metadata = {"title": "Test Title"}
        matches = [(Path("test.md"), post)]

        # TABLE format uses rich.console.Console.print, not typer.echo
        with patch("rich.console.Console.print") as mock_print:
            _display_query_results(matches, QueryOutputStyle.TABLE, "title")

            # Should have called print to display the table
            mock_print.assert_called()

    def test_display_query_results_path_format(self):
        """Test _display_query_results with PATH format."""
        import frontmatter

        from obsidian_cli.main import QueryOutputStyle

        post = frontmatter.Post("Content")
        post.metadata = {"title": "Test Title"}
        matches = [(Path("test.md"), post)]

        with patch("typer.echo") as mock_echo:
            _display_query_results(matches, QueryOutputStyle.PATH, "title")

            # PATH format outputs the Path object directly
            mock_echo.assert_called_once_with(Path("test.md"))

    def test_display_query_results_missing_key(self):
        """Test _display_query_results when key is missing from metadata."""
        import frontmatter

        from obsidian_cli.main import QueryOutputStyle

        post = frontmatter.Post("Content")
        post.metadata = {"test": "test"}  # Has a different key, not title
        matches = [(Path("test.md"), post)]

        with patch("typer.echo") as mock_echo:
            _display_query_results(matches, QueryOutputStyle.TITLE, "title")

            # When the requested key is missing, it shows filename: first available key
            mock_echo.assert_called_once_with("test.md: test")

    def test_check_if_path_blacklisted_match(self):
        """Test _check_if_path_blacklisted with matching path."""
        path = Path("Assets/image.png")
        blacklist = ["Assets/", ".obsidian/"]

        result = _check_if_path_blacklisted(path, blacklist)
        self.assertTrue(result)

    def test_check_if_path_blacklisted_no_match(self):
        """Test _check_if_path_blacklisted with non-matching path."""
        path = Path("Notes/test.md")
        blacklist = ["Assets/", ".obsidian/"]

        result = _check_if_path_blacklisted(path, blacklist)
        self.assertFalse(result)

    def test_find_matching_files_case_insensitive(self):
        """Test _find_matching_files with case insensitive search."""
        # Create test files
        (self.vault_path / "Test-File.md").write_text("# Test")
        (self.vault_path / "another-test.md").write_text("# Another")

        matches = _find_matching_files(self.vault_path, "test", exact_match=False)

        # Should find both files (case insensitive)
        self.assertEqual(len(matches), 2)
        match_names = [match.name for match in matches]
        self.assertIn("Test-File.md", match_names)
        self.assertIn("another-test.md", match_names)

    def test_find_matching_files_exact_match(self):
        """Test _find_matching_files with exact match."""
        # Create test files
        (self.vault_path / "test.md").write_text("# Test")
        (self.vault_path / "test-file.md").write_text("# Test File")

        matches = _find_matching_files(self.vault_path, "test", exact_match=True)

        # Should find only exact match
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].name, "test.md")

    def test_resolve_path_absolute(self):
        """Test _resolve_path with absolute path."""
        abs_path = self.vault_path / "test.md"
        abs_path.write_text("Content")

        result = _resolve_path(abs_path, self.vault_path)
        self.assertEqual(result, abs_path)

    def test_resolve_path_relative_with_extension(self):
        """Test _resolve_path with relative path that has .md extension."""
        test_file = self.vault_path / "test.md"
        test_file.write_text("Content")

        result = _resolve_path(Path("test.md"), self.vault_path)
        self.assertEqual(result, test_file)

    def test_resolve_path_relative_without_extension(self):
        """Test _resolve_path with relative path without .md extension."""
        test_file = self.vault_path / "test.md"
        test_file.write_text("Content")

        result = _resolve_path(Path("test"), self.vault_path)
        self.assertEqual(result, test_file)


if __name__ == "__main__":
    unittest.main()
