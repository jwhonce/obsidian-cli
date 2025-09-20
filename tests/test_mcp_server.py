"""Tests for MCP server functionality."""

import tempfile
import unittest
from pathlib import Path

from obsidian_cli.types import Vault


class TestMCPServerComponents(unittest.TestCase):
    """Test MCP server components with correct Vault parameters."""

    def test_vault_creation_with_blacklist(self):
        """Test that Vault objects can be created with blacklist parameter."""
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
            self.assertEqual(vault.ident_key, "uid")
            self.assertEqual(vault.path, tmp_path)

    def test_vault_blacklist_attribute_access(self):
        """Test that blacklist attribute can be accessed properly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            vault = Vault(
                editor=Path("vi"),
                ident_key="uid",
                blacklist=["temp/", "draft/"],
                config_dirs=["test.toml"],
                journal_template="test/{year}-{month:02d}-{day:02d}",
                path=tmp_path,
                verbose=False,
            )
            # This was the failing line - should now work with blacklist
            self.assertIsInstance(vault.blacklist, list)
            self.assertIn("temp/", vault.blacklist)
            self.assertIn("draft/", vault.blacklist)


if __name__ == "__main__":
    unittest.main()
