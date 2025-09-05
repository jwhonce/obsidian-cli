"""Unit tests for find command helper functions."""

import tempfile
import unittest
from pathlib import Path

import frontmatter

from obsidian_cli.main import (
    _check_filename_match,
    _check_if_path_blacklisted,
    _check_title_match,
    _find_matching_files,
    _get_frontmatter,
)


class TestFindHelpers(unittest.TestCase):
    """Test the helper functions used by the find command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_check_filename_match_exact(self):
        """Test exact filename matching."""
        # Exact match should match exactly
        self.assertTrue(_check_filename_match("test_file", "test_file", exact_match=True))
        self.assertFalse(_check_filename_match("test_file", "test", exact_match=True))
        self.assertFalse(_check_filename_match("test_file", "TEST_FILE", exact_match=True))

    def test_check_filename_match_fuzzy(self):
        """Test fuzzy filename matching."""
        # Fuzzy match should be case-insensitive and allow partial matches
        self.assertTrue(_check_filename_match("test_file", "test", exact_match=False))
        self.assertTrue(_check_filename_match("TEST_FILE", "test", exact_match=False))
        self.assertTrue(_check_filename_match("My_Test_File", "test", exact_match=False))
        self.assertFalse(_check_filename_match("example", "test", exact_match=False))

    def test_check_title_match(self):
        """Test title matching in frontmatter."""
        # Test with title that matches
        post = frontmatter.Post("content", title="My Test Title")
        self.assertTrue(_check_title_match(post, "test"))
        self.assertTrue(_check_title_match(post, "title"))
        # Case insensitive (search term should be lowercase)
        self.assertTrue(_check_title_match(post, "test"))

        # Test with title that doesn't match
        self.assertFalse(_check_title_match(post, "nonexistent"))

        # Test with no title in frontmatter
        post_no_title = frontmatter.Post("content", author="John Doe")
        self.assertFalse(_check_title_match(post_no_title, "test"))

        # Test with non-string title
        post_non_string = frontmatter.Post("content", title=123)
        self.assertFalse(_check_title_match(post_non_string, "test"))

    def test_check_if_path_ignored(self):
        """Test path ignoring logic."""
        ignored_dirs = ["Content/Archives/", "Assets/", ".obsidian/", ".git/"]

        # Test ignored paths
        self.assertTrue(
            _check_if_path_blacklisted(Path("Content/Archives/old_file.md"), ignored_dirs)
        )
        self.assertTrue(_check_if_path_blacklisted(Path("Assets/image.png"), ignored_dirs))
        self.assertTrue(_check_if_path_blacklisted(Path(".obsidian/config.json"), ignored_dirs))
        self.assertTrue(_check_if_path_blacklisted(Path(".git/config"), ignored_dirs))

        # Test non-ignored paths
        self.assertFalse(_check_if_path_blacklisted(Path("Notes/daily.md"), ignored_dirs))
        self.assertFalse(_check_if_path_blacklisted(Path("Projects/project1.md"), ignored_dirs))
        self.assertFalse(_check_if_path_blacklisted(Path("readme.md"), ignored_dirs))

    def test_get_frontmatter(self):
        """Test frontmatter extraction."""
        # Create a test file with frontmatter
        test_file = self.vault_path / "test.md"
        post = frontmatter.Post("Test content", title="Test Title", tags=["test", "example"])
        with open(test_file, "w") as f:
            f.write(frontmatter.dumps(post))

        # Test extracting frontmatter
        extracted_post = _get_frontmatter(test_file)
        self.assertEqual(extracted_post.metadata["title"], "Test Title")
        self.assertEqual(extracted_post.metadata["tags"], ["test", "example"])
        self.assertEqual(extracted_post.content, "Test content")

        # Create a test file without frontmatter
        test_file_no_fm = self.vault_path / "no_frontmatter.md"
        with open(test_file_no_fm, "w") as f:
            f.write("Just plain content")

        # Test extracting from file without frontmatter
        extracted_post_no_fm = _get_frontmatter(test_file_no_fm)
        self.assertEqual(len(extracted_post_no_fm.metadata), 0)
        self.assertEqual(extracted_post_no_fm.content, "Just plain content")

    def test_find_matching_files(self):
        """Test the main file finding logic."""
        # Create test files
        test_files = [
            ("daily_note.md", {"title": "Daily Note"}),
            ("weekly_summary.md", {"title": "Weekly Summary"}),
            ("task_list.md", {"title": "Task List"}),
            ("meeting_notes.md", {}),  # No title
        ]

        for filename, metadata in test_files:
            file_path = self.vault_path / filename
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Test fuzzy search by filename
        matches = _find_matching_files(self.vault_path, "daily", exact_match=False)
        self.assertEqual(len(matches), 1)
        self.assertIn(Path("daily_note.md"), matches)

        # Test fuzzy search by title
        matches = _find_matching_files(self.vault_path, "summary", exact_match=False)
        self.assertEqual(len(matches), 1)
        self.assertIn(Path("weekly_summary.md"), matches)

        # Test exact search
        matches = _find_matching_files(self.vault_path, "daily_note", exact_match=True)
        self.assertEqual(len(matches), 1)
        self.assertIn(Path("daily_note.md"), matches)

        # Test no matches
        matches = _find_matching_files(self.vault_path, "nonexistent", exact_match=False)
        self.assertEqual(len(matches), 0)

        # Test case insensitive search (search term should be lowercase for fuzzy search)
        matches = _find_matching_files(self.vault_path, "daily", exact_match=False)
        self.assertEqual(len(matches), 1)
        self.assertIn(Path("daily_note.md"), matches)

    def test_find_matching_files_with_subdirectories(self):
        """Test finding files in subdirectories."""
        # Create subdirectory structure
        subdir = self.vault_path / "notes" / "daily"
        subdir.mkdir(parents=True)

        # Create test files in subdirectories
        test_files = [
            ("notes/daily/monday.md", {"title": "Monday Note"}),
            ("notes/daily/tuesday.md", {"title": "Tuesday Note"}),
            ("top_level.md", {"title": "Top Level"}),
        ]

        for filepath, metadata in test_files:
            file_path = self.vault_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            post = frontmatter.Post("Test content", **metadata)
            with open(file_path, "w") as f:
                f.write(frontmatter.dumps(post))

        # Test finding files in subdirectories
        matches = _find_matching_files(self.vault_path, "monday", exact_match=False)
        self.assertEqual(len(matches), 1)
        self.assertIn(Path("notes/daily/monday.md"), matches)

        # Test finding by title in subdirectories
        matches = _find_matching_files(self.vault_path, "note", exact_match=False)
        # Should find all files with "note" in filename or title
        self.assertTrue(len(matches) >= 2)
        relative_paths = [str(p) for p in matches]
        self.assertTrue(any("monday.md" in p for p in relative_paths))
        self.assertTrue(any("tuesday.md" in p for p in relative_paths))

    def test_find_matching_files_with_malformed_frontmatter(self):
        """Test that find handles malformed frontmatter gracefully."""
        # Create a file with malformed frontmatter
        malformed_file = self.vault_path / "malformed.md"
        with open(malformed_file, "w") as f:
            f.write("---\ntitle: Unclosed quote\nbroken: yaml]\n---\nContent")

        # Create a normal file
        normal_file = self.vault_path / "normal.md"
        post = frontmatter.Post("Test content", title="Normal File")
        with open(normal_file, "w") as f:
            f.write(frontmatter.dumps(post))

        # Should still find files by filename even with malformed frontmatter
        matches = _find_matching_files(self.vault_path, "malformed", exact_match=False)
        self.assertEqual(len(matches), 1)
        self.assertIn(Path("malformed.md"), matches)

        # Should find normal files by title
        matches = _find_matching_files(self.vault_path, "normal", exact_match=False)
        self.assertTrue(len(matches) >= 1)
        self.assertIn(Path("normal.md"), matches)


if __name__ == "__main__":
    unittest.main()
