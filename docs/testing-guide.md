# Testing Guide

This document describes testing strategies, patterns, and conventions for the Obsidian CLI project.

## Test Structure

### Test Organization

```
tests/
├── test_coverage_improvements.py    # Comprehensive coverage tests
├── test_obsidian_file_error.py     # ObsidianFileError-specific tests
└── __init__.py
```

### Test Categories

1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Command-line interface testing
3. **Error Handling Tests**: Exception and exit code validation
4. **Configuration Tests**: Configuration loading and parsing

## Test Framework

### Dependencies

- `unittest`: Python standard testing framework
- `typer.testing.CliRunner`: CLI command testing
- `unittest.mock`: Mocking and patching
- `tempfile`: Temporary file/directory creation

### Base Test Class

```python
import unittest
from typer.testing import CliRunner
from pathlib import Path

class TestCoverageImprovements(unittest.TestCase):
    """Base test class with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def _get_error_output(self, result):
        """Get error output from result, handling both stderr and mixed output."""
        try:
            return result.stderr or result.output
        except ValueError:
            return result.output
```

## Testing ObsidianFileError

### Basic Error Creation Tests

```python
def test_obsidian_file_error_creation(self):
    """Test creating ObsidianFileError with different parameters."""
    # Test with default exit code
    error = ObsidianFileError("config.toml", "Configuration not found")
    self.assertEqual(error.ui_filename, "config.toml")
    self.assertEqual(error.message, "Configuration not found")
    self.assertEqual(error.exit_code, 12)  # default

    # Test with custom exit code
    error = ObsidianFileError("note.md", "Note not found", exit_code=11)
    self.assertEqual(error.exit_code, 11)
```

### Inheritance Tests

```python
def test_obsidian_file_error_inheritance(self):
    """Test that ObsidianFileError inherits from FileError."""
    error = ObsidianFileError("test.txt", "Test error")
    self.assertIsInstance(error, FileError)
    self.assertIsInstance(error, ObsidianFileError)
```

### String Representation Tests

```python
def test_obsidian_file_error_string_representation(self):
    """Test string representations of ObsidianFileError."""
    error = ObsidianFileError("config.toml", "Configuration not found", exit_code=12)

    # Test __str__
    self.assertEqual(str(error), "Configuration not found: config.toml")

    # Test __repr__
    repr_str = repr(error)
    self.assertIn("ObsidianFileError", repr_str)
    self.assertIn("config.toml", repr_str)
    self.assertIn("exit_code=12", repr_str)
```

## CLI Testing Patterns

### Command Execution

```python
def test_command_success(self):
    """Test successful command execution."""
    with self.runner.isolated_filesystem():
        vault = Path("vault").resolve()
        vault.mkdir()

        # Create test file
        test_file = vault / "test.md"
        test_file.write_text("# Test Content")

        result = self.runner.invoke(cli, ["--vault", str(vault), "cat", "test"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test Content", result.output)
```

### Error Condition Testing

```python
def test_file_not_found_error(self):
    """Test file not found error handling."""
    with self.runner.isolated_filesystem():
        vault = Path("vault").resolve()
        vault.mkdir()

        result = self.runner.invoke(cli, ["--vault", str(vault), "cat", "nonexistent"])
        self.assertEqual(result.exit_code, 11)  # File resolution error
```

### Configuration Testing

```python
def test_configuration_error_handling(self):
    """Test configuration error scenarios."""
    runner = CliRunner()

    # Test ObsidianFileError from configuration
    with patch("obsidian_cli.utils.Configuration.from_path") as mock_from_path:
        mock_from_path.side_effect = ObsidianFileError(
            "config.toml", "Config file not found"
        )

        result = runner.invoke(cli, ["info"])
        self.assertEqual(result.exit_code, 12)  # Default ObsidianFileError exit code
```

## Exit Code Testing

### Exit Code Conventions

Test that commands return appropriate exit codes:

| Scenario                  | Expected Exit Code | Test Pattern                             |
| ------------------------- | ------------------ | ---------------------------------------- |
| Success                   | 0                  | `self.assertEqual(result.exit_code, 0)`  |
| File not found in vault   | 11                 | `self.assertEqual(result.exit_code, 11)` |
| Configuration error       | 12                 | `self.assertEqual(result.exit_code, 12)` |
| General application error | 1                  | `self.assertEqual(result.exit_code, 1)`  |
| CLI usage error           | 2                  | `self.assertEqual(result.exit_code, 2)`  |

### Exit Code Test Patterns

```python
def test_exit_codes(self):
    """Test various exit code scenarios."""

    # File resolution error (exit_code=11)
    result = self.runner.invoke(cli, ["--vault", "/tmp", "meta", "nonexistent"])
    self.assertEqual(result.exit_code, 11)

    # Configuration error (exit_code=12)
    with patch("obsidian_cli.utils.Configuration.from_path") as mock:
        mock.side_effect = ObsidianFileError("config.toml", "Not found")
        result = self.runner.invoke(cli, ["info"])
        self.assertEqual(result.exit_code, 12)

    # General application error (exit_code=1)
    with patch("some_function", side_effect=Exception("General error")):
        result = self.runner.invoke(cli, ["some-command"])
        self.assertEqual(result.exit_code, 1)
```

## Mocking Patterns

### Configuration Mocking

```python
def test_with_mocked_configuration(self):
    """Test with mocked configuration."""
    with patch("obsidian_cli.utils.Configuration.from_path") as mock_from_path:
        mock_config = Configuration(vault=Path("/test/vault"))
        mock_from_path.return_value = (None, mock_config)

        # Test logic here
```

### File System Mocking

```python
def test_with_mocked_filesystem(self):
    """Test with mocked file system operations."""
    with patch("pathlib.Path.exists", return_value=False):
        # Test file not found scenarios
        pass

    with patch("pathlib.Path.read_text", return_value="mock content"):
        # Test file reading scenarios
        pass
```

### External Command Mocking

```python
@patch("subprocess.call")
def test_external_command(self, mock_call):
    """Test external command execution."""
    mock_call.return_value = 0

    result = self.runner.invoke(cli, ["edit", "somefile"])
    self.assertEqual(result.exit_code, 0)
    mock_call.assert_called_once()
```

## Logging Tests

### Logger Mocking

```python
def test_logging_behavior(self):
    """Test that logging occurs as expected."""
    with patch("obsidian_cli.main.logger") as mock_logger:
        # Trigger logging
        result = self.runner.invoke(cli, ["some-command"])

        # Verify logging calls
        mock_logger.error.assert_called_once_with(
            "Expected error message: %s", "error_details"
        )
```

### Verbose Mode Testing

```python
def test_verbose_mode(self):
    """Test verbose mode logging."""
    with self.runner.isolated_filesystem():
        vault = Path("vault").resolve()
        vault.mkdir()

        # Test verbose flag
        result = self.runner.invoke(cli, ["--vault", str(vault), "--verbose", "info"])
        self.assertEqual(result.exit_code, 0)
        # In verbose mode, additional output should be present
```

## Temporary File Testing

### Isolated Filesystem

```python
def test_with_isolated_filesystem(self):
    """Test using isolated filesystem."""
    with self.runner.isolated_filesystem():
        # All file operations happen in temporary directory
        vault = Path("vault").resolve()
        vault.mkdir()

        test_file = vault / "test.md"
        test_file.write_text("content")

        # Test operations
```

### Temporary Directories

```python
def test_with_temp_directory(self):
    """Test using temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_dir = Path(temp_dir) / "vault"
        vault_dir.mkdir()

        # Test operations
```

## Error Message Testing

### Message Validation

```python
def test_error_messages(self):
    """Test that error messages are informative."""
    result = self.runner.invoke(cli, ["--vault", "/nonexistent", "info"])

    # Check that error message contains helpful information
    self.assertIn("Vault not found", result.output)
    self.assertIn("/nonexistent", result.output)
```

### Error Output Capture

```python
def test_error_output_capture(self):
    """Test error output capturing."""
    result = self.runner.invoke(cli, ["invalid-command"])

    error_output = self._get_error_output(result)
    self.assertIn("invalid-command", error_output)
```

## Performance Testing

### Basic Performance Tests

```python
def test_command_performance(self):
    """Test that commands complete in reasonable time."""
    import time

    start_time = time.time()
    result = self.runner.invoke(cli, ["--vault", "/tmp", "ls"])
    end_time = time.time()

    # Should complete within reasonable time
    self.assertLess(end_time - start_time, 5.0)
```

## Coverage Testing

### Coverage Patterns

```python
def test_branch_coverage(self):
    """Test different code branches."""

    # Test success path
    result = self.runner.invoke(cli, ["valid-command"])
    self.assertEqual(result.exit_code, 0)

    # Test error path
    result = self.runner.invoke(cli, ["invalid-command"])
    self.assertNotEqual(result.exit_code, 0)

    # Test edge cases
    result = self.runner.invoke(cli, ["command-with-edge-case"])
    # Assert appropriate behavior
```

### Exception Coverage

```python
def test_exception_coverage(self):
    """Test exception handling branches."""

    # Test FileNotFoundError
    with patch("pathlib.Path.exists", return_value=False):
        result = self.runner.invoke(cli, ["cat", "nonexistent"])
        self.assertEqual(result.exit_code, 11)

    # Test PermissionError
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        result = self.runner.invoke(cli, ["cat", "restricted"])
        self.assertEqual(result.exit_code, 1)
```

## Test Utilities

### Helper Functions

```python
def create_test_vault(self, vault_path: Path) -> Path:
    """Create a test vault with sample files."""
    vault_path.mkdir(exist_ok=True)

    # Create sample files
    (vault_path / "note1.md").write_text("""---
title: Note 1
tags: [test]
---
# Note 1 Content""")

    (vault_path / "note2.md").write_text("""---
title: Note 2
---
# Note 2 Content""")

    return vault_path

def assert_file_contains(self, file_path: Path, content: str):
    """Assert that file contains expected content."""
    self.assertTrue(file_path.exists())
    file_content = file_path.read_text()
    self.assertIn(content, file_content)
```

### Test Data Generation

```python
def generate_test_frontmatter(self, **kwargs) -> str:
    """Generate test frontmatter with specified fields."""
    default_data = {
        "title": "Test Title",
        "created": "2024-01-01",
        "tags": ["test"]
    }
    default_data.update(kwargs)

    yaml_content = "\n".join(f"{k}: {v}" for k, v in default_data.items())
    return f"---\n{yaml_content}\n---\n"
```

## Running Tests

### Test Execution

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_coverage_improvements.py

# Run with coverage
python -m pytest --cov=src/obsidian_cli tests/

# Run specific test method
python -m pytest tests/test_coverage_improvements.py::TestCoverageImprovements::test_specific_method
```

### Test Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

## Best Practices

### Test Naming

- Use descriptive test names that explain what is being tested
- Follow pattern: `test_<functionality>_<scenario>_<expected_result>`
- Group related tests in the same test class

### Test Organization

- One test class per major functionality
- Setup common test data in `setUp()` method
- Use helper methods for repeated test patterns
- Keep tests independent and isolated

### Assertion Patterns

```python
# Good: Specific assertions
self.assertEqual(result.exit_code, 11)
self.assertIn("expected message", result.output)

# Bad: Generic assertions
self.assertTrue(result.exit_code != 0)
self.assertTrue("expected" in result.output)
```

### Error Testing

- Test both success and error paths
- Verify specific exit codes
- Check error message content
- Test error recovery mechanisms

### Mock Usage

- Mock external dependencies
- Mock file system operations for consistent tests
- Mock network calls and external services
- Verify mock calls when testing interactions

## Debugging Tests

### Test Debugging

```python
def test_with_debug_output(self):
    """Test with debug output for troubleshooting."""
    result = self.runner.invoke(cli, ["command"])

    # Print output for debugging
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    print(f"Exception: {result.exception}")

    # Assertions
    self.assertEqual(result.exit_code, 0)
```

### Capturing Test Output

```python
import sys
from io import StringIO

def test_with_captured_output(self):
    """Test with captured stdout/stderr."""
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        # Run test
        result = self.runner.invoke(cli, ["command"])
        output = captured_output.getvalue()

        # Assertions
        self.assertIn("expected output", output)
    finally:
        sys.stdout = sys.__stdout__
```
