"""
Obsidian CLI - Command-line interface for interacting with Obsidian vaults

This module provides a comprehensive set of command-line tools to interact with
Obsidian vaults, making it easier to perform common operations from the terminal.
It facilitates tasks such as creating notes, editing content, querying metadata,
and managing files.

Key features:
- Create and edit markdown files with proper frontmatter
- Query files based on frontmatter metadata with configurable directory filtering
- View and update metadata in existing files
- Add unique IDs to files
- Access existing journal entries with configurable templates
- Find files by name or title with exact/fuzzy matching
- Display information about the vault
- Configuration via obsidian-cli.toml file and environment variables
- Force flag for commands that modify files

The CLI uses Typer for command-line interface management and provides a clean,
intuitive interface with extensive help documentation.

Example usage:
    $ obsidian-cli --vault /path/to/vault info
    $ obsidian-cli --vault /path/to/vault new "My New Note"
    $ obsidian-cli --vault /path/to/vault query tags --exists
    $ obsidian-cli --vault /path/to/vault --ignored-directories "Archives/:Temp/" \\
        query tags --exists
    $ obsidian-cli --vault /path/to/vault find "Daily Note" --exact
    $ obsidian-cli --vault /path/to/vault journal
    $ obsidian-cli --vault /path/to/vault rm --force unwanted-note
    $ OBSIDIAN_BLACKLIST="Templates/:Archive/" obsidian-cli --vault /path/to/vault \\
        query tags --exists

Commands:
    add-uid     Add a unique ID to a page's frontmatter
    cat         Display the contents of a file
    edit        Edit any file with the configured editor
    find        Find files by name or title with exact/fuzzy matching
    info        Display vault and configuration information
    journal     Open today's journal entry (must exist)
    meta        View or update frontmatter metadata
    new         Create a new file in the vault
    query       Query frontmatter across all files
    rm          Remove a file from the vault
    serve       Start an MCP (Model Context Protocol) server

Configuration:
    The tool can be configured using an obsidian-cli.toml file which should contain:

    ```toml
    vault = "~/path/to/vault"
    editor = "vim"
    verbose = false
    ident_key = "uid"
    ignored_directories = ["Assets/", ".obsidian/", ".git/"]
    journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
    ```

    Configuration can be placed in:
    - ./obsidian-cli.toml (current directory)
    - ~/.config/obsidian-cli/config.toml (user's config directory)

    Environment Variables:
    - OBSIDIAN_VAULT: Path to the Obsidian vault
    - EDITOR: Editor to use for editing files
    - OBSIDIAN_BLACKLIST: Colon-separated list of directory patterns to ignore

    Journal Template Variables:
    - {year}: 4-digit year (e.g., 2025)
    - {month}: Month number (1-12)
    - {month:02d}: Zero-padded month (01-12)
    - {day}: Day number (1-31)
    - {day:02d}: Zero-padded day (01-31)
    - {month_name}: Full month name (e.g., January)
    - {month_abbr}: Abbreviated month (e.g., Jan)
    - {weekday}: Full weekday name (e.g., Monday)
    - {weekday_abbr}: Abbreviated weekday (e.g., Mon)

Author: Jhon Honce / Copilot enablement
Version: 0.1.11
License: Apache License 2.0
"""

import os
import sys
import tomllib
from asyncio import CancelledError
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shutil import get_terminal_size
from typing import Annotated, Optional

import frontmatter
import typer
from typing_extensions import Doc

# Get version from package metadata or fallback
try:
    import importlib.metadata

    __version__ = importlib.metadata.version("obsidian-cli")
except Exception:
    # Fallback for development mode
    try:
        from . import __version__
    except Exception:
        __version__ = "0.1.11"  # Fallback version

# Initialize Typer app
cli = typer.Typer(
    add_completion=False,
    help="Command-line interface for interacting with Obsidian.",
    context_settings={"max_content_width": get_terminal_size().columns},
)


def _version(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"obsidian-cli v{__version__}")
        raise typer.Exit()


@dataclass(frozen=True)
class Configuration:
    """Record configuration for obsidian-cli application.

    Default paths include:
    - ./obsidian-cli.toml (current directory)
    - ~/.config/obsidian-cli/config.toml (user's config directory)
    """

    editor: Path = Path("vi")
    ident_key: str = "uid"
    ignored_directories: list[str] = ("Assets/", ".obsidian/", ".git/")
    journal_template: str = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
    vault: Path = None
    verbose: bool = False

    @classmethod
    def from_file(cls, path: Optional[Path], verbose: bool = False) -> "Configuration":
        """Load configuration from a TOML file."""
        config_data = None

        if path:
            config_data = Configuration._load_toml_config(path, verbose)
        else:
            for config_path in ["./obsidian-cli.toml", "~/.config/obsidian-cli/config.toml"]:
                expanded_path = Path(os.path.expanduser(config_path))
                if expanded_path.exists():
                    config_data = Configuration._load_toml_config(expanded_path, verbose)
                    break

        if config_data is None:
            raise FileNotFoundError("No configuration file found.")

        return cls(
            editor=Path(config_data.get("editor", Configuration.editor)),
            ident_key=config_data.get("ident_key", Configuration.ident_key),
            ignored_directories=config_data.get(
                "ignored_directories", Configuration.ignored_directories
            ),
            journal_template=config_data.get("journal_template", Configuration.journal_template),
            vault=Path(config_data.get("vault", None)),
            verbose=config_data.get("verbose", Configuration.verbose),
        )

    @staticmethod
    def _load_toml_config(path: Path, verbose: bool = False) -> dict:
        """Load TOML configuration from the specified path or default locations.

        Args:
            path: Specific config file path
            verbose: Whether to print parsing messages

        Returns:
            dict: Configuration dictionary

        Raises:
            FileNotFoundError: When configuration file is not found
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        if verbose:
            typer.echo(f"Parsing configuration from: {path}")

        config_data = None
        try:
            with open(path, "rb") as f:
                config_data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            typer.secho(f"Error parsing {path}: {e}", err=True, color=True, fg="red")
            raise e

        return config_data


@dataclass(frozen=True)
class State:
    """Record state for obsidian-cli application."""

    editor: Path
    ident_key: str
    ignored_directories: list[str]
    journal_template: str
    vault: Path
    verbose: bool


@cli.callback()
def main(
    ctx: typer.Context,
    vault: Annotated[
        Optional[Path],
        typer.Option(
            envvar="OBSIDIAN_VAULT",
            help="Path to the Obsidian vault",
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            help=(
                "Path to the configuration file. "
                "(default: ./obsidian-cli.toml:~/.config/obsidian-cli/config.toml)"
            ),
            show_default=False,
        ),
    ] = None,
    ignored_directories: Annotated[
        Optional[str],
        typer.Option(
            "--ignored-directories",
            envvar="OBSIDIAN_BLACKLIST",
            help=(
                "Colon-separated list of directory patterns to ignore. "
                "(default: Assets/:.obsidian/:.git/)."
            ),
            show_default=False,
        ),
    ] = None,
    editor: Annotated[
        Optional[Path],
        typer.Option(
            envvar="EDITOR",
            help="Path for editor to use for editing journal entries (default: 'vi')",
            show_default=False,
        ),
    ] = None,
    verbose: Annotated[
        Optional[bool],
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose output",
            show_default=False,
        ),
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=_version,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """CLI operations for interacting with an Obsidian Vault."""
    try:
        configuration = Configuration.from_file(config, verbose=verbose is True)
    except FileNotFoundError:
        if verbose is True:
            typer.echo("No configuration file found, using defaults.")
        configuration = Configuration()
    except Exception as e:
        typer.secho(str(e), err=True, color=True, fg="red")
        raise typer.Exit(code=2) from e

    # Apply configuration values if CLI arguments are not provided
    if vault is None:
        vault_config = configuration.vault
        if vault_config:
            vault = Path(os.path.expanduser(vault_config))

    # Vault is required for all commands
    if vault is None:
        typer.secho(
            (
                "Error: Vault path is required. Use --vault option"
                " or specify 'vault' in a configuration file."
            ),
            err=True,
            color=True,
            fg="red",
        )
        raise typer.Exit(code=1)

    if editor is None:
        editor_config = configuration.editor
        if editor_config:
            editor = Path(os.path.expanduser(editor_config))

    # Get verbose setting from command line, config file, or default to False
    if verbose is None:
        verbose = configuration.verbose

    # Get ignored directories from command line, config, or defaults
    # (in order of precedence)
    if ignored_directories is not None:
        # Command line argument provided - split by colon
        ignored_dirs_list = [dir.strip() for dir in ignored_directories.split(":") if dir.strip()]
    else:
        # Use configuration file or defaults
        ignored_dirs_list = list(configuration.ignored_directories)

    # Validate journal template
    journal_template = configuration.journal_template
    try:
        test_vars = {
            "year": 2025,
            "month": 1,
            "day": 1,
            "month_name": "January",
            "month_abbr": "Jan",
            "weekday": "Monday",
            "weekday_abbr": "Mon",
        }
        journal_template.format(**test_vars)
    except (KeyError, ValueError) as e:
        typer.secho(
            f"Error: Invalid journal_template: {journal_template}",
            err=True,
            color=True,
            fg="red",
        )
        raise typer.Exit(code=1) from e

    # Create the application state
    ctx.obj = State(
        editor=editor,
        ident_key=configuration.ident_key,
        ignored_directories=ignored_dirs_list,
        journal_template=journal_template,
        vault=vault,
        verbose=verbose,
    )


PAGE_FILE = Annotated[
    Annotated[Path, typer.Argument(help="Obsidian page name or Path to file")],
    Doc("Obsidian page name or Path to markdown file."),
]

# CLI Commands (alphabetical order)


@cli.command()
def add_uid(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    force: Annotated[bool, typer.Option(help="if set, overwrite existing uid")] = False,
) -> None:
    """Add a unique ID to a page's frontmatter if it doesn't already have one."""
    state: State = ctx.obj

    try:
        # While the short cut of using Obsidian page names is convenient, it implies
        #  we cannot use typer helpers to enforce validation.
        filename = _resolve_path(page_or_path, state.vault)
    except FileNotFoundError as e:
        typer.secho(e, err=True, color=True, fg="red")
        raise typer.Exit(code=2) from e

    try:
        # Use the helper function to get frontmatter to check if UID already exists
        post = _get_frontmatter(filename)

        # Check if UID already exists
        if state.ident_key in post.metadata and not force:
            typer.secho(
                f"Page '{page_or_path}' already has UID: {post.metadata[state.ident_key]}",
                err=True,
                color=True,
                fg="red",
            )
            typer.secho("Use --force to replace it.", err=True, color="yellow")
            raise typer.Exit(code=1)

        import uuid

        new_uuid = str(uuid.uuid4())
        typer.echo(f"Generated new UUID: {new_uuid}") if state.verbose else None

        # Update frontmatter with the new UUID
        ctx.invoke(meta, ctx=ctx, page_or_path=page_or_path, key=state.ident_key, value=new_uuid)

    except Exception as e:
        raise typer.Exit(code=1) from e


@cli.command()
def cat(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    show_frontmatter: Annotated[
        bool, typer.Option(help="If set, show frontmatter in addition to file content.")
    ] = False,
) -> None:
    """Display the contents of a file in the Obsidian Vault."""
    state: State = ctx.obj

    try:
        filename = _resolve_path(page_or_path, state.vault)

        if show_frontmatter:
            # Simply read and display the entire file
            typer.echo(filename.read_text())
        else:
            # Parse with frontmatter and only display the content / body
            typer.echo(frontmatter.load(filename).content)
    except FileNotFoundError as e:
        typer.secho(e, err=True, color=True, fg="red")
        raise typer.Exit(code=2) from e
    except Exception as e:
        raise typer.Exit(code=1) from e


@cli.command()
def edit(ctx: typer.Context, page_or_path: PAGE_FILE) -> None:
    """Edit any file in the Obsidian Vault with the configured editor."""
    state: State = ctx.obj

    try:
        filename = _resolve_path(page_or_path, state.vault)
    except FileNotFoundError as e:
        typer.secho(e, err=True, color=True, fg="red")
        raise typer.Exit(code=2) from e

    try:
        # Open the file in the configured editor
        import subprocess

        subprocess.call([state.editor, filename])
    except FileNotFoundError:
        editor_name = state.editor
        typer.secho(
            f"Error: '{editor_name}' command not found. "
            f"Please ensure {editor_name} is installed and in your PATH.",
            err=True,
            color=True,
            fg="red",
        )
        raise typer.Exit(code=1)  # noqa: B904
    except Exception as e:
        typer.secho(f"An error occurred while editing {filename}", err=True, color=True, fg="red")
        raise typer.Exit(code=1) from e

    ctx.invoke(meta, ctx=ctx, page_or_path=page_or_path, key="modified", value=datetime.now())


@cli.command()
def find(
    ctx: typer.Context,
    page_name: Annotated[str, typer.Argument(help="Obsidian Page to use in search")],
    exact_match: Annotated[
        bool,
        typer.Option(
            "--exact/--no-exact",
            "-e",
            help="Require exact match on page name",
        ),
    ] = False,
) -> None:
    """Find files in the vault that match the given page name."""
    state: State = ctx.obj

    if state.verbose:
        typer.echo(f"Searching for page: '{page_name}'")
        typer.echo(f"Exact match: {exact_match}\n")

    # Convert page_name to lowercase for case-insensitive search if not exact match
    search_name = page_name if exact_match else page_name.lower()

    # Find matches
    matches = _find_matching_files(state.vault, search_name, exact_match)

    # Display results
    _display_find_results(matches, page_name, state.verbose, state.vault)


def _get_vault_info(state) -> dict:
    """Get vault information as structured data.

    Args:
        state: State object containing vault configuration

    Returns:
        Dictionary containing vault information
    """
    vault_path = Path(state.vault)

    if not vault_path.exists():
        return {
            "error": f"Vault not found at: {vault_path}",
            "vault_path": str(vault_path),
            "exists": False,
        }

    # Count files and directories
    file_count = 0
    dir_count = 0
    md_files = []

    for item in vault_path.rglob("*"):
        if item.is_file():
            file_count += 1
            if item.suffix == ".md":
                md_files.append(item)
        elif item.is_dir():
            dir_count += 1

    # Get journal template information
    template_vars = _get_journal_template_vars()
    journal_path_str = state.journal_template.format(**template_vars)

    return {
        "vault_path": str(vault_path),
        "exists": True,
        "total_files": file_count,
        "total_directories": dir_count,
        "markdown_files": len(md_files),
        "editor": state.editor,
        "verbose": state.verbose,
        "ignored_directories": state.ignored_directories,
        "journal_template": state.journal_template,
        "journal_path": journal_path_str,
        "version": __version__,
    }


@cli.command()
def info(ctx: typer.Context) -> None:
    """Display information about the current Obsidian Vault and configuration."""
    state: State = ctx.obj

    vault_info = _get_vault_info(state)

    if not vault_info["exists"]:
        typer.secho(vault_info["error"], err=True, color=True, fg="red")
        raise typer.Exit(code=1)

    # Display vault statistics
    typer.secho("--- Vault Information ---", bold=True)
    typer.echo(f"Vault Path: {vault_info['vault_path']}")
    typer.echo(f"Total Files: {vault_info['total_files']}")
    typer.echo(f"Total Directories: {vault_info['total_directories']}")

    # Display configuration information
    typer.echo("")
    typer.secho("--- Configuration Details ---", bold=True)
    typer.echo(f"Editor: {vault_info['editor']}")
    typer.echo(f"Verbose: {vault_info['verbose']}")
    typer.echo(f"Ignored Directories: {':'.join(vault_info['ignored_directories'])}")
    journal_template_info = f"{vault_info['journal_template']} => {vault_info['journal_path']}"
    typer.echo(f"Journal Template: {journal_template_info}")
    typer.echo(f"Version: {vault_info['version']}")


@cli.command()
def journal(
    ctx: typer.Context,
) -> None:
    """Open today's journal entry in the Obsidian Vault.

    (default: 'Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}')
    """
    state: State = ctx.obj

    # Prepare template variables using helper function
    template_vars = _get_journal_template_vars()

    try:
        # Format the template with current date
        journal_path_str = state.journal_template.format(**template_vars)
        page_path = Path(journal_path_str)
    except KeyError as e:
        typer.secho(
            f"Invalid template variable in journal_template: {e}", err=True, color=True, fg="red"
        )
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.secho(f"Error formatting journal template: {e}", err=True, color=True, fg="red")
        raise typer.Exit(code=1) from e

    if state.verbose:
        typer.echo(f"Using journal template: {state.journal_template}")
        typer.echo(f"Resolved journal path: {page_path}")

    try:
        # Open the journal for editing
        ctx.invoke(edit, ctx=ctx, page_or_path=page_path)
    except FileNotFoundError as e:
        typer.echo(f"Today's journal '{page_path}' not found.", err=True, color=True, fg="red")
        raise typer.Exit(code=2) from e


@cli.command()
@cli.command("frontmatter")
def meta(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    key: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "Key of the frontmatter metadata to view or update."
                " If unset, list all frontmatter metadata."
            ),
        ),
    ] = None,
    value: Annotated[
        Optional[str],
        typer.Option(help="New metadata for given key. If unset, list current metadata of key."),
    ] = None,
) -> None:
    """View or update frontmatter metadata in a file."""
    state: State = ctx.obj

    try:
        filename = _resolve_path(page_or_path, state.vault)
        post = _get_frontmatter(filename)
    except FileNotFoundError as e:
        typer.secho(e, err=True, color=True, fg="red")
        raise typer.Exit(code=1) from e

    try:
        # Process the metadata based on provided arguments
        if key is None:
            _list_all_metadata(post)
        elif value is None:
            _display_metadata_key(post, key)
        else:
            _update_metadata_key(post, filename, key, value, state.verbose)

    except KeyError:
        typer.secho(
            f"Key '{key}' not found in frontmatter of '{page_or_path}'",
            err=True,
            color=True,
            fg="red",
        )
        raise typer.Exit(code=1)  # noqa: B904
    except Exception as e:
        raise typer.Exit(code=1) from e


@cli.command()
def new(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    force: Annotated[bool, typer.Option(help="Overwrite existing file")] = False,
) -> None:
    """Create a new file in the Obsidian Vault."""
    state: State = ctx.obj

    # For new files, we check if it exists first, but don't use _resolve_path
    # since we expect the file to not exist yet
    filename = state.vault / page_or_path.with_suffix(".md")
    if filename.exists() and not force:
        typer.secho(f"File already exists: {filename}", err=True, color=True, fg="red")
        raise typer.Exit(code=1)
    elif filename.exists() and force:
        typer.secho(
            f"Overwriting existing file: {filename}", color="yellow"
        ) if state.verbose else None

    try:
        # Create parent directories if they don't exist
        filename.parent.mkdir(parents=True, exist_ok=True)

        # Metadata for the frontmatter
        title = page_or_path.stem

        # Check if stdin has content (if pipe is being used)
        if not sys.stdin.isatty():
            # Read content from stdin
            content = sys.stdin.read().strip()

            # Use the piped content for the file
            post = frontmatter.Post(content)
            typer.echo("Using content from stdin") if state.verbose else None
        else:
            from mdutils.mdutils import MdUtils

            md_file = MdUtils(file_name=str(filename), title=title, title_header_style="atx")
            post = frontmatter.Post(md_file.get_md_text())

        # Add frontmatter metadata
        created_time = datetime.now()
        post["created"] = created_time
        post["modified"] = created_time
        post["title"] = title

        import uuid

        post[state.ident_key] = str(uuid.uuid4())

        # Write to file with frontmatter
        with open(filename, "w") as f:
            f.write(frontmatter.dumps(post) + "\n\n")
        typer.echo(f"Created new file: {filename}") if state.verbose else None

        # Now edit the file if we're not using stdin
        # (if using stdin, the file already has content)
        if sys.stdin.isatty():
            ctx.invoke(edit, ctx=ctx, page_or_path=page_or_path)

    except Exception as e:
        raise typer.Exit(code=1) from e


@cli.command()
def query(
    ctx: typer.Context,
    key: Annotated[str, typer.Argument(help="Frontmatter key to query across Vault")],
    value: Annotated[
        Optional[str],
        typer.Option(help="Find pages where the key's metadata exactly matches this string"),
    ] = None,
    contains: Annotated[
        Optional[str],
        typer.Option(help="Find pages where the key's metadata contains this substring"),
    ] = None,
    exists: Annotated[
        bool,
        typer.Option("--exists", help="Find pages where the key exists", show_default=False),
    ] = False,
    missing: Annotated[
        bool,
        typer.Option("--missing", help="Find pages where the key is missing", show_default=False),
    ] = False,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format styles (path, title, full, count, json)",
        ),
    ] = "path",
    count: Annotated[
        bool,
        typer.Option(
            "--count",
            "-c",
            help="Only show count of matching pages",
            show_default=False,
        ),
    ] = False,
) -> None:
    """Query frontmatter across all files in the vault."""
    state: State = ctx.obj

    # Check for conflicting options
    if value is not None and contains is not None:
        typer.secho(
            "Error: Cannot specify both --value and --contains", err=True, color=True, fg="red"
        )
        raise typer.Exit(code=1)

    if state.verbose:
        typer.echo(f"Searching for frontmatter key: '{key}'")
        if value is not None:
            typer.echo(f"Filtering for exact value: '{value}'")
        if contains is not None:
            typer.echo(f"Filtering for substring: '{contains}'")
        if exists:
            typer.echo("Filtering for key existence")
        if missing:
            typer.echo("Filtering for key absence")

    # Find all markdown files in the vault
    markdown_files = list(state.vault.rglob("*.md"))
    matches = []

    for file_path in markdown_files:
        try:
            # Get relative path from vault root
            rel_path = file_path.relative_to(state.vault)

            # Skip files in ignored directories
            if _check_if_path_ignored(rel_path, state.ignored_directories):
                typer.echo(
                    f"Skipping excluded file: {rel_path}", err=True
                ) if state.verbose else None
                continue

            # Parse frontmatter
            post = _get_frontmatter(file_path)  # Check if key exists
            has_key = key in post.metadata

            # Apply filters
            if missing and has_key:
                continue
            if exists and not has_key:
                continue

            if has_key:
                metadata = post.metadata[key]

                # Value filtering
                if value is not None and str(metadata) != value:
                    continue

                # Contains filtering
                if contains is not None and contains not in str(metadata):
                    continue
            elif not missing:
                # If the key doesn't exist and we're not specifically
                # looking for missing keys
                continue

            # If we got here, the file matches all criteria
            matches.append((rel_path, post))

        except Exception as e:
            # Skip files with issues
            typer.echo(
                f"Warning: Could not process {file_path}: {e}",
                err=True,
                color="yellow",
            ) if state.verbose else None

    # Display results
    if count:
        typer.echo(f"Found {len(matches)} matching files")
    else:
        _display_query_results(matches, format, key)


@cli.command()
def rm(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    force: Annotated[bool, typer.Option(help="Skip confirmation prompt")] = False,
) -> None:
    """Remove a file from the Obsidian Vault."""
    state: State = ctx.obj

    try:
        filename = _resolve_path(page_or_path, state.vault)
    except FileNotFoundError as e:
        typer.secho(e, err=True, color=True, fg="red")
        raise typer.Exit(code=2) from e

    # Skip confirmation if force is True, otherwise ask for confirmation
    if not force and not typer.confirm(f"Are you sure you want to delete '{filename}'?"):
        typer.echo("Operation cancelled.")
        return

    try:
        # Remove the file
        filename.unlink()
        typer.echo(f"File removed: {filename}") if state.verbose else None
    except Exception as e:
        raise typer.Exit(code=1) from e


@cli.command()
def serve(ctx: typer.Context) -> None:
    """Start an MCP (Model Context Protocol) server for the vault."""

    # This command starts an MCP server that exposes vault operations as tools
    # that can be used by AI assistants and other MCP clients. The server
    # communicates over stdio using the MCP protocol.
    #
    # Example usage:
    #     obsidian-cli --vault /path/to/vault serve
    #
    # The server will run indefinitely until interrupted (Ctrl+C).

    state: State = ctx.obj

    try:
        import asyncio

        from .mcp_server import serve_mcp
    except ImportError as e:
        typer.secho(
            (
                f"Error: MCP dependencies not installed. "
                f"Please install with: pip install mcp\n"
                f"Details: {e}"
            ),
            err=True,
            color=True,
            fg="red",
        )
        raise typer.Exit(1) from e

    if state.verbose:
        typer.echo(f"Starting MCP server for vault: {state.vault}")
        typer.echo("Server will run until interrupted (Ctrl+C)")

    # Set up signal handling to suppress stack traces
    import signal
    import sys

    def signal_handler(signum, frame):
        if state.verbose:
            typer.echo("\nMCP server stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Run the MCP server
        asyncio.run(serve_mcp(ctx, state))
    except (KeyboardInterrupt, CancelledError):
        if state.verbose:
            typer.echo("\nMCP server stopped.")
        # Ensure output is flushed before exiting
        import sys

        sys.stdout.flush()
        sys.stderr.flush()
        # Return without raising to prevent any stack trace
        return
    except Exception as e:
        import traceback

        typer.secho(f"Error starting MCP server: {e}", err=True, color=True, fg="red")
        if state.verbose:
            typer.echo(f"Traceback: {traceback.format_exc()}", err=True)
        raise typer.Exit(1) from e


# Helper functions (alphabetical order)


def _check_if_path_ignored(rel_path: Path, ignored_directories: list[str]) -> bool:
    """Check if a relative path should be ignored based on configured patterns.

    Args:
        rel_path: The relative path to check.
        ignored_directories: List of directory patterns to ignore.

    Returns:
        bool: True if the path should be ignored, False otherwise.
    """
    path_str = str(rel_path)
    return any(path_str.startswith(pattern) for pattern in ignored_directories)


def _check_filename_match(file_stem: str, search_name: str, exact_match: bool) -> bool:
    """Check if a filename matches the search criteria.

    Args:
        file_stem: The filename without extension to check against.
        search_name: The search term to look for.
        exact_match: If True, requires exact equality; if False, performs a
                     case-insensitive substring match.

    Returns:
        bool: True if the filename matches the search criteria, False otherwise.
    """
    if exact_match:
        return file_stem == search_name
    else:
        return search_name in file_stem.lower()


def _check_title_match(post: frontmatter.Post, search_name: str) -> bool:
    """Check if a frontmatter title matches the search criteria.

    Looks for the 'title' key in the frontmatter and checks if the search term
    is contained within it (case-insensitive).

    Args:
        post: The frontmatter Post object containing metadata.
        search_name: The search term to look for in the title.

    Returns:
        bool: True if the title contains the search term, False otherwise or if
              there is no title in the frontmatter.
    """
    if "title" in post.metadata:
        title = post.metadata["title"]
        return isinstance(title, str) and search_name in title.lower()
    return False


def _display_find_results(matches: list[Path], page_name: str, verbose: bool, vault: Path) -> None:
    """Display the results of the find command.

    Prints the matching file paths to stdout. In verbose mode, also attempts
    to display the title from the frontmatter of each file.

    Args:
        matches: List of relative file paths that matched the search criteria.
        page_name: The original search term (for error messages).
        verbose: If True, display additional metadata about matched files.
        vault: Path to the Obsidian vault (for resolving relative paths).

    Returns:
        None: Results are printed directly to stdout.
    """
    if not matches:
        typer.secho(f"No files found matching '{page_name}'", err=True, color=True, fg="red")
    else:
        for match in sorted(matches):
            typer.echo(match)

            # Show frontmatter title if verbose and it exists
            if verbose:
                try:
                    path = vault / match
                    post = _get_frontmatter(path)
                    if "title" in post.metadata:
                        typer.echo(f"  title: {post.metadata['title']}")
                except Exception:
                    pass


def _display_metadata_key(post: frontmatter.Post, key: str) -> None:
    """Display the value for a specific metadata key.

    Retrieves and outputs the value associated with a specified key from
    a file's frontmatter.

    Args:
        post: The frontmatter Post object containing metadata.
        key: The key to look up and display from the frontmatter.

    Returns:
        None: Value is printed directly to stdout, or an error message if
              the key doesn't exist.
    """
    if key in post.metadata:
        typer.echo(f"{key}: {post.metadata[key]}")
    else:
        raise KeyError(f"Key '{key}' not found in frontmatter")


def _display_query_results(
    matches: list[tuple[Path, frontmatter.Post]], format_type: str, key: str
) -> None:
    """Display the results of a frontmatter query.

    Formats and displays the matching files based on the specified format type.

    Args:
        matches: List of tuples containing (relative_path, post) for each match.
        format_type: The output format to use ('path', 'title', 'full', or 'json').
        key: The frontmatter key that was queried.

    Returns:
        None: Results are printed directly to stdout.
    """

    if not matches:
        typer.echo("No matching files found", err=True, color="yellow")
        return

    match format_type:
        case "path":
            for rel_path, _ in sorted(matches, key=lambda x: x[0]):
                typer.echo(rel_path)

        case "title":
            for rel_path, post in sorted(matches, key=lambda x: x[0]):
                title = post.metadata.get("title", rel_path.stem)
                typer.echo(f"{rel_path}: {title}")

        case "full":
            for rel_path, post in sorted(matches, key=lambda x: x[0]):
                typer.echo(f"{rel_path}:")
                for k, v in post.metadata.items():
                    typer.echo(f"  {k}: {v}")
                typer.echo("")

        case "json":
            # Build a JSON-friendly structure
            result = []
            for rel_path, post in matches:
                entry = {
                    "path": str(rel_path),
                    "frontmatter": post.metadata,
                }
                if key in post.metadata:
                    entry["value"] = post.metadata[key]
                result.append(entry)

            import json

            typer.echo(json.dumps(result, indent=2, default=str))

        case _:
            raise ValueError(f"Unknown format type: {format_type}")


def _find_matching_files(vault: Path, search_name: str, exact_match: bool) -> list[Path]:
    """Find files in the vault that match the search criteria.

    Searches through all markdown files in the vault and checks if they match
    the search criteria either by filename or frontmatter title.

    Args:
        vault: Path to the Obsidian vault.
        search_name: The search term to look for in filenames and titles.
        exact_match: If True, requires exact equality; if False, performs
                     case-insensitive substring match.

    Returns:
        list[Path]: List of relative paths to files that match the search criteria.
    """
    matches = []

    # Search for markdown files in the vault
    for file_path in vault.rglob("*.md"):
        # Get relative path from vault root
        rel_path = file_path.relative_to(vault)

        # Get the file stem (filename without extension) as the page name
        file_stem = file_path.stem

        # Check for match in filename
        if _check_filename_match(file_stem, search_name, exact_match):
            matches.append(rel_path)
            continue

        # Also check frontmatter for title field if not exact match
        if not exact_match:
            try:
                post = _get_frontmatter(file_path)
                if _check_title_match(post, search_name) and rel_path not in matches:
                    matches.append(rel_path)
            except Exception:
                # Skip files with issues in frontmatter
                pass

    return matches


def _get_frontmatter(filename: Path) -> frontmatter.Post:
    """Get frontmatter from a file.

    Parses the given file and extracts its frontmatter and content.

    Args:
        filename: Path to the file to read.

    Returns:
        frontmatter.Post: Object containing both metadata and content.

    Raises:
        FileNotFoundError: When the file doesn't exist.
    """
    try:
        return frontmatter.load(filename)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File '{filename}' does not exist.") from e


def _get_journal_template_vars() -> dict[str, str | int]:
    """Get template variables for journal path formatting.

    Returns:
        dict: Dictionary containing template variables for journal path formatting.
    """
    date = datetime.now()
    return {
        "year": date.year,
        "month": date.month,
        "day": date.day,
        "month_name": date.strftime("%B"),
        "month_abbr": date.strftime("%b"),
        "weekday": date.strftime("%A"),
        "weekday_abbr": date.strftime("%a"),
    }


def _list_all_metadata(post: frontmatter.Post) -> None:
    """Display all metadata keys and values.

    Iterates through all keys in the frontmatter metadata and prints them
    with their associated values.

    Args:
        post: The frontmatter Post object containing metadata.

    Returns:
        None: Values are printed directly to stdout, or an error message
              if no metadata is found.
    """
    if not post.metadata:
        typer.secho("No frontmatter metadata found for this page", err=True, color=True, fg="red")
    else:
        for k, v in post.metadata.items():
            typer.echo(f"{k}: {v}")


def _resolve_path(page_or_path: Path, vault: Path) -> Path:
    """Resolve the path of a page or file within the Obsidian vault.

    First checks if the path exists as is, then checks if it exists relative to
    the vault path. Automatically adds .md extension if not present.

    Args:
        page_or_path: Path to resolve, may be absolute or relative to the vault.
        vault: Path to the Obsidian vault root.

    Returns:
        Path: The resolved absolute path to the file.

    Raises:
        FileNotFoundError: When the file cannot be found at either location.
    """
    filename = page_or_path.with_suffix(".md")
    if filename.exists():
        return page_or_path

    filename = vault / page_or_path.with_suffix(".md")
    if filename.exists():
        return filename

    raise FileNotFoundError(f"Page / File '{page_or_path}' not found.")


def _update_metadata_key(
    post: frontmatter.Post, filename: Path, key: str, value: str, verbose: bool
) -> None:
    """Update a specific metadata key with a new value.

    Sets or updates a metadata key in the frontmatter of a file and also
    updates the 'modified' timestamp. Saves the changes back to the file.

    Args:
        post: The frontmatter Post object containing metadata.
        filename: Path to the file to update.
        key: The metadata key to set or update.
        value: The value to set for the key.
        verbose: If True, print a message confirming the update.

    Returns:
        None: The file is updated directly, and a confirmation message may be printed.
    """
    post[key] = value
    post["modified"] = datetime.now()

    # Write back to the file
    with open(filename, "w") as f:
        f.write(frontmatter.dumps(post))
    typer.echo(f"Updated '{key}': '{value}' in {filename}") if verbose else None


if __name__ == "__main__":
    cli()
