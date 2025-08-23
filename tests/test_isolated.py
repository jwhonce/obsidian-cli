import os
import shutil
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from typer.testing import CliRunner

from obsidian_cli.main import cli


class TestIsolated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Move home config file to avoid test interference"""
        cls.home_config = Path.home() / ".config" / "obsidian-cli" / "config.toml"
        cls.home_backup = None
        if cls.home_config.exists():
            cls.home_backup = cls.home_config.with_suffix(".toml.backup")
            shutil.move(str(cls.home_config), str(cls.home_backup))

    @classmethod
    def tearDownClass(cls):
        """Restore home config file"""
        if cls.home_backup and cls.home_backup.exists():
            shutil.move(str(cls.home_backup), str(cls.home_config))

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "test_vault"
        self.vault_path.mkdir()
        self.runner = CliRunner()

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

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

    def test_journal_command_invalid_template(self):
        """Test journal command with invalid template variable"""
        # Create a config file with invalid template
        config_file = self.vault_path / "bad-journal-config.toml"
        config_content = f'''
vault = "{self.vault_path}"
journal_template = "Journal/{{invalid_var}}/{{year}}"
'''
        with open(config_file, "w") as f:
            f.write(config_content)

        result = self.runner.invoke(cli, ["--config", str(config_file), "journal"])
        self.assertEqual(result.exit_code, 1)  # Template validation error -> exit code 1

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


if __name__ == "__main__":
    unittest.main()
