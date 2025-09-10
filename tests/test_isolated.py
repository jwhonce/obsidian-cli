"""
Test Configuration loading in isolated environment.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from obsidian_cli.main import Configuration


class TestIsolated(unittest.TestCase):
    """Test Configuration in isolated environment."""

    def setUp(self):
        """Set up isolated test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.xdg_config_dir = Path(self.temp_dir) / "xdg_config"
        self.home_dir = Path(self.temp_dir) / "home"

        # Create directories
        self.xdg_config_dir.mkdir(parents=True)
        self.home_dir.mkdir(parents=True)

        # Store original environment
        self.old_cwd = os.getcwd()
        self.old_xdg_config = os.environ.get("XDG_CONFIG_HOME")
        self.old_home = os.environ.get("HOME")

        # Set isolated environment
        os.chdir(self.temp_dir)
        os.environ["XDG_CONFIG_HOME"] = str(self.xdg_config_dir)
        os.environ["HOME"] = str(self.home_dir)

    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment
        os.chdir(self.old_cwd)
        if self.old_xdg_config is not None:
            os.environ["XDG_CONFIG_HOME"] = self.old_xdg_config
        elif "XDG_CONFIG_HOME" in os.environ:
            del os.environ["XDG_CONFIG_HOME"]
        if self.old_home is not None:
            os.environ["HOME"] = self.old_home
        elif "HOME" in os.environ:
            del os.environ["HOME"]

        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_toml_config_xdg_path(self):
        """Test TOML configuration loading from XDG config path."""
        # Test XDG config path
        xdg_config_file = self.xdg_config_dir / "obsidian-cli" / "config.toml"
        xdg_config_file.parent.mkdir(parents=True)
        xdg_config_file.write_text("""
vault = "/xdg/vault"
editor = "nano"
""")

        source, config = Configuration.from_path()
        self.assertEqual(source, xdg_config_file)
        self.assertEqual(str(config.vault), "/xdg/vault")
        self.assertEqual(str(config.editor), "nano")

    def test_toml_config_home_path(self):
        """Test TOML configuration loading from ~/.config path."""
        # Clear XDG_CONFIG_HOME to test ~/.config fallback
        del os.environ["XDG_CONFIG_HOME"]

        home_config_file = self.home_dir / ".config" / "obsidian-cli" / "config.toml"
        home_config_file.parent.mkdir(parents=True)
        home_config_file.write_text("""
vault = "/home/vault"
editor = "vim"
""")

        source, config = Configuration.from_path()
        self.assertEqual(source, home_config_file)
        self.assertEqual(str(config.vault), "/home/vault")
        self.assertEqual(str(config.editor), "vim")

        # Restore XDG_CONFIG_HOME for cleanup
        os.environ["XDG_CONFIG_HOME"] = str(self.xdg_config_dir)

    def test_no_config_file_defaults(self):
        """Test default configuration when no config file exists."""
        source, config = Configuration.from_path()
        self.assertIsNone(source)
        self.assertEqual(config.editor, Path("vi"))
        self.assertEqual(config.ident_key, "uid")
        self.assertEqual(config.blacklist, ["Assets/", ".obsidian/", ".git/"])
        self.assertIsNone(config.vault)
        self.assertFalse(config.verbose)


if __name__ == "__main__":
    unittest.main()
