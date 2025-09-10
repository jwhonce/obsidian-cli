# Error Handling in Obsidian CLI

This document describes the error handling strategy and conventions used in the Obsidian CLI project.

## ObsidianFileError Class

The `ObsidianFileError` class is a project-specific enhancement of `click.FileError` that provides improved handling of file-related errors with standardized exit codes.

### Class Definition

```python
class ObsidianFileError(FileError):
    """Project-specific FileError with enhanced functionality.

    Encapsulates click.FileError with improved handling of file paths, messages,
    and exit codes for obsidian-cli specific operations.

    Attributes:
        file_path: Path to the file that caused the error
        message: Human-readable error message
        exit_code: Exit code to use when this error causes program termination
    """
```

### Constructor

```python
def __init__(self, file_path: Union[str, Path], message: Optional[str], exit_code: int = 12):
    """Initialize the ObsidianFileError.

    Args:
        file_path: Path to the file that caused the error (str or Path)
        message: Human-readable error message describing the issue
        exit_code: Exit code to use when this error terminates the program (default: 12)
    """
```

### Features

- **Enhanced Inheritance**: Inherits from `click.FileError` for compatibility with Click/Typer
- **Flexible Path Handling**: Accepts both string and `Path` objects
- **Custom Exit Codes**: Allows specification of exit codes for different error scenarios
- **Rich String Representations**: Provides formatted `__str__` and `__repr__` methods

### Usage Examples

```python
# Basic usage with default exit code (12)
raise ObsidianFileError("config.toml", "Configuration file not found")

# Custom exit code for specific scenarios
raise ObsidianFileError(
    Path("vault/note.md"),
    "Page not found in vault",
    exit_code=11
)

# Using Path objects
config_path = Path("~/.config/obsidian-cli/config.toml").expanduser()
raise ObsidianFileError(config_path, "Invalid configuration format")
```

## Exit Code Conventions

The Obsidian CLI uses a standardized set of exit codes to indicate different types of errors:

### Standard Exit Codes

| Exit Code | Description          | Usage                                             |
| --------- | -------------------- | ------------------------------------------------- |
| `0`       | Success              | Command completed successfully                    |
| `1`       | General Error        | Standard application errors                       |
| `2`       | Misuse/Invalid Usage | Command line usage errors, handled by Click/Typer |

### ObsidianFileError Exit Codes

| Exit Code | Description                      | Usage                                             |
| --------- | -------------------------------- | ------------------------------------------------- |
| `11`      | File Resolution Error            | File not found in vault via `_resolve_path()`     |
| `12`      | Configuration/General File Error | Default for configuration and general file errors |

### Exit Code Usage by Function

#### `_resolve_path()` Function

- **Exit Code**: `11`
- **Usage**: When a file cannot be found in the Obsidian vault
- **Example**: `obsidian-cli meta nonexistent-file`

```python
raise ObsidianFileError(
    page_or_path,
    f"Page or File not found in vault: {vault}",
    exit_code=11
)
```

#### Configuration Loading

- **Exit Code**: `12` (default)
- **Usage**: Configuration file errors, TOML parsing issues
- **Example**: Missing or invalid configuration files

```python
raise ObsidianFileError(path, "Configuration file not found")
# Uses default exit_code=12
```

## Error Handling Patterns

### Configuration Errors

```python
try:
    (source, configuration) = Configuration.from_path(config, verbose=verbose)
except (FileError, ObsidianFileError):
    # Re-raise file errors to be handled by Click/Typer
    raise
except Exception as e:
    # Handle other configuration errors
    typer.secho(f"Error loading configuration: {e}", err=True, fg=typer.colors.RED)
    raise typer.Exit(code=2) from e
```

### File Resolution Errors

```python
def _resolve_path(page_or_path: Path, vault: Path) -> Path:
    # Try various path resolution strategies
    # ...

    # If all strategies fail
    raise ObsidianFileError(
        page_or_path,
        f"Page or File not found in vault: {vault}",
        exit_code=11
    )
```

### Command-Level Error Handling

```python
def some_command(page_name: str, state: State):
    try:
        resolved_path = _resolve_path(Path(page_name), state.vault)
        # Command logic here
    except ObsidianFileError:
        # Let Click/Typer handle the exit code
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise typer.Exit(code=1) from e
```

## Testing Error Handling

### Test Patterns

```python
def test_file_not_found_error(self):
    """Test that file not found errors use correct exit code."""
    result = self.runner.invoke(cli, ["--vault", str(vault), "meta", "nonexistent"])
    self.assertEqual(result.exit_code, 11)  # File resolution error

def test_configuration_error(self):
    """Test that configuration errors use correct exit code."""
    with patch("obsidian_cli.utils.Configuration.from_path") as mock_from_path:
        mock_from_path.side_effect = ObsidianFileError(
            "config.toml", "Config file not found"  # Uses default exit_code=12
        )
        result = self.runner.invoke(cli, ["info"])
        self.assertEqual(result.exit_code, 12)
```

### Test Utilities

```python
def assert_file_error(self, result, expected_exit_code, expected_message_fragment=None):
    """Helper to assert file error conditions."""
    self.assertNotEqual(result.exit_code, 0)
    self.assertEqual(result.exit_code, expected_exit_code)
    if expected_message_fragment:
        self.assertIn(expected_message_fragment, result.output)
```

## Best Practices

### When to Use ObsidianFileError

1. **File Operations**: Use for file-related errors in the application layer
2. **Configuration Loading**: Use for configuration file issues
3. **Vault Operations**: Use for vault-specific file operations

### When NOT to Use ObsidianFileError

1. **Click/Typer Validation**: Let Click/Typer handle command line validation
2. **Network Errors**: Use appropriate network-specific exceptions
3. **Permission Errors**: Use standard Python exceptions with appropriate handling

### Error Message Guidelines

1. **Be Specific**: Include file paths and context
2. **Be Helpful**: Suggest solutions when possible
3. **Be Consistent**: Use similar language patterns across the application

```python
# Good
raise ObsidianFileError(
    config_path,
    f"Configuration file not found. Create one at {config_path} or use --config"
)

# Better context
raise ObsidianFileError(
    page_path,
    f"Page '{page_path.stem}' not found in vault '{vault}'. Check the filename and try again."
)
```

## Migration Guide

### From Standard FileError

```python
# Old pattern
e = FileError(str(path), "File not found")
e.exit_code = 2
raise e

# New pattern
raise ObsidianFileError(path, "File not found", exit_code=12)
```

### Updating Tests

```python
# Old test expectation
self.assertEqual(result.exit_code, 2)

# New test expectation (depends on error type)
self.assertEqual(result.exit_code, 11)  # For file resolution errors
self.assertEqual(result.exit_code, 12)  # For configuration errors
```

## Troubleshooting

### Common Issues

1. **Wrong Exit Code**: Ensure you're using the correct exit code for the error type
2. **Test Failures**: Update test expectations to match new exit codes
3. **Click Compatibility**: Ensure ObsidianFileError inherits properly from FileError

### Debugging Tips

1. Use `repr(error)` to see detailed error information
2. Check exit codes in tests to ensure proper error handling
3. Use logging to trace error propagation through the application
