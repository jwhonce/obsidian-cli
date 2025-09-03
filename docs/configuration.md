# Configuration Guide

This document explains how to configure obsidian-cli for your workflow.

## Configuration File Locations

obsidian-cli searches for configuration files in this order:

1. Path specified with `--config` option
2. `obsidian-cli.toml` in the current directory
3. `~/.config/obsidian-cli/config.toml` (or `$XDG_CONFIG_HOME/obsidian-cli/config.toml`)

If no configuration file is found, obsidian-cli uses default settings. In this case, you must specify the vault path using the `--vault` option.

## Configuration Format

obsidian-cli uses TOML configuration files. Here's a complete example:

```toml
# Path to your Obsidian vault
vault = "/path/to/your/obsidian/vault"

# Editor command for opening files
editor = "code"

# Key used for unique identifiers in frontmatter
ident_key = "uid"

# Directories to ignore during queries and operations
ignored_directories = ["Assets/", ".obsidian/", ".git/", "Templates/"]

# Template for journal file paths
journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"

# Enable verbose output by default
verbose = false
```

## Configuration Options

### vault

**Type:** String (path)
**Required:** Yes (either in config or via `--vault` option)
**Description:** Path to your Obsidian vault directory.

```toml
vault = "/Users/username/Documents/MyVault"
```

### editor

**Type:** String
**Default:** `"vi"`
**Description:** Command to use for opening files with the `edit` command.

```toml
# VS Code
editor = "code"

# Vim
editor = "vim"

# Neovim
editor = "nvim"

# Emacs
editor = "emacs"

# System default
editor = "open"  # macOS
editor = "xdg-open"  # Linux
```

### ident_key

**Type:** String
**Default:** `"uid"`
**Description:** Frontmatter key used for unique identifiers by the `add-uid` command.

```toml
ident_key = "id"
# or
ident_key = "uuid"
# or
ident_key = "note_id"
```

### ignored_directories

**Type:** Array of strings
**Default:** `["Assets/", ".obsidian/", ".git/"]`
**Description:** Directories to exclude from `query`, `ls`, and other vault operations.

```toml
ignored_directories = [
    "Assets/",
    ".obsidian/",
    ".git/",
    "Templates/",
    "Archive/",
    "_drafts/"
]
```

### journal_template

**Type:** String
**Default:** `"Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"`
**Description:** Template for generating journal file paths. Supports various date formatting variables.

#### Template Variables

- `{year}` - Four-digit year (e.g., 2025)
- `{month}` - Month number (1-12)
- `{month:02d}` - Zero-padded month (01-12)
- `{day}` - Day number (1-31)
- `{day:02d}` - Zero-padded day (01-31)
- `{month_name}` - Full month name (e.g., January)
- `{month_abbr}` - Abbreviated month (e.g., Jan)
- `{weekday}` - Full weekday name (e.g., Monday)
- `{weekday_abbr}` - Abbreviated weekday (e.g., Mon)

#### Template Examples

```toml
# Default format: Calendar/2025/01/2025-01-15.md
journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"

# Simple daily notes: Daily/2025-01-15.md
journal_template = "Daily/{year}-{month:02d}-{day:02d}"

# Monthly organization: Journal/2025/January/15.md
journal_template = "Journal/{year}/{month_name}/{day}"

# Weekly organization: Weekly/2025/Week-03/Monday.md
journal_template = "Weekly/{year}/Week-{week:02d}/{weekday}"

# Flat structure with weekday: Journal/Monday-2025-01-15.md
journal_template = "Journal/{weekday}-{year}-{month:02d}-{day:02d}"
```

### verbose

**Type:** Boolean
**Default:** `false`
**Description:** Enable verbose output by default.

```toml
verbose = true
```

## Environment Variables

You can override configuration values using environment variables:

- `OBSIDIAN_VAULT` - Override vault path
- `OBSIDIAN_EDITOR` - Override editor command
- `XDG_CONFIG_HOME` - Change config directory location (Linux/macOS)

```bash
# Use different vault for this session
export OBSIDIAN_VAULT="/path/to/different/vault"
obsidian-cli ls

# Use different editor
export OBSIDIAN_EDITOR="vim"
obsidian-cli edit "My Note"
```

## Command-Line Overrides

Any configuration option can be overridden via command-line flags:

```bash
# Override vault setting
obsidian-cli --vault /different/vault ls

# Enable verbose mode for one command
obsidian-cli --verbose query status --exists

# Use different config file
obsidian-cli --config /path/to/custom.toml ls
```

## Configuration Validation

obsidian-cli validates configuration on startup:

- **vault**: Must be a valid directory path
- **editor**: Must be a valid command (checked when used)
- **ignored_directories**: Must be an array of strings
- **journal_template**: Must be a valid format string

Invalid configurations will show clear error messages with suggestions for fixes.

## Examples by Use Case

### Academic Research

```toml
vault = "/Users/researcher/Research"
editor = "obsidian"  # Open in Obsidian app
ident_key = "paper_id"
ignored_directories = ["Assets/", ".obsidian/", ".git/", "PDFs/", "Data/"]
journal_template = "Daily/{year}-{month:02d}-{day:02d}"
verbose = true
```

### Software Development

```toml
vault = "/Users/dev/notes"
editor = "code"
ident_key = "note_id"
ignored_directories = ["Assets/", ".obsidian/", ".git/", "attachments/"]
journal_template = "Journal/{year}/Week-{week:02d}/{weekday}"
verbose = false
```

### Personal Knowledge Management

```toml
vault = "/Users/person/SecondBrain"
editor = "obsidian"
ident_key = "uid"
ignored_directories = ["Assets/", ".obsidian/", ".git/", "Templates/", "Archive/"]
journal_template = "Calendar/{year}/{month_name}/{day:02d}-{weekday_abbr}"
verbose = false
```

## Troubleshooting

### Common Issues

1. **"No vault specified"**

   - Add `vault` to your config file or use `--vault` option

2. **"Configuration file not found"**

   - obsidian-cli will use defaults; this is normal if you haven't created a config file

3. **"Invalid journal template"**

   - Check that your template uses valid variable names and format specifiers

4. **"Editor command not found"**
   - Ensure your editor is installed and in your PATH

### Debug Configuration

Use the verbose flag to see which configuration file is being used:

```bash
obsidian-cli --verbose ls
```

This will show:

- Which configuration file was loaded (if any)
- Final configuration values being used
- Any configuration validation warnings
