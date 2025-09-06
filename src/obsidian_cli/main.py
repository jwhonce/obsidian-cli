"""
Obsidian CLI - Command-line interface for interacting with Obsidian vaults

This module provides a comprehensive set of command-line tools to interact with
Obsidian vaults, making it easier to perform common operations from the terminal.
It facilitates tasks such as creating notes, editing content, querying metadata,
and managing files.

Key features:
- Access existing journal entries with configurable templates
- Add unique IDs to files
- Configuration via obsidian-cli.toml file and environment variables
- Create and edit markdown files with proper frontmatter
- Display information about the vault
- Find files by name or title with exact/fuzzy matching
- Force flag for commands that modify files
- Query files based on frontmatter metadata with configurable directory filtering
- View and update metadata in existing files

The CLI uses Typer for command-line interface management and provides a clean,
intuitive interface with extensive help documentation.

Example usage:
    $ obsidian-cli --help
    $ obsidian-cli --vault /path/to/vault info
    $ obsidian-cli --vault /path/to/vault new "My New Note"
    $ obsidian-cli --vault /path/to/vault query tags --exists
    $ obsidian-cli --vault /path/to/vault --blacklist "Archives/:Temp/" \
        query tags --exists
    $ obsidian-cli --vault /path/to/vault find "Daily Note" --exact
    $ obsidian-cli --vault /path/to/vault journal
    $ obsidian-cli --vault /path/to/vault rm --force unwanted-note
    $ OBSIDIAN_BLACKLIST="Templates/:Archive/" obsidian-cli --vault /path/to/vault \
        query tags --exists

Commands:
    add-uid     Add a unique ID to a page's frontmatter
    cat         Display the contents of a file
    edit        Edit any file with the configured editor
    find        Find files by name or title with exact/fuzzy matching
    info        Display vault and configuration information
    journal     Open a journal entry (optionally for a specific --date)
    ls          List markdown files in the vault, respecting the blacklist
    meta        View or update frontmatter metadata
    new         Create a new file in the vault
    query       Query frontmatter across all files
    rm          Remove a file from the vault
    serve       Start an MCP (Model Context Protocol) server

Configuration:
    The tool can be configured using an obsidian-cli.toml file which should contain:

    ```toml
    editor = "vi"
    ident_key = "uid"
    blacklist = ["Assets/", ".obsidian/", ".git/"]
    journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
    vault = "~/path/to/vault"
    verbose = false
    ```

    Configuration can be placed in:
    - ./obsidian-cli.toml (current directory)
    - ~/.config/obsidian-cli/config.toml (user's config directory)

    Environment Variables:
    - EDITOR: Editor to use for editing files
    - OBSIDIAN_BLACKLIST: Colon-separated list of directory patterns to ignore
    - OBSIDIAN_VAULT: Path to the Obsidian vault

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
Version: 0.1.14
License: Apache License 2.0
"""

import errno
import logging
import os
import sys
import tomllib
from asyncio import CancelledError
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from shutil import get_terminal_size
from typing import Annotated, Any, Optional, Union

import frontmatter
import typer
from typing_extensions import Doc

from .utils import (
    _check_if_path_blacklisted,
    _display_find_results,
    _display_metadata_key,
    _display_query_results,
    _find_matching_files,
    _get_frontmatter,
    _get_journal_template_vars,
    _list_all_metadata,
    _resolve_path,
    _update_metadata_key,
)

# Get version from package metadata or fallback
try:
    import importlib.metadata

    __version__ = importlib.metadata.version("obsidian-cli")
except Exception:
    # Fallback for development mode
    try:
        from . import __version__
    except Exception:
        __version__ = "0.1.14"  # Fallback version


# Initialize Typer app
cli = typer.Typer(
    add_completion=False,
    help="Command-line interface for interacting with Obsidian.",
    context_settings={"max_content_width": get_terminal_size().columns},
)
logger = logging.getLogger(__name__)


def _version(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"obsidian-cli v{__version__}")
        raise typer.Exit()


@dataclass(frozen=True)
class Configuration:
    """Record configuration for obsidian-cli application.

    Default paths include in order of precedence:
    - ./obsidian-cli.toml (current directory)
    - ~/.config/obsidian-cli/config.toml (user's config directory)
    """

    editor: Path = Path("vi")
    ident_key: str = "uid"
    blacklist: list[str] = field(default_factory=lambda: ["Assets/", ".obsidian/", ".git/"])
    journal_template: str = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
    vault: Optional[Path] = None
    verbose: bool = False

    config_dirs: list[Path] = field(
        default_factory=lambda: [
            Path("obsidian-cli.toml"),
            (
                Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
                / "obsidian-cli"
                / "config.toml"
            ),
        ]
    )

    @classmethod
    def from_file(cls, path: Optional[Path] = None, verbose: bool = False) -> "Configuration":
        """Load configuration from a TOML file."""
        default = cls()

        config_data = {}
        if path:
            config_data = cls._load_toml_config(path, verbose)
        else:
            # Search default locations
            for config_path in default.config_dirs:
                if config_path.exists():
                    config_data = cls._load_toml_config(config_path, verbose)
                    break

        return cls(
            editor=Path(config_data.get("editor", default.editor)),
            ident_key=config_data.get("ident_key", default.ident_key),
            blacklist=config_data.get(
                "blacklist", config_data.get("ignored_directories", default.blacklist)
            ),
            journal_template=config_data.get("journal_template", default.journal_template),
            vault=Path(config_data["vault"]) if config_data.get("vault") else default.vault,
            verbose=config_data.get("verbose", default.verbose),
        )

    @staticmethod
    def _load_toml_config(path: Path, verbose: bool = False) -> dict[str, Any]:
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
            raise FileNotFoundError(errno.ENOENT, "Configuration file not found", str(path))

        if verbose:
            typer.echo(f"Parsing configuration from: {path}")

        config_data = None
        try:
            with open(path, "rb") as f:
                config_data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            typer.secho(f"Error parsing {path}: {e}", err=True, fg="red")
            raise e

        return config_data


@dataclass(frozen=True)
class State:
    """Record state for obsidian-cli application."""

    editor: Path
    ident_key: str
    blacklist: list[str]
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
                "[default: ./obsidian-cli.toml:~/.config/obsidian-cli/config.toml]"
            ),
            show_default=False,
        ),
    ] = None,
    blacklist: Annotated[
        Optional[str],
        typer.Option(
            "--blacklist",
            envvar="OBSIDIAN_BLACKLIST",
            help=(
                "Colon-separated list of directory patterns to ignore. "
                "[default: Assets/:.obsidian/:.git/]"
            ),
            show_default=False,
        ),
    ] = None,
    editor: Annotated[
        Optional[Path],
        typer.Option(
            envvar="EDITOR",
            help="Path for editor to use for editing journal entries [default: 'vi']",
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
    ] = None,  # pyright: ignore[reportUnusedParameter]
) -> None:
    """CLI operations for interacting with an Obsidian Vault."""

    # Configuration precedence:
    #   command line args > environment variables > config file > coded defaults
    try:
        configuration = Configuration.from_file(config, verbose=(verbose is True))
    except FileNotFoundError:
        configuration = Configuration()
        if verbose is True:
            logger.warn("No configuration file found, using coded defaults.")
    except Exception as e:
        typer.secho(str(e), err=True, fg="red")
        raise typer.Exit(code=2) from e

    # Get verbose setting from command line, config file, or default to False
    if verbose is None:
        verbose = configuration.verbose
    logger.setLevel(logging.DEBUG if verbose else logging.WARN)

    # Apply configuration values if CLI arguments are not provided
    if vault is None:
        if configuration.vault:
            vault = configuration.vault.expanduser()

    # Vault is required for all commands
    if vault is None:
        typer.secho(
            (
                "Error: Vault path is required. Use --vault option"
                " or specify 'vault' in a configuration file."
            ),
            err=True,
            fg="red",
        )
        raise typer.Exit(code=2)

    if editor is None:
        if configuration.editor:
            editor = configuration.editor.expanduser()

    # Get blacklist directories from command line, config, or defaults
    # (in order of precedence)
    if blacklist is None:
        blacklist_dirs_list = list(configuration.blacklist)
    else:
        # Command line argument provided - split by colon
        blacklist_dirs_list = [dir.strip() for dir in blacklist.split(":") if dir.strip()]

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
            fg="red",
        )
        raise typer.Exit(code=1) from e

    # Create the application state
    ctx.obj = State(
        editor=editor,
        ident_key=configuration.ident_key,
        blacklist=blacklist_dirs_list,
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

    # While the short cut of using Obsidian page names is convenient, it implies
    #  we cannot use typer helpers to enforce validation.
    filename = _resolve_path(page_or_path, state.vault)

    try:
        # Use the helper function to get frontmatter to check if UID already exists
        post = _get_frontmatter(filename)

        # Check if UID already exists
        if state.ident_key in post.metadata and not force:
            typer.secho(
                f"Page '{page_or_path}' already has UID: {post.metadata[state.ident_key]}",
                err=True,
                fg="red",
            )
            typer.secho("Use --force to replace it.", err=True, fg="yellow")
            raise typer.Exit(code=1)

        import uuid

        new_uuid = str(uuid.uuid4())
        if state.verbose:
            typer.echo(f"Generated new UUID: {new_uuid}")

        # Update frontmatter with the new UUID
        ctx.invoke(
            meta,
            ctx=ctx,
            page_or_path=page_or_path,
            key=state.ident_key,
            value=new_uuid,
        )

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
    filename = _resolve_path(page_or_path, state.vault)

    try:
        if show_frontmatter:
            # Simply read and display the entire file
            typer.echo(filename.read_text())
        else:
            # Parse with frontmatter and only display the content / body
            typer.echo(frontmatter.load(filename).content)
    except Exception as e:
        raise typer.Exit(code=1) from e


@cli.command()
def edit(ctx: typer.Context, page_or_path: PAGE_FILE) -> None:
    """Edit any file in the Obsidian Vault with the configured editor."""
    state: State = ctx.obj
    filename = _resolve_path(page_or_path, state.vault)

    try:
        # Open the file in the configured editor
        import subprocess

        subprocess.call([state.editor, filename])
    except FileNotFoundError as e:
        typer.secho(
            f"Error: '{state.editor}' command not found. "
            f"Please ensure {state.editor} is installed and in your PATH.",
            err=True,
            fg="red",
        )
        raise typer.Exit(code=2) from e
    except Exception as e:
        typer.secho(f"An error occurred while editing {filename}", err=True, fg="red")
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


def _get_vault_info(state: Union[Path, str]) -> dict[str, Any]:
    """Get vault information as structured data.

    Args:
        state: State object containing vault configuration

    Returns:
        Dictionary containing vault information
    """

    # MCP server uses this function with state.vault as a string
    vault_path = Path(state.vault)

    if not vault_path.exists():
        return {
            "error": f"Vault not found at: {vault_path}",
            "vault_path": str(vault_path),
            "exists": False,
        }

    def _walk_vault(path: Path):
        """Recursively walks a directory and yields Path objects for directories and files."""
        yield path

        for entry in path.iterdir():
            if entry.is_dir():
                # Recursively call for subdirectories
                yield from _walk_vault(entry)
            else:
                # Yield file Path object
                yield entry

    summary: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "total_size": 0})

    for entry in _walk_vault(vault_path):
        if entry.is_dir():
            summary["directories"]["count"] += 1
            summary["directories"]["total_size"] += entry.lstat().st_size

        elif entry.is_file():
            summary["files"]["count"] += 1
            summary[entry.suffix]["count"] += 1

            try:
                st_size = entry.lstat().st_size
                summary["files"]["total_size"] += st_size
                summary[entry.suffix]["total_size"] += st_size
            except Exception:
                pass

    # Get journal template information
    template_vars = _get_journal_template_vars(datetime.now())
    journal_path_str = state.journal_template.format(**template_vars)

    return {
        "blacklist": state.blacklist,
        "editor": state.editor,
        "exists": True,
        "journal_path": journal_path_str,
        "journal_template": state.journal_template,
        "markdown_files": summary[".md"]["count"],
        "total_directories": summary["directories"]["count"],
        "total_files": summary["files"]["count"],
        "vault_path": str(vault_path),
        "verbose": state.verbose,
        "version": __version__,
    }


@cli.command()
def info(ctx: typer.Context) -> None:
    """Display information about the current Obsidian Vault and configuration."""
    state: State = ctx.obj

    vault_info = _get_vault_info(state)

    if not vault_info["exists"]:
        typer.secho(vault_info["error"], err=True, fg="red")
        raise typer.Exit(code=1)

    # Display vault statistics
    typer.secho("--- Vault Information ---", bold=True)
    typer.echo(f"Vault Path: {vault_info['vault_path']}")
    typer.echo(f"Markdown Files: {vault_info['markdown_files']}")
    typer.echo(f"Total Files: {vault_info['total_files']}")
    typer.echo(f"Total Directories: {vault_info['total_directories']}")

    # Display configuration information
    typer.echo("")
    typer.secho("--- Configuration Details ---", bold=True)
    typer.echo(f"Editor: {vault_info['editor']}")
    typer.echo(f"Verbose: {vault_info['verbose']}")
    typer.echo(f"Blacklist: {':'.join(vault_info['blacklist'])}")
    journal_template_info = f"{vault_info['journal_template']} => {vault_info['journal_path']}"
    typer.echo(f"Journal Template: {journal_template_info}")
    typer.echo(f"Version: {vault_info['version']}")


@cli.command()
def journal(
    ctx: typer.Context,
    date: Annotated[
        Optional[str],
        typer.Option(
            "--date",
            help="Date to open in YYYY-MM-DD format; defaults to today if omitted",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Open a journal entry in the Obsidian Vault.

    If --date is provided, open that date's entry (YYYY-MM-DD). Otherwise, open today's entry.
    """
    state: State = ctx.obj

    # Determine target date
    if date is None:
        dt = datetime.now()
    else:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError as e:
            typer.secho("Invalid --date format. Use YYYY-MM-DD.", err=True, fg="red")
            raise typer.Exit(code=1) from e

    # Build template variables from target date
    template_vars = _get_journal_template_vars(dt)

    try:
        journal_path_str = state.journal_template.format(**template_vars)
        page_path = Path(journal_path_str).with_suffix(".md")
    except KeyError as e:
        typer.secho(f"Invalid template variable in journal_template: {e}", err=True, fg="red")
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.secho(f"Error formatting journal template: {e}", err=True, fg="red")
        raise typer.Exit(code=1) from e

    if state.verbose:
        typer.echo(f"Using journal template: {state.journal_template}")
        typer.echo(f"Resolved journal path: {page_path}")

    try:
        # Open the journal for editing
        ctx.invoke(edit, ctx=ctx, page_or_path=page_path)
    except FileNotFoundError as e:
        typer.secho(f"Journal entry '{page_path}' not found.", err=True, fg="red")
        raise typer.Exit(code=2) from e


@cli.command()
def ls(ctx: typer.Context) -> None:
    """List all markdown files in the vault."""
    state: State = ctx.obj

    # Find all markdown files in the vault
    for file_path in sorted(state.vault.rglob("*.md")):
        # Get relative path from vault root
        rel_path = file_path.relative_to(state.vault)

        # Skip files in blacklisted directories
        if _check_if_path_blacklisted(rel_path, state.blacklist):
            continue

        typer.echo(rel_path)


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
    filename = _resolve_path(page_or_path, state.vault)

    try:
        post = _get_frontmatter(filename)
    except FileNotFoundError as e:
        typer.secho(e, err=True, fg="red")
        raise typer.Exit(code=2) from e

    try:
        # Process the metadata based on provided arguments
        if key is None:
            _list_all_metadata(post)
        elif value is None:
            _display_metadata_key(post, key)
        else:
            _update_metadata_key(post, filename, key, value, state.verbose)

    except KeyError as e:
        typer.secho(
            f"Key '{key}' not found in frontmatter of '{page_or_path}'",
            err=True,
            fg="red",
        )
        raise typer.Exit(code=1) from e
    except Exception as e:
        raise typer.Exit(code=1) from e


@cli.command()
def new(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    force: Annotated[bool, typer.Option(help="Overwrite existing file with new contents")] = False,
) -> None:
    """Create a new file in the Obsidian Vault."""
    state: State = ctx.obj

    # For new files, we check if it exists first, but don't use _resolve_path
    # since we expect the file to not exist yet
    filename = state.vault / page_or_path.with_suffix(".md")
    if filename.exists() and not force:
        typer.secho(f"File already exists: {filename}", err=True, fg="red")
        raise typer.Exit(code=1) from FileExistsError(
            errno.EEXIST, "File already exists", str(filename)
        )
    elif filename.exists() and force:
        if state.verbose:
            typer.secho(f"Overwriting existing file: {filename}", fg="yellow")

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
            if state.verbose:
                typer.echo("Using content from stdin")
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
        with open(filename, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post) + "\n\n")
        if state.verbose:
            typer.echo(f"Created new file: {filename}")

        # Now edit the file if we're not using stdin
        # (if using stdin, the file already has content)
        if sys.stdin.isatty():
            ctx.invoke(edit, ctx=ctx, page_or_path=page_or_path)

    except Exception as e:
        raise typer.Exit(code=1) from e


class QueryOutputStyle(StrEnum):
    JSON = "json"
    PATH = "path"
    TABLE = "table"
    TITLE = "title"


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
        QueryOutputStyle,
        typer.Option("--format", "-f", help="Output format style", case_sensitive=False),
    ] = QueryOutputStyle.PATH,
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
        typer.secho("Error: Cannot specify both --value and --contains", err=True, fg="red")
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
    matches = []
    for file_path in state.vault.rglob("*.md"):
        try:
            # Get relative path from vault root
            rel_path = file_path.relative_to(state.vault)

            # Skip files in blacklisted directories
            if _check_if_path_blacklisted(rel_path, state.blacklist):
                if state.verbose:
                    typer.echo(f"Skipping excluded file: {rel_path}", err=True)
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
            if state.verbose:
                typer.echo(
                    f"Warning: Could not process {file_path}: {e}",
                    err=True,
                    fg="yellow",
                )

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
    filename = _resolve_path(page_or_path, state.vault)

    # Skip confirmation if force is True, otherwise ask for confirmation
    if not force and not typer.confirm(f"Are you sure you want to delete '{filename}'?"):
        typer.echo("Operation cancelled.")
        return

    try:
        # Remove the file
        filename.unlink()
        if state.verbose:
            typer.echo(f"File removed: {filename}")
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

        typer.secho(f"Error starting MCP server: {e}", err=True, fg="red")
        if state.verbose:
            typer.secho(f"Traceback: {traceback.format_exc()}", err=True, fg="red")
        raise typer.Exit(1) from e


class TyperLoggerHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        (fg, bg) = (None, None)
        match record.levelno:
            case logging.DEBUG:
                fg = typer.colors.BLACK
            case logging.INFO:
                fg = typer.colors.BRIGHT_BLUE
            case logging.WARNING:
                fg = typer.colors.BRIGHT_MAGENTA
            case logging.CRITICAL:
                fg = typer.colors.BRIGHT_RED
            case logging.ERROR:
                fg = typer.colors.BRIGHT_WHITE
                bg = typer.colors.RED
        typer.secho(self.format(record), bg=bg, fg=fg)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET, handlers=(TyperLoggerHandler(),))

    cli()
