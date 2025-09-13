#!/usr/bin/env python3
"""
Comprehensive test validation and fix script.
"""

import os
import sys
import unittest
from io import StringIO
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def validate_test_environment():
    """Validate that the test environment is properly set up."""
    print("=== Validating Test Environment ===")

    # Check Python version
    print(f"Python version: {sys.version}")

    # Check required imports
    required_modules = [
        "typer",
        "click",
        "frontmatter",
        "rich",
        "tomllib",
    ]

    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False

    # Check obsidian-cli imports
    try:
        from obsidian_cli.exceptions import ObsidianFileError
        from obsidian_cli.main import cli
        from obsidian_cli.types import Configuration

        print("✓ obsidian-cli modules")
    except ImportError as e:
        print(f"❌ obsidian-cli modules: {e}")
        return False

    return True


def run_individual_test(test_class, test_method):
    """Run an individual test method."""
    suite = unittest.TestSuite()
    suite.addTest(test_class(test_method))

    # Capture output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    output = stream.getvalue()
    return result.wasSuccessful(), output


def validate_exit_codes():
    """Validate that exit codes work as expected."""
    print("\n=== Validating Exit Codes ===")

    try:
        from obsidian_cli.exceptions import ObsidianFileError

        # Test default exit code
        error = ObsidianFileError("test.txt", "Test message")
        assert error.exit_code == 12, f"Expected 12, got {error.exit_code}"
        print("✓ Default exit_code is 12")

        # Test custom exit code
        error_custom = ObsidianFileError("test.txt", "Test message", exit_code=11)
        assert error_custom.exit_code == 11, f"Expected 11, got {error_custom.exit_code}"
        print("✓ Custom exit_code works")

        # Test inheritance
        from click import FileError

        assert isinstance(error, FileError), "ObsidianFileError should inherit from FileError"
        print("✓ Inheritance works")

        return True

    except Exception as e:
        print(f"❌ Exit code validation failed: {e}")
        return False


def run_critical_tests():
    """Run the most critical tests."""
    print("\n=== Running Critical Tests ===")

    try:
        from tests.test_coverage_improvements import TestCoverageImprovements

        critical_tests = [
            "test_obsidian_file_error_default_behavior",
            "test_version_callback",
            "test_resolve_path_error_code_updated",
        ]

        failed_tests = []

        for test_name in critical_tests:
            success, output = run_individual_test(TestCoverageImprovements, test_name)
            if success:
                print(f"✓ {test_name}")
            else:
                print(f"❌ {test_name}")
                failed_tests.append((test_name, output))

        if failed_tests:
            print(f"\n{len(failed_tests)} tests failed:")
            for test_name, output in failed_tests:
                print(f"\n--- {test_name} ---")
                print(output)
            return False

        return True

    except Exception as e:
        print(f"❌ Critical tests failed: {e}")
        return False


def fix_common_issues():
    """Fix common issues that might cause test failures."""
    print("\n=== Checking for Common Issues ===")

    # Check if pyproject.toml exists
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_path.exists():
        print("⚠️  pyproject.toml not found - this might cause import issues")
    else:
        print("✓ pyproject.toml exists")

    # Check src structure
    src_path = Path(__file__).parent.parent / "src" / "obsidian_cli"
    if not src_path.exists():
        print("❌ src/obsidian_cli directory not found")
        return False
    else:
        print("✓ src/obsidian_cli directory exists")

    # Check for __init__.py files
    init_files = [
        src_path / "__init__.py",
        src_path.parent / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            print(f"⚠️  {init_file} missing - creating empty file")
            init_file.touch()
        else:
            print(f"✓ {init_file} exists")

    return True


def main():
    """Main validation and fix function."""
    print("=== Obsidian CLI Test Validation and Fix ===\n")

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    success = True

    # Validate environment
    if not validate_test_environment():
        print("❌ Environment validation failed")
        success = False

    # Fix common issues
    if not fix_common_issues():
        print("❌ Could not fix common issues")
        success = False

    # Validate exit codes
    if not validate_exit_codes():
        print("❌ Exit code validation failed")
        success = False

    # Run critical tests
    if not run_critical_tests():
        print("❌ Critical tests failed")
        success = False

    if success:
        print("\n✅ All validations passed! Tests should work correctly.")
        return 0
    else:
        print("\n❌ Some validations failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
