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

Add unique identifiers to notes that don't already have them.

```bash
obsidian-cli add-uid [OPTIONS] [PAGES]...
```

**Options:**

- `--force, -f` - Skip confirmation prompt and add UIDs to all specified notes
- `--dry-run` - Show what would be done without making changes

**Examples:**

```bash
# Add UIDs to all notes
obsidian-cli add-uid

# Add UID to specific note
obsidian-cli add-uid "My Note.md"

# Force add UIDs without confirmation
obsidian-cli add-uid --force
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

List all notes in the vault.

```bash
obsidian-cli ls [OPTIONS]
```

**Options:**

- `--format, -f [path|title|full]` - Output format (default: path)

**Examples:**

```bash
# List all notes (paths only)
obsidian-cli ls

# List with titles
obsidian-cli ls --format title

# List with full metadata
obsidian-cli ls --format full
```

### new

Create a new note with optional frontmatter.

```bash
obsidian-cli new [OPTIONS] TITLE
```

**Arguments:**

- `TITLE` - Title of the new note

**Options:**

- `--force, -f` - Overwrite existing file if it exists
- `--tags TEXT` - Comma-separated list of tags
- `--status TEXT` - Status value for the note
- `--category TEXT` - Category for the note
- `--template PATH` - Path to template file to use

**Examples:**

```bash
# Create a simple note
obsidian-cli new "My New Note"

# Create with frontmatter
obsidian-cli new "Project Plan" --tags project,planning --status active

# Create from template
obsidian-cli new "Meeting Notes" --template templates/meeting.md
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
- `--format, -f [path|title|full|count|json]` - Output format styles (default: path)
- `--count, -c` - Only show count of matching pages
- `--group-by, -g TEXT` - Group results by the specified frontmatter property

**Examples:**

```bash
# Find notes with specific status
obsidian-cli query status --value active

# Find notes containing text in title
obsidian-cli query title --contains project

# Count notes by status
obsidian-cli query status --exists --count

# Group notes by category
obsidian-cli query status --exists --group-by category

# JSON output for scripting
obsidian-cli query tags --exists --format json
```

### rm

Remove notes from the vault.

```bash
obsidian-cli rm [OPTIONS] PAGES...
```

**Arguments:**

- `PAGES` - Note titles or file paths to remove

**Options:**

- `--force, -f` - Skip confirmation prompt

**Examples:**

```bash
# Remove a note (with confirmation)
obsidian-cli rm "Old Note"

# Remove multiple notes
obsidian-cli rm "Note 1" "Note 2" "Note 3"

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

### version

Display version information.

```bash
obsidian-cli version
```

**Examples:**

```bash
# Show version
obsidian-cli version
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
