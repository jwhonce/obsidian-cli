"""Unit tests for obsidian_cli module utility functions."""

import tempfile
import unittest
import uuid
from pathlib import Path

import typer

from obsidian_cli.main import _resolve_path


class TestUtils(unittest.TestCase):
    """Test suite for utility functions."""

    def test_resolve_path_existing_file(self):
        """Test _resolve_path with an existing file."""
        # Create a temporary file
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir)
            test_file = vault_path / "test_note.md"
            test_file.write_text("Test content")

            # Test with absolute path
            resolved_path = _resolve_path(test_file, vault_path)
            # Just check if paths refer to the same file (Mac may add /private/ prefix)
            self.assertTrue(resolved_path.exists())
            self.assertEqual(resolved_path.name, test_file.name)

    def test_resolve_path_nonexistent_file(self):
        """Test _resolve_path with a non-existent file."""
        # Create a temporary directory as vault
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir)
            file_path = Path(f"{uuid.uuid4()}.md")  # Random filename that doesn't exist

            with self.assertRaises(typer.BadParameter):
                _resolve_path(file_path, vault_path)
