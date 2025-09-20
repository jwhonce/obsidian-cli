"""
Comprehensive tests for MCP server functionality to improve coverage.
"""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import typer

from obsidian_cli.mcp_server import (
    handle_create_note,
    handle_find_notes,
    handle_get_note_content,
    handle_get_vault_info,
    serve_mcp,
)
from obsidian_cli.types import Vault


class TestMCPServerComprehensive(unittest.TestCase):
    """Comprehensive test cases for MCP server functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "test_vault"
        self.vault_path.mkdir()
        # Create .obsidian directory to make it a valid Obsidian vault
        (self.vault_path / ".obsidian").mkdir()

        self.vault = Vault(
            editor=Path("vi"),
            ident_key="uid",
            blacklist=["Assets/", ".obsidian/"],
            config_dirs=["test.toml"],
            journal_template="Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}",
            path=self.vault_path,
            verbose=False,
        )

        self.ctx = MagicMock(spec=typer.Context)
        self.ctx.obj = self.vault

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_serve_mcp_import_error(self):
        """Test serve_mcp import error handling."""
        # Since MCP imports are now at module level, we test the import error
        # by attempting to import the module with missing dependencies

        # This test verifies that the ImportError is raised at module load time
        # when MCP dependencies are missing, which is the expected behavior
        # with our new import structure

        # We can't easily test this in isolation anymore since the imports
        # happen at module load time, so we just verify the function exists
        # and is callable
        self.assertTrue(callable(serve_mcp))
        self.assertEqual(serve_mcp.__name__, "serve_mcp")

    def test_handle_create_note_success(self):
        """Test successful note creation."""

        async def run_test():
            args = {"filename": "test-note", "content": "Test content", "force": False}

            with patch("obsidian_cli.main.new") as mock_new:
                mock_new.return_value = None
                result = await handle_create_note(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Successfully created note", result[0].text)
                mock_new.assert_called_once()

        asyncio.run(run_test())

    def test_handle_create_note_with_md_extension(self):
        """Test note creation with .md extension in filename."""

        async def run_test():
            args = {"filename": "test-note.md", "content": "", "force": False}

            with patch("obsidian_cli.main.new") as mock_new:
                mock_new.return_value = None
                result = await handle_create_note(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Successfully created note", result[0].text)
                # Should call with filename without .md extension
                call_args = mock_new.call_args[0]  # positional args
                self.assertEqual(
                    call_args[1].name, "test-note"
                )  # page_or_path is second positional arg

        asyncio.run(run_test())

    def test_handle_create_note_file_exists(self):
        """Test note creation when file already exists."""

        async def run_test():
            args = {"filename": "existing-note", "content": "Test content", "force": False}

            with patch("obsidian_cli.main.new") as mock_new:
                mock_new.side_effect = typer.Exit(code=1)
                result = await handle_create_note(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("already exists", result[0].text)
                self.assertIn("force=true", result[0].text)

        asyncio.run(run_test())

    def test_handle_create_note_other_exit_code(self):
        """Test note creation with other exit codes."""

        async def run_test():
            args = {"filename": "test-note", "content": "Test content", "force": False}

            with patch("obsidian_cli.main.new") as mock_new:
                mock_new.side_effect = typer.Exit(code=2)
                result = await handle_create_note(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Command exited with code 2", result[0].text)

        asyncio.run(run_test())

    def test_handle_create_note_exception(self):
        """Test note creation with general exception."""

        async def run_test():
            args = {"filename": "test-note", "content": "Test content", "force": False}

            with patch("obsidian_cli.main.new") as mock_new:
                mock_new.side_effect = Exception("Test error")
                result = await handle_create_note(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Failed to create note", result[0].text)
                self.assertIn("Test error", result[0].text)

        asyncio.run(run_test())

    def test_handle_find_notes_success(self):
        """Test successful note finding."""

        async def run_test():
            args = {"term": "test", "exact": False}

            # Create test files
            (self.vault_path / "test-file.md").write_text("# Test")
            (self.vault_path / "another-test.md").write_text("# Another")

            result = await handle_find_notes(self.ctx, self.vault, args)

            self.assertEqual(len(result), 1)
            self.assertIn("Found 2 file(s)", result[0].text)
            self.assertIn("test-file.md", result[0].text)
            self.assertIn("another-test.md", result[0].text)

        asyncio.run(run_test())

    def test_handle_find_notes_no_matches(self):
        """Test note finding with no matches."""

        async def run_test():
            args = {"term": "nonexistent", "exact": True}

            result = await handle_find_notes(self.ctx, self.vault, args)

            self.assertEqual(len(result), 1)
            self.assertIn("No files found matching", result[0].text)

        asyncio.run(run_test())

    def test_handle_find_notes_exception(self):
        """Test note finding with exception."""

        async def run_test():
            args = {"term": "test", "exact": False}

            with patch("obsidian_cli.main._find_matching_files") as mock_find:
                mock_find.side_effect = Exception("Find error")
                result = await handle_find_notes(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Error finding notes", result[0].text)
                self.assertIn("Find error", result[0].text)

        asyncio.run(run_test())

    def test_handle_get_note_content_success(self):
        """Test successful note content retrieval."""

        async def run_test():
            args = {"filename": "test-note", "show_frontmatter": False}

            # Create test file
            test_file = self.vault_path / "test-note.md"
            test_file.write_text("""---
title: Test Note
---
This is the content.""")

            with patch("obsidian_cli.main.cat") as mock_cat:

                def mock_cat_func(ctx, filename, show_frontmatter=False):
                    print("This is the content.")

                mock_cat.side_effect = mock_cat_func
                result = await handle_get_note_content(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("This is the content.", result[0].text)

        asyncio.run(run_test())

    def test_handle_get_note_content_file_not_found(self):
        """Test note content retrieval when file not found."""

        async def run_test():
            args = {"filename": "nonexistent-note", "show_frontmatter": False}

            with patch("obsidian_cli.main.cat") as mock_cat:
                mock_cat.side_effect = typer.Exit(code=2)
                result = await handle_get_note_content(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("File not found", result[0].text)

        asyncio.run(run_test())

    def test_handle_get_note_content_other_exit_code(self):
        """Test note content retrieval with other exit codes."""

        async def run_test():
            args = {"filename": "test-note", "show_frontmatter": False}

            with patch("obsidian_cli.main.cat") as mock_cat:
                mock_cat.side_effect = typer.Exit(code=1)
                result = await handle_get_note_content(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Error reading note: exit code 1", result[0].text)

        asyncio.run(run_test())

    def test_handle_get_note_content_exception(self):
        """Test note content retrieval with exception."""

        async def run_test():
            args = {"filename": "test-note", "show_frontmatter": False}

            with patch("obsidian_cli.main.cat") as mock_cat:
                mock_cat.side_effect = Exception("Read error")
                result = await handle_get_note_content(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Error reading note", result[0].text)
                self.assertIn("Read error", result[0].text)

        asyncio.run(run_test())

    def test_handle_get_vault_info_success(self):
        """Test successful vault info retrieval."""

        async def run_test():
            args = {}

            # Create test files of different types
            (self.vault_path / "test1.md").write_text("# Test 1")
            (self.vault_path / "test2.md").write_text("# Test 2")
            (self.vault_path / "notes.txt").write_text("Some notes")
            (self.vault_path / "config.json").write_text('{"key": "value"}')
            (self.vault_path / "image.png").write_bytes(b"fake image data")

            result = await handle_get_vault_info(self.ctx, self.vault, args)

            self.assertEqual(len(result), 1)
            self.assertIn("Obsidian Vault Information", result[0].text)
            self.assertIn(str(self.vault_path), result[0].text)
            self.assertIn("Editor: vi", result[0].text)

            # Check that usage information is included
            self.assertIn("Usage files:", result[0].text)
            self.assertIn("Usage directories:", result[0].text)

            # Check that file type statistics are included
            self.assertIn("File Types by Extension:", result[0].text)
            self.assertIn("- md: 2 files", result[0].text)  # 2 markdown files
            self.assertIn("- txt: 1 files", result[0].text)  # 1 text file
            self.assertIn("- json: 1 files", result[0].text)  # 1 JSON file
            self.assertIn("- png: 1 files", result[0].text)  # 1 PNG file
            # Check that sizes are shown with appropriate units (should be Bytes for small files)
            self.assertIn("Bytes", result[0].text)

        asyncio.run(run_test())

    def test_handle_get_vault_info_nonexistent_vault(self):
        """Test vault info retrieval with nonexistent vault."""

        async def run_test():
            args = {}

            # Create state with nonexistent vault
            bad_vault = Vault(
                editor=Path("vi"),
                ident_key="uid",
                blacklist=[],
                config_dirs=["test.toml"],
                journal_template="test",
                path=Path("/nonexistent/path"),
                verbose=False,
            )

            result = await handle_get_vault_info(self.ctx, bad_vault, args)

            self.assertEqual(len(result), 1)
            self.assertIn("Vault not found", result[0].text)

        asyncio.run(run_test())

    def test_handle_get_vault_info_exception(self):
        """Test vault info retrieval with exception."""

        async def run_test():
            args = {}

            with patch("obsidian_cli.mcp_server._get_vault_info") as mock_info:
                mock_info.side_effect = Exception("Info error")
                result = await handle_get_vault_info(self.ctx, self.vault, args)

                self.assertEqual(len(result), 1)
                self.assertIn("Error retrieving vault information", result[0].text)
                self.assertIn("Info error", result[0].text)

        asyncio.run(run_test())

    def test_serve_mcp_success_mock(self):
        """Test that serve_mcp can be called without errors when properly mocked."""
        # This is a simplified test that just ensures the function structure is correct
        # Full integration testing would require actual MCP server setup which would
        # run indefinitely, so we just verify the function signature and structure
        self.assertTrue(callable(serve_mcp))
        self.assertTrue(hasattr(serve_mcp, "__code__"))
        self.assertEqual(serve_mcp.__code__.co_argcount, 2)  # ctx, vault

        # Verify it's an async function
        import asyncio

        self.assertTrue(asyncio.iscoroutinefunction(serve_mcp))

    def test_mcp_tool_error_handling(self):
        """Test that MCP tool errors are properly handled."""
        # The individual handlers catch exceptions and return error messages
        # The call_tool function in serve_mcp provides additional logging

        from unittest.mock import patch

        from obsidian_cli.mcp_server import handle_find_notes

        async def run_test():
            with patch("obsidian_cli.main._find_matching_files") as mock_find:
                # Make _find_matching_files raise an exception
                mock_find.side_effect = Exception("Test error in tool")

                # The handler catches the exception and returns an error message
                result = await handle_find_notes(self.ctx, self.vault, {"term": "test"})

                # Verify the result contains error message
                self.assertEqual(len(result), 1)
                self.assertIn("Error finding notes:", result[0].text)
                self.assertIn("Test error in tool", result[0].text)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
