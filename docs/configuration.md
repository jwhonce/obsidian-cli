# Configuration Guide

obsidian-cli offers multiple ways to configure your settings, providing flexibility for different workflows and environments.

## Configuration Options

The following options can be configured:

| Option                | Description                                        | Default                    |
| --------------------- | -------------------------------------------------- | -------------------------- |
| `vault`               | Path to your Obsidian vault                        | None                       |
| `editor`              | Editor to use for opening files                    | 'vi'                       |
| `verbose`             | Whether to display verbose output                  | False                      |
| `ident_key`           | Frontmatter key for unique identifiers             | 'uid'                      |
| `ignored_directories` | List of directory patterns to exclude from queries | See default patterns below |
| `journal_template`    | Template for journal file paths                    | See template section below |

## Configuration Methods (in order of precedence)

1. Command line arguments
2. Environment variables
3. Configuration file
4. Default values

## Command Line Arguments

Command line arguments take precedence over all other configuration methods:

```bash
obsidian-cli --vault ~/Documents/MyVault --editor code info
```

## Environment Variables

If command line arguments are not provided, environment variables are used:

- `OBSIDIAN_VAULT`: Path to your Obsidian vault
- `EDITOR`: Editor to use for opening files

```bash
# Set for current session
export OBSIDIAN_VAULT=~/Documents/MyVault
export EDITOR=code

# Or inline for a single command
OBSIDIAN_VAULT=~/Documents/MyVault obsidian-cli info
```

## Configuration File

If neither command line arguments nor environment variables are set, obsidian-cli looks for configuration in TOML files.

Files are checked in the following order:

1. `./obsidian-cli.toml` (current working directory)
2. `~/.config/obsidian-cli/config.toml` (user config directory)

You can also specify a custom configuration file:

```bash
obsidian-cli --config ~/my-custom-config.toml info
```

### Example Configuration File

```toml
# obsidian-cli.toml
vault = "~/Documents/ObsidianVault"
editor = "vim"
verbose = false
ident_key = "uid"
ignored_directories = [
  ".obsidian/",
  ".git/",
  "Templates/",
  "Attachments/"
]
journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
```

### Configuration Details

#### ignored_directories

The `ignored_directories` option allows you to specify directory patterns that should be excluded from query operations. This is useful for:

- Excluding archived or historical content (`Content/Archives/`)
- Skipping asset directories (`Assets/`, `Attachments/`)
- Avoiding system directories (`.obsidian/`, `.git/`)
- Filtering out template directories (`Templates/`)

Patterns are matched against the beginning of relative file paths within your vault. For example, if you have a file at `Content/Archives/old-note.md`, it will be excluded because it starts with `Content/Archives/`.

#### ident_key

The `ident_key` option specifies which frontmatter key to use for unique identifiers when creating new files or adding UIDs to existing files. This allows customization of the identifier field name to match your vault's conventions.

For example, if you prefer to use `id` instead of the default `uid`:

```toml
ident_key = "id"
```

#### journal_template

The `journal_template` option specifies the path template for journal files. The template supports the following variables:

- `{year}`: 4-digit year (e.g., 2025)
- `{month}`: Month number (1-12)
- `{month:02d}`: Zero-padded month (01-12)
- `{day}`: Day number (1-31)
- `{day:02d}`: Zero-padded day (01-31)
- `{month_name}`: Full month name (e.g., January)
- `{month_abbr}`: Abbreviated month (e.g., Jan)
- `{weekday}`: Full weekday name (e.g., Monday)
- `{weekday_abbr}`: Abbreviated weekday (e.g., Mon)

Example templates:

```toml
# Default template
journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"

# Alternative formats
journal_template = "Daily Notes/{year}-{month:02d}-{day:02d} {weekday}"
journal_template = "Journal/{month_name} {year}/{day:02d} - {weekday}"
journal_template = "Notes/{year}/{month_abbr}/{day:02d}"
```

**Default ignored directories:**

- `.obsidian/`
- `.git/`

## Default Values

If no configuration is found, the following defaults are used:

- `editor`: 'vi'
- `verbose`: False
- `ident_key`: 'uid'
- `ignored_directories`: `[".obsidian/", ".git/"]`
- `journal_template`: 'Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}'

Note: `vault` has no default and must be specified through one of the above methods.
