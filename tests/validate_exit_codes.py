#!/usr/bin/env python3
"""
Exit Code Validation Utility

This script validates that the current test suite expectations match
the actual ObsidianFileError behavior in the codebase.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_cli.exceptions import ObsidianFileError


def test_obsidian_file_error_defaults():
    """Test ObsidianFileError default behavior."""
    print("Testing ObsidianFileError default exit code...")

    # Test default exit code
    error = ObsidianFileError("test.txt", "Test message")
    assert error.exit_code == 12, f"Expected exit_code=12, got {error.exit_code}"
    print("✓ Default exit_code is 12")

    # Test custom exit code
    error_custom = ObsidianFileError("test.txt", "Test message", exit_code=11)
    assert error_custom.exit_code == 11, f"Expected exit_code=11, got {error_custom.exit_code}"
    print("✓ Custom exit_code still works")

    # Test string representation
    error_str = str(error)
    assert "Test message: test.txt" == error_str, f"Unexpected string representation: {error_str}"
    print("✓ String representation correct")

    print("All ObsidianFileError tests passed!")


def check_resolve_path_behavior():
    """Check _resolve_path function behavior."""
    print("\nChecking _resolve_path behavior...")

    # Import the function
    from obsidian_cli.utils import _resolve_path

    # Test with non-existent paths
    try:
        _resolve_path(Path("nonexistent"), Path("/tmp"))
        raise AssertionError("Expected ObsidianFileError to be raised")
    except ObsidianFileError as e:
        assert e.exit_code == 12, f"Expected exit_code=12, got {e.exit_code}"
        print("✓ _resolve_path uses default exit_code=12")

    print("_resolve_path behavior validated!")


def main():
    """Run all validation tests."""
    print("=== ObsidianFileError Exit Code Validation ===\n")

    try:
        test_obsidian_file_error_defaults()
        check_resolve_path_behavior()
        print("\n=== All validations passed! ===")
        print("\nCurrent exit code behavior:")
        print("- ObsidianFileError default: 12")
        print("- _resolve_path errors: 12 (uses default)")
        print("- Configuration errors: 12 (uses default)")
        print("- General app errors: 1")
        print("- CLI usage errors: 2 (Click/Typer)")
        print("- Success: 0")

        return 0

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
