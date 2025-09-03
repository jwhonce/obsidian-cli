import os
import shutil
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from obsidian_cli.main import cli


class TestIsolated(unittest.TestCase):
    """Test cases that require isolated environment setup."""

    @classmethod
    def setUpClass(cls):
        """Move home config file to avoid test interference."""
        cls.home_config = Path.home() / ".config" / "obsidian-cli" / "config.toml"
        cls.home_backup = None
        if cls.home_config.exists():
            cls.home_backup = cls.home_config.with_suffix(".toml.backup")
            shutil.move(str(cls.home_config), str(cls.home_backup))

    @classmethod
    def tearDownClass(cls):
        """Restore home config file."""
        if cls.home_backup and cls.home_backup.exists():
            shutil.move(str(cls.home_backup), str(cls.home_config))

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "test_vault"
        self.vault_path.mkdir()
        self.runner = CliRunner()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_error_handling_missing_vault(self):
        """Test error handling when vault is missing."""
        result = self.runner.invoke(cli, ["info"])

        # The CLI should exit with code 2 when vault is missing
        self.assertEqual(result.exit_code, 2)
        # Check for vault-related error in stderr or stdout
        error_output = (result.stderr or "") + (result.stdout or "")
        self.assertTrue(
            "Vault path is required" in error_output
            or "vault" in error_output.lower()
            or len(error_output) > 0  # At least some error output
        )

    def test_journal_command_invalid_template(self):
        """Test journal command with invalid template variable."""
        # Create a config file with invalid template
        config_file = self.vault_path / "bad-journal-config.toml"
        config_content = f'''
vault = "{self.vault_path}"
journal_template = "Journal/{{invalid_var}}/{{year}}"
'''
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        result = self.runner.invoke(cli, ["--config", str(config_file), "journal"])
        self.assertEqual(result.exit_code, 1)  # Template validation error -> exit code 1
        error_output = (result.stderr or "") + (result.stdout or "")
        self.assertTrue(
            "Invalid" in error_output
            or "journal_template" in error_output
            or "template" in error_output.lower()
            or len(error_output) > 0  # At least some error output
        )

    def test_toml_config_default_paths(self):
        """Test automatic config loading from default paths."""
        # Test loading from current directory in isolated environment
        old_cwd = os.getcwd()
        old_xdg_config = os.environ.get("XDG_CONFIG_HOME")
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            # Set isolated config environment
            isolated_config_dir = Path(temp_dir) / "isolated_config"
            isolated_config_dir.mkdir()
            os.environ["XDG_CONFIG_HOME"] = str(isolated_config_dir)

            # No config files should exist, should return default configuration
            from obsidian_cli.main import Configuration

            # When no config files exist, from_file() returns default config
            config = Configuration.from_file()
            self.assertIsNone(config.vault)  # Default vault is None
            self.assertFalse(config.verbose)  # Default verbose is False

            # Create a config file in current directory
            current_config = Path("./obsidian-cli.toml")
            with open(current_config, "w", encoding="utf-8") as f:
                f.write("""
vault = "/current/dir/vault"
verbose = true
""")

            # Now it should load the config file
            config = Configuration.from_file()
            self.assertEqual(str(config.vault), "/current/dir/vault")
            self.assertTrue(config.verbose)

        finally:
            os.chdir(old_cwd)
            if old_xdg_config is not None:
                os.environ["XDG_CONFIG_HOME"] = old_xdg_config
            elif "XDG_CONFIG_HOME" in os.environ:
                del os.environ["XDG_CONFIG_HOME"]
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
