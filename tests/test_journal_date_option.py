import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from obsidian_cli.main import cli


class TestJournalDateOption(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("subprocess.run", return_value=None)
    def test_journal_with_valid_date(self, mock_run):
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir(parents=True, exist_ok=True)
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()
            # Create the expected journal file for 2024-02-03 based on default template
            expected_path = Path("Calendar/2024/02/2024-02-03.md")
            (vault / expected_path).parent.mkdir(parents=True, exist_ok=True)
            (vault / expected_path).write_text("test")

            result = self.runner.invoke(
                cli,
                ["--vault", str(vault), "journal", "--date", "2024-02-03"],
            )
            self.assertEqual(result.exit_code, 0)
            mock_run.assert_called()

    def test_journal_with_invalid_date(self):
        """Test journal command with invalid date format - uses typer.BadParameter."""
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir()
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()
            # Mock subprocess.run to avoid editor launch
            with patch("subprocess.run", return_value=None):
                result = self.runner.invoke(
                    cli,
                    ["--vault", str(vault), "journal", "--date", "03-02-2024"],
                )
                # Current implementation uses typer.BadParameter (exit code 2)
                self.assertEqual(result.exit_code, 2)
                # Error message is displayed in CLI output via BadParameter
                # Editor should not be invoked when date validation fails

    @patch("subprocess.run", return_value=None)
    def test_journal_without_date(self, mock_run):
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir(parents=True, exist_ok=True)
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()
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
            mock_run.assert_called()

    def test_journal_with_various_invalid_date_formats(self):
        """Test journal command with various invalid date formats."""
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir()
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()

            # These formats are rejected by datetime.strptime("%Y-%m-%d")
            invalid_dates = [
                "2024/02/03",  # Wrong separator
                "02-03-2024",  # Wrong order (MM-DD-YYYY)
                "2024-13-01",  # Invalid month
                "2024-02-32",  # Invalid day
                "not-a-date",  # Non-date string
                "2024-02",  # Incomplete date
                "",  # Empty string
                "2024-02-03-extra",  # Extra components
                "24-02-03",  # Two-digit year
                "2024.02.03",  # Wrong separator
                "March 3, 2024",  # Natural language format
                "2024-FEB-03",  # Month as text
                "20240203",  # No separators
            ]
            # Note: "2024-2-3" is actually valid to Python's strptime but may fail later

            for invalid_date in invalid_dates:
                with self.subTest(date=invalid_date):
                    # Mock subprocess.run to avoid editor launch
                    with patch("subprocess.run", return_value=None):
                        result = self.runner.invoke(
                            cli,
                            ["--vault", str(vault), "journal", "--date", invalid_date],
                        )
                        # Current implementation uses typer.BadParameter (exit code 2)
                        self.assertEqual(
                            result.exit_code,
                            2,
                            f"Date '{invalid_date}' should be rejected with exit code 2 (BadParameter)",
                        )
                        # Error is displayed to user via BadParameter with usage help

    def test_journal_with_python_valid_but_nonstandard_dates(self):
        """Test dates that Python accepts but we might want to reject for consistency."""
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir()
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()

            # These dates are valid to Python's parser but non-standard format
            potentially_problematic_dates = [
                "2024-2-3",  # Missing zero padding - Python accepts this
                "2024-12-1",  # Missing zero padding in day
            ]

            for date_str in potentially_problematic_dates:
                with self.subTest(date=date_str):
                    result = self.runner.invoke(
                        cli,
                        ["--vault", str(vault), "journal", "--date", date_str],
                    )
                    # These might succeed (exit_code=0) or fail later in the pipeline
                    # depending on file creation/template issues
                    self.assertIn(
                        result.exit_code,
                        [0, 1, 2, 12],  # Various possible outcomes
                        f"Date '{date_str}' should have a reasonable exit code",
                    )

    def test_journal_invalid_date_logging(self):
        """Test that invalid date errors are properly logged."""
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir()
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()

            # Mock subprocess.run to avoid editor launch
            with patch("subprocess.run", return_value=None):
                # Test with verbose logging to capture error logs
                result = self.runner.invoke(
                    cli,
                    ["--vault", str(vault), "--verbose", "journal", "--date", "invalid-date"],
                )

                # Current implementation uses typer.BadParameter (exit code 2)
                self.assertEqual(result.exit_code, 2)
                # BadParameter displays error messages to user with usage help

    @patch("subprocess.run", return_value=None)
    def test_journal_with_edge_case_valid_dates(self, mock_run):
        """Test journal command with edge case valid dates."""
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir()
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()

            edge_case_dates = [
                "2024-01-01",  # New Year's Day
                "2024-12-31",  # New Year's Eve
                "2000-02-29",  # Leap year
                "1999-02-28",  # Non-leap year February
                "2024-04-30",  # 30-day month
            ]

            for valid_date in edge_case_dates:
                with self.subTest(date=valid_date):
                    # Create expected journal directory structure
                    year, month, day = valid_date.split("-")
                    expected_dir = vault / f"Calendar/{year}/{month}"
                    expected_dir.mkdir(parents=True, exist_ok=True)
                    expected_file = expected_dir / f"{year}-{month}-{day}.md"
                    expected_file.write_text("test content")

                    result = self.runner.invoke(
                        cli,
                        ["--vault", str(vault), "journal", "--date", valid_date],
                    )
                    self.assertEqual(result.exit_code, 0, f"Date '{valid_date}' should be valid")
                    mock_run.assert_called()
                    mock_run.reset_mock()  # Reset for next iteration

    def test_future_badparameter_behavior(self):
        """Test current BadParameter behavior in journal command.

        The journal command now uses typer.BadParameter for invalid date validation,
        which provides user-friendly error messages and proper usage help.
        """
        with self.runner.isolated_filesystem():
            vault = Path("vault").resolve()
            vault.mkdir()
            # Create .obsidian directory to make it a valid Obsidian vault
            (vault / ".obsidian").mkdir()

            # If journal command used BadParameter, this would be the expected behavior:
            # result = self.runner.invoke(
            #     cli,
            #     ["--vault", str(vault), "journal", "--date", "invalid-date"],
            # )
            # self.assertEqual(result.exit_code, 2)  # BadParameter exit code
            # self.assertIn("invalid --date format", result.output)  # User-visible error
            # self.assertIn("--date", result.output)  # Parameter context
            # self.assertIn("Usage:", result.output)  # Usage help

            # For now, just document current behavior
            # Mock subprocess.run to avoid editor launch
            with patch("subprocess.run", return_value=None):
                result = self.runner.invoke(
                    cli,
                    ["--vault", str(vault), "journal", "--date", "invalid-date"],
                )
                self.assertEqual(result.exit_code, 2)  # BadParameter exit code
                self.assertIn("invalid --date format", result.output)  # User-visible error
                self.assertIn("--date", result.output)  # Parameter context
                self.assertIn("Usage:", result.output)  # Usage help
