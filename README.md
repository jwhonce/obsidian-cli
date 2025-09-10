# Obsidian CLI

A command-line interface for interacting with Obsidian vaults with AI assistant integration via Model Context Protocol (MCP).

[![Test Coverage](https://img.shields.io/badge/coverage-78%25-brightgreen.svg)](https://github.com/jhonce/obsidian-cli)
[![Version](https://img.shields.io/badge/version-0.1.16-blue.svg)](https://github.com/jhonce/obsidian-cli)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## Features

- **Note Management**: Create, edit, and delete notes with frontmatter support
- **Vault Operations**: List, search, and query notes across your vault
- **Journal Support**: Open daily notes with customizable templates
- **UID Management**: Add unique identifiers to notes for better organization
- **MCP Server**: AI assistant integration via Model Context Protocol
- **Flexible Configuration**: TOML-based configuration with sensible defaults
- **Comprehensive Testing**: 78% test coverage with 117 tests ensuring reliability

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
editor = "vi"
ident_key = "uid"
blacklist = ["Assets/", ".obsidian/", ".git/"]
journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
vault = "~/path/to/vault"
verbose = false
```

## Commands

### Core Commands

- `add-uid` - Add unique identifiers to notes
- `cat` - Display the contents of a file
- `edit` - Open a note in your configured editor
- `find` - Find files by name or title with exact/fuzzy matching
- `info` - Display vault and configuration information
- `journal` - Open today's journal entry
- `ls` - List all notes in the vault
- `meta` - View or update frontmatter metadata
- `new` - Create a new note with optional frontmatter
- `query` - Search and filter notes by frontmatter properties
- `rm` - Remove notes from the vault
- `serve` - Start MCP server for AI assistant integration

### Command: ls

List markdown files in the vault.

- **Description**: Prints the relative paths of all `*.md` files under the configured vault.
- **Blacklist**: Respects blacklisted directory prefixes (e.g., `Assets/`, `.obsidian/`, `.git/`).

  - Configure via any of:

    - CLI: `--blacklist "Assets/:.obsidian/:.git/"`
    - Env: `OBSIDIAN_BLACKLIST="Assets/:.obsidian/:.git/"`
    - Config: `blacklist = ["Assets/", ".obsidian/", ".git/"]` in obsidian-cli.toml

- **Output**: One path per line, relative to the vault root.
- **Requires**: `--vault` to point to your Obsidian vault directory (or set via config/env).

Usage:

- Basic listing

  - `obsidian-cli --vault /path/to/vault ls`

- With custom blacklist

  - `obsidian-cli --vault /path/to/vault --blacklist "Templates/:Archive/" ls`

Notes:

- Matching is prefix-based and case-sensitive (e.g., `Assets/` matches `Assets/images.png`, but not `assets/`).
- Only Markdown files (`*.md`) are listed.

See also: [docs/commands/ls.md](docs/commands/ls.md)

### Examples

```bash
# Create a new note
obsidian-cli new "Project Ideas"

# Query notes by status
obsidian-cli query status --value active

# Find notes containing specific text
obsidian-cli find "meeting notes" --exact

# Display vault information
obsidian-cli info

# View metadata of a note
obsidian-cli meta "Project Ideas"

# Update metadata
obsidian-cli meta "Project Ideas" --key status --value completed

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

The `serve` command starts a Model Context Protocol server that exposes vault operations to AI assistants. This enables seamless integration with AI tools like Claude Desktop and other MCP-compatible systems.

### Available MCP Tools

- `create_note` - Create new notes with frontmatter
- `find_notes` - Search notes by various criteria
- `get_note_content` - Retrieve note content and metadata
- `get_vault_info` - Get vault statistics and information

### Usage with AI Assistants

```bash
# Start the MCP server
obsidian-cli --vault /path/to/vault serve

# The server runs until interrupted (Ctrl+C)
# AI assistants can now interact with your vault through MCP protocol
```

For detailed MCP setup instructions, see [docs/mcp-integration.md](docs/mcp-integration.md).

## License

Apache 2.0 License
