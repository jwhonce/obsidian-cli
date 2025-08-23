# Command Reference

This document provides detailed information on all available commands in obsidian-cli.

## Global Options

These options can be used with any command:

- `--config PATH`: Path to the configuration file
- `--vault PATH`: Path to the Obsidian vault
- `--editor PATH`: Editor to use for editing journal entries (default: 'vi')
- `--verbose, -v`: Enable verbose output
- `--version`: Show version and exit
- `--help`: Show help message and exit

## Commands

### add-uid

Add a unique ID to a page's frontmatter if it doesn't already have one.

```bash
obsidian-cli add-uid PAGE_OR_FILE [--force]
```

Options:

- `--force`: Replace existing UID if one exists

### cat

Display the contents of a file in the Obsidian Vault.

```bash
obsidian-cli cat PAGE_OR_FILE [--show-frontmatter]
```

Options:

- `--show-frontmatter`: Show the YAML frontmatter at the beginning of the file

### edit

Edit any file in the Obsidian Vault with the configured editor.

```bash
obsidian-cli edit PAGE_OR_FILE
```

### find

Find files in the vault that match the given page name.

```bash
obsidian-cli find PAGE_NAME [--exact]
```

Options:

- `--exact, -e`: Require exact match on page name

### info

Display information about the current Obsidian Vault and configuration.

```bash
obsidian-cli info
```

### journal

Open today's journal entry in the Obsidian Vault. The journal file must already exist.

```bash
obsidian-cli journal
```

The journal command uses a configurable template to determine the path to today's journal file. By default, it looks for files matching the pattern: `Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}.md`

If the journal file doesn't exist, the command will exit with an error. Use the `new` command to create journal files first:

```bash
# Create today's journal file first
obsidian-cli new "Calendar/2025/08/2025-08-20"

# Then open it with the journal command
obsidian-cli journal
```

The journal template can be customized in the configuration file using the `journal_template` setting.

### meta / frontmatter

View or update frontmatter metadata in a file. These commands are aliases of each other.

```bash
obsidian-cli meta PAGE_OR_FILE [KEY] [VALUE]
obsidian-cli frontmatter PAGE_OR_FILE [KEY] [VALUE]
```

Behavior:

- If neither KEY nor VALUE is provided, lists all frontmatter metadata
- If only KEY is provided, displays the current value of that key
- If both KEY and VALUE are provided, updates the key with the new value

### new

Create a new file in the Obsidian Vault.

```bash
obsidian-cli new PAGE_OR_FILE [--force]
```

Options:

- `--force, -f`: Overwrite existing file if it exists

### query

Query frontmatter across all files in the vault. Files in configured ignored directories are automatically excluded from the search.

```bash
obsidian-cli query KEY [OPTIONS]
```

Options:

- `--value VALUE`: Find files where the key exactly matches this value
- `--contains STRING`: Find files where the key's value contains this substring
- `--exists`: Find files where the key exists (regardless of value)
- `--missing`: Find files where the key does not exist
- `--format, -f FORMAT`: Output format (path, title, full, count, json)
- `--count, -c`: Only show count of matching files

**Note:** The query command respects the `ignored_directories` configuration setting, automatically excluding files from specified directory patterns (e.g., archives, assets, system directories).

### rm

Remove a file from the Obsidian Vault.

```bash
obsidian-cli rm PAGE_OR_FILE [--force]
```

Options:

- `--force, -f`: Skip confirmation prompt and delete immediately
