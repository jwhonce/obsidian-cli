"""Tests for MCP server functionality."""

import tempfile
import unittest
from pathlib import Path

from obsidian_cli.main import State


class TestMCPServerComponents(unittest.TestCase):
    """Test MCP server components with correct State parameters."""

    def test_state_creation_with_blacklist(self):
        """Test that State objects can be created with blacklist parameter."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            state = State(
                editor=Path("vi"),
                ident_key="uid",
                blacklist=["Assets/", ".obsidian/", ".git/"],
                journal_template="Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}",
                vault=tmp_path,
                verbose=False,
            )
            self.assertEqual(state.blacklist, ["Assets/", ".obsidian/", ".git/"])
            self.assertEqual(state.ident_key, "uid")
            self.assertEqual(state.vault, tmp_path)

    def test_state_blacklist_attribute_access(self):
        """Test that blacklist attribute can be accessed properly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            state = State(
                editor=Path("vi"),
                ident_key="uid",
                blacklist=["temp/", "draft/"],
                journal_template="test/{year}-{month:02d}-{day:02d}",
                vault=tmp_path,
                verbose=False,
            )
            # This was the failing line - should now work with blacklist
            self.assertIsInstance(state.blacklist, list)
            self.assertIn("temp/", state.blacklist)
            self.assertIn("draft/", state.blacklist)


if __name__ == "__main__":
    unittest.main()
