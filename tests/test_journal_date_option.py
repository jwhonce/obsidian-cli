import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from obsidian_cli.main import cli


class TestJournalDateOption(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("subprocess.call", return_value=0)
    def test_journal_with_valid_date(self, mock_call):
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir(parents=True, exist_ok=True)
            # Create the expected journal file for 2024-02-03 based on default template
            expected_path = Path("Calendar/2024/02/2024-02-03.md")
            (vault / expected_path).parent.mkdir(parents=True, exist_ok=True)
            (vault / expected_path).write_text("test")

            result = self.runner.invoke(
                cli,
                ["--vault", str(vault), "journal", "--date", "2024-02-03"],
            )
            self.assertEqual(result.exit_code, 0)
            mock_call.assert_called()

    @patch("subprocess.call", return_value=0)
    def test_journal_with_invalid_date(self, mock_call):
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir()
            result = self.runner.invoke(
                cli,
                ["--vault", str(vault), "journal", "--date", "03-02-2024"],
            )
            self.assertEqual(result.exit_code, 1)
            # With logging changes, we verify the exit code confirms the error path was taken

    @patch("subprocess.call", return_value=0)
    def test_journal_without_date(self, mock_call):
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir(parents=True, exist_ok=True)
            # Create today's expected journal file based on default template variables
            # Compute directory structure consistent with default template
            from datetime import datetime

            today = datetime.now()
            expected_dir = Path(f"Calendar/{today.year}/{today.month:02d}")
            expected_file = expected_dir / f"{today.year}-{today.month:02d}-{today.day:02d}.md"
            (vault / expected_dir).mkdir(parents=True, exist_ok=True)
            (vault / expected_file).write_text("today")

            result = self.runner.invoke(cli, ["--vault", str(vault), "journal"])
            self.assertEqual(result.exit_code, 0)
            mock_call.assert_called()
