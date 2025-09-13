# API Reference

This document provides detailed API reference for the Obsidian CLI project.

## Module Organization

The Obsidian CLI codebase is organized into the following modules:

- **`configuration.py`** - Configuration class and TOML file handling
- **`exceptions.py`** - Project-specific exception classes 
- **`main.py`** - CLI commands, State class, and main application logic
- **`mcp_server.py`** - Model Context Protocol server functionality
- **`utils.py`** - Utility functions for file operations, display, and vault management

## Classes

### ObsidianFileError

**Location**: `src/obsidian_cli/exceptions.py`

**Inheritance**: `click.FileError` → `ObsidianFileError`

Enhanced FileError class with project-specific functionality.

#### Constructor

```python
def __init__(self, file_path: Union[str, Path], message: Optional[str], exit_code: int = 12)
```

**Parameters**:

- `file_path` (Union[str, Path]): Path to the file that caused the error
- `message` (Optional[str]): Human-readable error message
- `exit_code` (int): Exit code for program termination (default: 12)

#### Methods

##### `__str__() -> str`

Returns formatted error message.

**Returns**: String in format `"{message}: {filename}"`

##### `__repr__() -> str`

Returns detailed representation for debugging.

**Returns**: String with class name and all attributes

#### Attributes

- `exit_code` (int): Exit code to use when this error terminates the program
- `ui_filename` (str): Filename for user display (inherited from FileError)
- `message` (Optional[str]): Error message (inherited from FileError)

### Configuration

**Location**: `src/obsidian_cli/configuration.py`

**Type**: `@dataclass(frozen=True)`

Immutable configuration class for obsidian-cli application settings.

#### Fields

- `blacklist` (list[str]): Directory patterns to ignore (default:
  `["Assets/", ".obsidian/", ".git/"]`)
- `config_dirs` (list[Path]): Configuration file search paths
- `editor` (Path): Default editor command (default: `Path("vi")`)
- `ident_key` (str): Identifier key for frontmatter (default: `"uid"`)
- `journal_template` (str): Template for journal file paths
- `vault` (Optional[Path]): Path to Obsidian vault
- `verbose` (bool): Verbose output flag (default: `False`)

#### Class Methods

##### `from_path(path: Optional[Union[str, Path]] = None, verbose: bool = False) -> Tuple[bool, "Configuration"]`

Load configuration from TOML file.

**Returns:**
- `Tuple[bool, Configuration]`: (True if config was read from file, False if using defaults, Configuration instance)

**Parameters**:

- `path` (Optional[Union[str, Path]]): Configuration file path or colon-separated paths
- `verbose` (bool): Whether to print parsing messages

**Returns**: Tuple of (config_file_path, configuration_instance)

**Raises**: `ObsidianFileError` when configuration file not found

##### `_load_toml_config(path: Path, verbose: bool = False) -> Union[dict[str, Any] | None]`

Static method to load TOML configuration from file.

**Parameters**:

- `path` (Path): Path to configuration file
- `verbose` (bool): Whether to print parsing messages

**Returns**: Dictionary of configuration data

**Raises**:

- `ObsidianFileError` when file not found
- `tomllib.TOMLDecodeError` when TOML parsing fails

## Utility Functions

### File Operations

#### `_resolve_path(page_or_path: Path, vault: Path) -> Path`

Resolve file path within Obsidian vault.

**Parameters**:

- `page_or_path` (Path): Path to resolve (absolute or relative to vault)
- `vault` (Path): Obsidian vault root directory

**Returns**: Resolved absolute path to file

**Raises**: `ObsidianFileError` (exit_code=11) when file cannot be found

**Behavior**:

1. Checks if path exists as-is with `.md` extension
2. Checks if path exists relative to vault with `.md` extension
3. Raises error if neither location contains the file

#### `_get_frontmatter(filename: Path) -> frontmatter.Post`

Parse frontmatter from markdown file.

**Parameters**:

- `filename` (Path): Path to markdown file

**Returns**: Frontmatter Post object with metadata and content

**Raises**: `FileNotFoundError` when file doesn't exist

### Search and Query Functions

#### `_find_matching_files(vault: Path, search_name: str, exact_match: bool) -> list[Path]`

Find files matching search criteria.

**Parameters**:

- `vault` (Path): Obsidian vault directory
- `search_name` (str): Search term for filenames and titles
- `exact_match` (bool): Whether to require exact filename match

**Returns**: List of relative paths to matching files

**Search Strategy**:

1. Searches all `.md` files in vault recursively
2. Matches against filename stem (without extension)
3. If not exact match, also searches frontmatter titles
4. Returns deduplicated results

#### `_check_filename_match(file_stem: str, search_name: str, exact_match: bool) -> bool`

Check if filename matches search criteria.

**Parameters**:

- `file_stem` (str): Filename without extension
- `search_name` (str): Search term
- `exact_match` (bool): Exact vs. substring matching

**Returns**: True if filename matches criteria

#### `_check_title_match(post: frontmatter.Post, search_name: str) -> bool`

Check if frontmatter title matches search criteria.

**Parameters**:

- `post` (frontmatter.Post): Frontmatter object
- `search_name` (str): Search term

**Returns**: True if title contains search term (case-insensitive)

#### `_check_if_path_blacklisted(rel_path: Path, blacklist: list[str]) -> bool`

Check if path should be ignored based on blacklist patterns.

**Parameters**:

- `rel_path` (Path): Relative path to check
- `blacklist` (list[str]): List of directory patterns to ignore

**Returns**: True if path should be blacklisted

### Display Functions

#### `_display_find_results(matches: list[Path], page_name: str, verbose: bool, vault: Path) -> None`

Display search results to stdout.

**Parameters**:

- `matches` (list[Path]): List of matching file paths
- `page_name` (str): Original search term
- `verbose` (bool): Whether to show additional metadata
- `vault` (Path): Vault path for resolving relative paths

**Behavior**:

- Shows "No files found" message if no matches
- Lists matched files in sorted order
- In verbose mode, shows frontmatter titles

#### `_display_query_results(matches: list[tuple[Path, frontmatter.Post]], format_type, key: str) -> None`

Display frontmatter query results in specified format.

**Parameters**:

- `matches` (list[tuple[Path, frontmatter.Post]]): Query results
- `format_type` (QueryOutputStyle): Output format (PATH, TITLE, TABLE, JSON)
- `key` (str): Queried frontmatter key

**Output Formats**:

- `PATH`: File paths only
- `TITLE`: File paths with titles
- `TABLE`: Rich table with all frontmatter
- `JSON`: Structured JSON output

#### `_display_metadata_key(post: frontmatter.Post, key: str) -> None`

Display specific metadata key value.

**Parameters**:

- `post` (frontmatter.Post): Frontmatter object
- `key` (str): Key to display

**Raises**: `KeyError` if key not found in frontmatter

#### `_list_all_metadata(post: frontmatter.Post) -> None`

Display all metadata keys and values.

**Parameters**:

- `post` (frontmatter.Post): Frontmatter object

**Behavior**:

- Shows error message if no metadata found
- Lists all key-value pairs from frontmatter

### Metadata Operations

#### `_update_metadata_key(post: frontmatter.Post, filename: Path, key: str, value: str, verbose: bool) -> None`

Update frontmatter metadata key with new value.

**Parameters**:

- `post` (frontmatter.Post): Frontmatter object to update
- `filename` (Path): Path to file being updated
- `key` (str): Metadata key to set
- `value` (str): Value to set
- `verbose` (bool): Whether to print confirmation

**Side Effects**:

- Modifies the frontmatter Post object
- Adds/updates 'modified' timestamp
- Writes changes back to file
- Prints confirmation if verbose

### Template Functions

#### `_get_journal_template_vars(date: datetime) -> dict[str, str | int]`

Get template variables for journal path formatting.

**Parameters**:

- `date` (datetime): Date for template variables

**Returns**: Dictionary with template variables:

- `year` (int): Full year
- `month` (int): Month number
- `day` (int): Day number
- `month_name` (str): Full month name
- `month_abbr` (str): Abbreviated month name
- `weekday` (str): Full weekday name
- `weekday_abbr` (str): Abbreviated weekday name

### System Information

#### `_get_vault_info(state: "State") -> dict[str, Any]`

Get comprehensive vault information as structured data.

**Parameters**:

- `state` (State): Application state with vault configuration

**Returns**: Dictionary with vault information:

- `exists` (bool): Whether vault exists
- `vault_path` (str): Path to vault
- `total_files` (int): Total file count
- `total_directories` (int): Total directory count
- `markdown_files` (int): Count of `.md` files
- `blacklist` (list[str]): Active blacklist patterns
- `editor` (Path): Configured editor
- `journal_path` (str): Current journal path
- `journal_template` (str): Journal template pattern
- `verbose` (bool): Verbose mode setting
- `version` (str): Application version

**Error Handling**: Returns error information if vault doesn't exist

## Constants and Enums

### Exit Codes

| Code | Constant | Description                                                  |
| ---- | -------- | ------------------------------------------------------------ |
| 0    | -        | Success                                                      |
| 1    | -        | General application error                                    |
| 2    | -        | Command line usage error (Click/Typer)                       |
| 11   | -        | File resolution error (ObsidianFileError)                    |
| 12   | -        | Configuration/general file error (ObsidianFileError default) |

### Default Values

| Setting          | Default Value                                              | Description                           |
| ---------------- | ---------------------------------------------------------- | ------------------------------------- |
| Editor           | `vi`                                                       | Default text editor                   |
| Blacklist        | `["Assets/", ".obsidian/", ".git/"]`                       | Default ignored directories           |
| Ident Key        | `uid`                                                      | Default identifier key in frontmatter |
| Journal Template | `Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}` | Default journal path pattern          |

## Error Handling Patterns

### Exception Hierarchy

```
BaseException
 └── Exception
     └── click.ClickException
         └── click.FileError
             └── ObsidianFileError
```

### Common Error Scenarios

1. **File Not Found in Vault** (exit_code=11)
   - Raised by: `_resolve_path()`
   - Trigger: File doesn't exist in vault

2. **Configuration File Missing** (exit_code=12)
   - Raised by: `Configuration._load_toml_config()`
   - Trigger: Config file not found

3. **Configuration Parse Error** (exit_code=2)
   - Raised by: `Configuration._load_toml_config()`
   - Trigger: Invalid TOML syntax

4. **Missing Frontmatter Key** (KeyError)
   - Raised by: `_display_metadata_key()`
   - Trigger: Requested key not in frontmatter

## Type Definitions

### Common Type Aliases

```python
from typing import Union, Optional, Tuple, Any
from pathlib import Path

# Path types
PathLike = Union[str, Path]

# Configuration loading result
ConfigResult = Tuple[Union[Path, None], Configuration]

# Frontmatter query results
QueryMatches = list[tuple[Path, frontmatter.Post]]

# Vault info structure
VaultInfo = dict[str, Any]
```

## Dependencies

### External Dependencies

- `click`: Command-line interface framework (FileError base class)
- `typer`: Modern CLI framework built on Click
- `frontmatter`: YAML frontmatter parsing
- `rich`: Terminal formatting and display
- `tomllib`: TOML configuration parsing (Python 3.11+)

### Internal Dependencies

- **Modular design**: Functionality separated into specialized modules
- **Clean imports**: Configuration and exceptions in separate modules prevent circular dependencies
- **TYPE_CHECKING**: Used to avoid runtime import cycles for type hints
- **State object**: Passed between functions for configuration access
