# Command Reference

This document provides detailed information about all available commands in obsidian-cli.

## Global Options

All commands support these global options:

- `--vault PATH` - Specify the vault directory (required if not in config)
- `--config PATH` - Specify configuration file path
- `--verbose` - Enable verbose output
- `--help` - Show help information

## Commands

### add-uid

Add a unique ID to a page's frontmatter if it doesn't already have one.

```bash
obsidian-cli add-uid [OPTIONS] PAGE_OR_PATH
```

**Arguments:**

- `PAGE_OR_PATH` - Obsidian page name or path to file

**Options:**

- `--force` - If set, overwrite existing uid

**Examples:**

```bash
# Add UID to a specific note
obsidian-cli add-uid "My Note"

# Force overwrite existing UID
obsidian-cli add-uid --force "My Note"
```

### cat

Display the contents of a file in the Obsidian Vault.

```bash
obsidian-cli cat [OPTIONS] PAGE_OR_PATH
```

**Arguments:**

- `PAGE_OR_PATH` - Obsidian page name or path to file

**Options:**

- `--show-frontmatter` - If set, show frontmatter in addition to file content

**Examples:**

```bash
# Display note content only
obsidian-cli cat "My Note"

# Display note with frontmatter
obsidian-cli cat --show-frontmatter "My Note"
```

### edit

Open a note in your configured editor.

```bash
obsidian-cli edit [OPTIONS] PAGE_OR_PATH
```

**Arguments:**

- `PAGE_OR_PATH` - Note title or file path to edit

**Examples:**

```bash
# Edit by title
obsidian-cli edit "My Note"

# Edit by path
obsidian-cli edit "Projects/idea.md"
```

### find

Find files in the vault that match the given page name.

```bash
obsidian-cli find [OPTIONS] PAGE_NAME
```

**Arguments:**

- `PAGE_NAME` - Obsidian page to use in search

**Options:**

- `--exact/-e` - Require exact match on page name

**Examples:**

```bash
# Find notes with fuzzy matching
obsidian-cli find "meeting"

# Find notes with exact matching
obsidian-cli find --exact "Daily Meeting Notes"
```

### info

Display information about the current Obsidian Vault and configuration.

```bash
obsidian-cli info
```

**Examples:**

```bash
# Show vault information
obsidian-cli info
```

### journal

Open today's journal entry or a journal for a specific date.

```bash
obsidian-cli journal [OPTIONS]
```

**Options:**

- `--date, -d TEXT` - Date for journal entry (YYYY-MM-DD format). Defaults to today.

**Examples:**

```bash
# Open today's journal
obsidian-cli journal

# Open journal for specific date
obsidian-cli journal --date 2025-01-15
```

### ls

List all markdown files in the vault.

```bash
obsidian-cli ls
```

**Examples:**

```bash
# List all notes (paths only)
obsidian-cli ls
```

### meta

View or update frontmatter metadata in a file.

```bash
obsidian-cli meta [OPTIONS] PAGE_OR_PATH
```

**Arguments:**

- `PAGE_OR_PATH` - Obsidian page name or path to file

**Options:**

- `--key TEXT` - Key of the frontmatter metadata to view or update
- `--value TEXT` - New metadata for given key

**Examples:**

```bash
# List all metadata for a note
obsidian-cli meta "My Note"

# View specific metadata key
obsidian-cli meta "My Note" --key status

# Update metadata
obsidian-cli meta "My Note" --key status --value completed
```

### new

Create a new file in the Obsidian Vault.

```bash
obsidian-cli new [OPTIONS] PAGE_OR_PATH
```

**Arguments:**

- `PAGE_OR_PATH` - Obsidian page name or path to file

**Options:**

- `--force` - Overwrite existing file with new contents

**Examples:**

```bash
# Create a simple note
obsidian-cli new "My New Note"

# Overwrite existing file
obsidian-cli new --force "Existing Note"

# Create note with content from stdin
echo "Note content" | obsidian-cli new "Note from Stdin"
```

### query

Search and filter notes by frontmatter properties.

```bash
obsidian-cli query [OPTIONS] KEY
```

**Arguments:**

- `KEY` - Frontmatter key to query across vault

**Options:**

- `--value TEXT` - Find pages where the key's metadata exactly matches this string
- `--contains TEXT` - Find pages where the key's metadata contains this substring
- `--exists` - Find pages where the key exists
- `--missing` - Find pages where the key is missing
- `--style, -s [json|path|table|title]` - Output format style (default: path)
- `--count, -c` - Only show count of matching pages

**Examples:**

```bash
# Find notes with specific status
obsidian-cli query status --value active

# Find notes containing text in title
obsidian-cli query title --contains project

# Count notes by status
obsidian-cli query status --exists --count

# Table format output
obsidian-cli query status --exists --style table

# JSON output for scripting
obsidian-cli query tags --exists --style json
```

### rm

Remove notes from the vault.

```bash
obsidian-cli rm [OPTIONS] PAGE_OR_PATH
```

**Arguments:**

- `PAGE_OR_PATH` - Note title or file path to remove

**Options:**

- `--force, -f` - Skip confirmation prompt

**Examples:**

```bash
# Remove a note (with confirmation)
obsidian-cli rm "Old Note"

# Force removal without confirmation
obsidian-cli rm --force "Temporary Note"
```

### serve

Start MCP server for AI assistant integration.

```bash
obsidian-cli serve [OPTIONS]
```

The server exposes these MCP tools:

- `create_note` - Create new notes with frontmatter
- `find_notes` - Search notes by various criteria
- `get_note_content` - Retrieve note content and metadata
- `get_vault_info` - Get vault statistics and information

**Examples:**

```bash
# Start MCP server
obsidian-cli serve

# Use with AI assistant (Claude Desktop example)
# Add to Claude Desktop config:
# {
#   "mcpServers": {
#     "obsidian": {
#       "command": "obsidian-cli",
#       "args": ["serve"]
#     }
#   }
# }
```

## Configuration Integration

All commands respect the configuration file settings. You can override any configuration value using command-line options:

```bash
# Override vault setting
obsidian-cli --vault /different/vault ls

# Enable verbose mode
obsidian-cli --verbose query status --exists
```

## Error Handling

Commands provide clear error messages and appropriate exit codes:

- `0` - Success
- `1` - General error (invalid arguments, configuration issues)
- `2` - File not found or validation error

Use `--verbose` flag for detailed error information and debugging.
