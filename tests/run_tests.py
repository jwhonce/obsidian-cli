#!/usr/bin/env python3
"""
Test runner script to identify and fix failing tests.
"""

import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obsidian_cli.exceptions import ObsidianFileError
from tests.test_coverage_improvements import TestCoverageImprovements


def run_specific_tests():
    """Run specific tests that might be failing."""

    # Create test suite with potentially problematic tests
    suite = unittest.TestSuite()

    # Add tests that are most likely to fail
    test_methods = [
        "test_obsidian_file_error_default_behavior",
        "test_resolve_path_error_code_updated",
        "test_configuration_error_exit_codes",
        "test_file_resolution_commands_exit_codes",
        "test_meta_file_not_found",
        "test_rm_file_not_found_error_logging",
    ]

    for method in test_methods:
        if hasattr(TestCoverageImprovements, method):
            suite.addTest(TestCoverageImprovements(method))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def validate_imports():
    """Validate that all required imports are available."""
    try:
        from obsidian_cli.exceptions import ObsidianFileError
        from obsidian_cli.main import cli, main
        from obsidian_cli.types import Configuration, State
        from obsidian_cli.utils import _get_vault_info

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def check_obsidian_file_error():
    """Check ObsidianFileError behavior."""
    try:
        # Test default exit code
        error = ObsidianFileError("test.txt", "Test message")
        assert error.exit_code == 12, f"Expected exit_code=12, got {error.exit_code}"

        # Test custom exit code
        error_custom = ObsidianFileError("test.txt", "Test message", exit_code=11)
        assert error_custom.exit_code == 11, f"Expected exit_code=11, got {error_custom.exit_code}"

        # Test string representation
        error_str = str(error)
        assert "Test message: test.txt" == error_str, f"Unexpected string: {error_str}"

        print("✓ ObsidianFileError behavior correct")
        return True
    except Exception as e:
        print(f"❌ ObsidianFileError test failed: {e}")
        return False


def main():
    """Main test runner."""
    print("=== Test Validation Runner ===\n")

    # Check imports
    if not validate_imports():
        return 1

    # Check ObsidianFileError
    if not check_obsidian_file_error():
        return 1

    # Run specific tests
    print("\n=== Running Specific Tests ===")
    if run_specific_tests():
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
