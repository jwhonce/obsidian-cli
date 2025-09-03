# Obsidian CLI

A command-line interface for interacting with Obsidian vaults with AI assistant integration via Model Context Protocol (MCP).

## Features

- **Note Management**: Create, edit, and delete notes with frontmatter support
- **Vault Operations**: List, search, and query notes across your vault
- **Journal Support**: Open daily notes with customizable templates
- **UID Management**: Add unique identifiers to notes for better organization
- **MCP Server**: AI assistant integration via Model Context Protocol
- **Flexible Configuration**: TOML-based configuration with sensible defaults

## Installation

```bash
pip install obsidian-cli
```

## Quick Start

If no configuration file is found, obsidian-cli will use default settings. You'll need to specify the vault path:

```bash
# List all notes in a vault
obsidian-cli --vault /path/to/vault ls

# Create a new note
obsidian-cli --vault /path/to/vault new "My New Note"

# Search for notes containing "python"
obsidian-cli --vault /path/to/vault query title --contains python
```

## Configuration

Create a configuration file at one of these locations:

- `obsidian-cli.toml` (current directory)
- `~/.config/obsidian-cli/config.toml`

Example configuration:

```toml
vault = "/path/to/your/obsidian/vault"
editor = "code"
ident_key = "uid"
ignored_directories = ["Assets/", ".obsidian/", ".git/"]
journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
verbose = false
```

## Commands

### Core Commands

- `add-uid` - Add unique identifiers to notes
- `edit` - Open a note in your configured editor
- `journal` - Open today's journal entry
- `ls` - List all notes in the vault
- `new` - Create a new note with optional frontmatter
- `query` - Search and filter notes by frontmatter properties
- `rm` - Remove notes from the vault
- `serve` - Start MCP server for AI assistant integration
- `version` - Display version information

### Examples

```bash
# Create a note with frontmatter
obsidian-cli new "Project Ideas" --tags work,brainstorm --status active

# Query notes by status
obsidian-cli query status --value active

# Group query results by category
obsidian-cli query status --exists --group-by category

# Open journal with custom date
obsidian-cli journal --date 2025-01-15

# Start MCP server for AI integration
obsidian-cli serve
```

## Journal Templates

The journal template supports these variables:

- `{year}` - Four-digit year (e.g., 2025)
- `{month}` - Month number (1-12)
- `{month:02d}` - Zero-padded month (01-12)
- `{day}` - Day number (1-31)
- `{day:02d}` - Zero-padded day (01-31)
- `{month_name}` - Full month name (e.g., January)
- `{month_abbr}` - Abbreviated month (e.g., Jan)
- `{weekday}` - Full weekday name (e.g., Monday)
- `{weekday_abbr}` - Abbreviated weekday (e.g., Mon)

## MCP Integration

The `serve` command starts a Model Context Protocol server that exposes vault operations to AI assistants:

- `create_note` - Create new notes with frontmatter
- `find_notes` - Search notes by various criteria
- `get_note_content` - Retrieve note content and metadata
- `get_vault_info` - Get vault statistics and information

## License

Apache 2.0 License
