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
    - OBSIDIAN_CONFIG_DIRS: Colon-separated list of configuration files to read from
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
Version: 0.1.20
License: Apache License 2.0
"""

import asyncio
import importlib.metadata
import os
import signal
import sys
import tomllib
import traceback
import uuid
from asyncio import CancelledError
from datetime import datetime
from pathlib import Path
from shutil import get_terminal_size
from typing import Annotated, Optional

import click
import frontmatter  # type: ignore[import-untyped]
import typer
from mdutils.mdutils import MdUtils  # type: ignore[import-untyped]

from .exceptions import ObsidianFileError
from .mcp_server import serve_mcp
from .types import PAGE_FILE, Configuration, QueryOutputStyle, Vault
from .utils import (
    _check_if_path_blacklisted,
    _display_find_results,
    _display_metadata_key,
    _display_query_results,
    _display_vault_info,
    _find_matching_files,
    _get_frontmatter,
    _get_journal_template_vars,
    _get_vault_info,
    _list_all_metadata,
    _resolve_path,
    _update_metadata_key,
)

# Get version from package metadata or fallback
try:
    __version__ = importlib.metadata.version("obsidian-cli")
except Exception:  # pylint: disable=broad-except
    # Fallback for development mode
    try:
        from . import __version__
    except Exception:  # pylint: disable=broad-except
        __version__ = "0.1.21"  # Fallback version


# Initialize Typer app
cli = typer.Typer(
    add_completion=False,
    context_settings={
        "auto_envvar_prefix": "OBSIDIAN",
        "max_content_width": get_terminal_size().columns,
    },
    help="Command-line interface for interacting with Obsidian.",
    no_args_is_help=True,
)


def _version(value: bool) -> None:
    """Callback to print version and exit."""
    if value:
        typer.echo(f"obsidian-cli v{__version__}")
        raise typer.Exit()


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
            dir_okay=False,
            envvar="OBSIDIAN_CONFIG",
            exists=True,
            file_okay=True,
            help=("Configuration file to read configuration from."),
        ),
    ] = None,
    blacklist: Annotated[
        Optional[str],
        typer.Option(
            "--blacklist",
            envvar="OBSIDIAN_BLACKLIST",
            help=(
                "Colon-separated list of directories to ignore. [default: Assets/:.obsidian/:.git/]"
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
            envvar="OBSIDIAN_VERBOSE",
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
            envvar="",
        ),
    ] = None,
) -> None:
    """CLI operations for interacting with an Obsidian Vault."""
    _ = version  # noqa: F841

    # Configuration order of precedence:
    #   command line args > environment variables > config file > coded default
    try:
        (from_file, configuration) = Configuration.from_path(config, verbose=verbose is True)

        if verbose is None:
            verbose = configuration.verbose
    except ObsidianFileError as e:
        raise click.UsageError("Error loading configuration.") from e
    except tomllib.TOMLDecodeError as e:
        raise click.UsageError("Error parsing TOML configuration file.") from e
    except Exception as e:
        raise click.UsageError("Error loading configuration.") from e
    finally:
        if verbose and not from_file:
            typer.secho(
                "Hard-coded defaults will be used as no config file was found.",
                err=True,
                fg=typer.colors.YELLOW,
            )

    # Apply configuration values if CLI arguments are not provided
    if vault is None:
        vault = configuration.vault
        # Vault is required for all commands
        if vault is None:
            raise typer.BadParameter(
                (
                    "vault path is required."
                    " Use --vault option, OBSIDIAN_VAULT environment variable,"
                    " or specify 'vault' in a configuration file."
                ),
                ctx=ctx,
                param_hint="--vault",
            )
    vault = vault.expanduser().resolve()

    # Validate that the vault directory exists and contains .obsidian folder
    if not vault.exists():
        raise typer.BadParameter(
            f"vault directory does not exist: {vault}",
            ctx=ctx,
            param_hint="--vault",
        )

    if not vault.is_dir():
        raise typer.BadParameter(
            f"vault path must be a directory: {vault}",
            ctx=ctx,
            param_hint="--vault",
        )

    obsidian_config_dir = vault / ".obsidian"
    if not obsidian_config_dir.exists():
        raise typer.BadParameter(
            f"invalid Obsidian vault: missing .obsidian directory in {vault}",
            ctx=ctx,
            param_hint="--vault",
        )

    if editor is None:
        editor = configuration.editor

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
    except (KeyError, ValueError):
        typer.secho(f"Invalid journal_template: {journal_template}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from None

    # Create the vault object
    ctx.obj = Vault(
        blacklist=blacklist_dirs_list,
        config_dirs=configuration.config_dirs,
        editor=editor,
        ident_key=configuration.ident_key,
        journal_template=journal_template,
        path=vault,
        verbose=verbose,
    )


# CLI Commands (alphabetical order)


@cli.command()
def add_uid(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    force: Annotated[bool, typer.Option(help="if set, overwrite existing uid")] = False,
) -> None:
    """Add a unique ID to a page's frontmatter if it doesn't already have one."""
    vault: Vault = ctx.obj
    filename = _resolve_path(page_or_path, vault.path)
    post = _get_frontmatter(filename)

    # Check if UID already exists (outside try block since this is intentional control flow)
    if vault.ident_key in post.metadata and not force:
        if vault.verbose:
            typer.secho(
                f"Use --force to replace value of existing {vault.ident_key}.",
                err=True,
                fg=typer.colors.YELLOW,
            )

        raise typer.BadParameter(
            (
                f"Page '{page_or_path}' already has"
                f" {{'{vault.ident_key}': '{post.metadata[vault.ident_key]}'}}"
            ),
            ctx=ctx,
            param_hint="force",
        )

    new_uuid = str(uuid.uuid4())
    if vault.verbose:
        typer.echo(f"Generated new {{'{vault.ident_key}': '{new_uuid}'}}")

    # Update frontmatter with the new UUID
    ctx.invoke(
        meta,
        ctx=ctx,
        page_or_path=page_or_path,
        key=vault.ident_key,
        value=new_uuid,
    )


@cli.command()
def cat(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    show_frontmatter: Annotated[
        bool, typer.Option(help="If set, show frontmatter in addition to file content.")
    ] = False,
) -> None:
    """Display the contents of a file in the Obsidian Vault."""
    vault: Vault = ctx.obj
    filename = _resolve_path(page_or_path, vault.path)

    if show_frontmatter:
        # Simply read and display the entire file
        try:
            typer.echo(filename.read_text())
        except Exception as e:
            typer.secho(
                f"Error displaying contents of '{page_or_path}': {e}", err=True, fg=typer.colors.RED
            )
            raise typer.Exit(code=1) from None
    else:
        try:
            # Parse with frontmatter and only display the content / body
            typer.echo(frontmatter.load(filename).content)
        except Exception as e:
            typer.secho(
                f"Error displaying contents of '{page_or_path}': {e}", err=True, fg=typer.colors.RED
            )
            raise typer.Exit(code=1) from None


@cli.command()
def edit(ctx: typer.Context, page_or_path: PAGE_FILE) -> None:
    """Edit any file in the Obsidian Vault with the configured editor."""
    vault: Vault = ctx.obj
    filename = _resolve_path(page_or_path, vault.path)

    # Note: typer.launch() is designed for opening URLs/files with default applications,
    # not for running specific commands with custom editors. For this use case, we need
    # to honor the user's configured editor, so subprocess.run() is the appropriate tool.

    try:
        import subprocess

        # Open the file in the configured editor
        subprocess.run([str(vault.editor), str(filename)], check=True)

    except FileNotFoundError as e:
        raise typer.BadParameter(
            f"command '{vault.editor}' not found. "
            f" Ensure '{vault.editor}' is installed and in your PATH={os.environ['PATH']}.",
            ctx=ctx,
            param_hint="--editor",
        ) from e
    except subprocess.CalledProcessError as e:
        typer.secho(
            f"Editor '{vault.editor}' exited with code {e.returncode} while editing {filename}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1) from None
    except Exception as e:
        typer.secho(
            f"Error launching editor '{vault.editor}' while editing {filename}: {e}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1) from None

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
    vault: Vault = ctx.obj

    if vault.verbose:
        typer.echo(f"Searching for page: '{page_name}'")
        typer.echo(f"Exact match: {exact_match}")

    # Normalize search name
    search_name = page_name if exact_match else page_name.lower()

    matches = _find_matching_files(vault.path, search_name, exact_match)
    if matches:
        _display_find_results(matches, page_name, vault.verbose, vault.path)
        return

    typer.secho(f"No files found matching '{page_name}'", err=True, fg=typer.colors.YELLOW)


@cli.command()
def info(ctx: typer.Context) -> None:
    """Display information about the current Obsidian Vault and configuration."""
    vault: Vault = ctx.obj

    vault_info = _get_vault_info(vault)
    if not vault_info["exists"]:
        typer.secho(
            f"Error getting vault info: {vault_info['error']}", err=True, fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    _display_vault_info(vault_info)


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
    """Open a journal entry in the Obsidian Vault."""
    vault: Vault = ctx.obj

    # If --date is provided, open that date's entry (YYYY-MM-DD). Otherwise, open today's entry.
    if date is None:
        dt = datetime.now()
    else:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise typer.BadParameter(
                "invalid --date format. Use ISO format YYYY-MM-DD.", ctx=ctx, param_hint="--date"
            ) from None

    # Build template variables from target date
    template_vars = _get_journal_template_vars(dt)
    try:
        journal_path_str = vault.journal_template.format(**template_vars)
        page_path = Path(journal_path_str).with_suffix(".md")
    except KeyError as e:
        typer.secho(
            f"Invalid template variable in journal_template: {e}", err=True, fg=typer.colors.RED
        )
        raise typer.Exit(code=1) from None
    except Exception as e:
        typer.secho(f"Error formatting journal template: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from None

    if vault.verbose:
        typer.echo(
            f"Using journal template: {vault.journal_template}\nResolved journal path: {page_path}",
        )

    ctx.invoke(edit, ctx=ctx, page_or_path=page_path)


@cli.command()
def ls(ctx: typer.Context) -> None:
    """List white-listed pages in the vault."""
    vault: Vault = ctx.obj

    # Find all markdown files in the vault
    for file_path in sorted(vault.path.rglob("*.md")):
        # Get relative path from vault root
        rel_path = file_path.relative_to(vault.path)

        # Skip files in blacklisted directories
        if _check_if_path_blacklisted(rel_path, vault.blacklist):
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
    vault: Vault = ctx.obj

    filename = _resolve_path(page_or_path, vault.path)
    post = _get_frontmatter(filename)

    try:
        # Process the metadata based on provided arguments
        if key is None:
            _list_all_metadata(post)
        elif value is None:
            _display_metadata_key(post, key)
        else:
            _update_metadata_key(post, filename, key, value, vault.verbose)
    except KeyError:
        typer.secho(
            f"Frontmatter metadata '{key}' not found in '{page_or_path}'",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1) from None
    except Exception as e:
        typer.secho(
            f"Error updating frontmatter metadata {{'{key}': '{value}'}} in '{page_or_path}': {e}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1) from None


@cli.command()
def new(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    force: Annotated[bool, typer.Option(help="Overwrite existing file with new contents")] = False,
) -> None:
    """Create a new file in the Obsidian Vault."""
    vault: Vault = ctx.obj

    # We don't use _resolve_path() here since we expect the file to not exist
    filename = vault.path / page_or_path.with_suffix(".md")
    is_overwrite = filename.exists()
    if is_overwrite:
        if not force:
            raise typer.BadParameter(
                f"File already exists: {filename}", ctx=ctx, param_hint="page_or_path"
            )

        if vault.verbose:
            typer.echo(f"Overwriting existing file: {filename}")

    # Create parent directories if they don't exist
    try:
        filename.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        typer.secho(
            f"Error creating directory '{filename.parent}': {e}", err=True, fg=typer.colors.RED
        )
        raise typer.Exit(code=1) from None

    # Prepare file content
    title = page_or_path.stem

    try:
        # Check if stdin has content (if pipe is being used)
        if not sys.stdin.isatty():
            # Read content from stdin
            content = sys.stdin.read().strip()
            post = frontmatter.Post(content)

            if vault.verbose:
                typer.echo("Using content from stdin")
        else:
            md_file = MdUtils(file_name=str(filename), title=title, title_header_style="atx")
            post = frontmatter.Post(md_file.get_md_text())
    except Exception as e:
        typer.secho(f"Error preparing file content: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from None

    # Add frontmatter metadata
    created_time = datetime.now()
    post["created"] = created_time
    post["modified"] = created_time
    post["title"] = title
    post[vault.ident_key] = str(uuid.uuid4())

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post) + "\n\n")
    except OSError as e:
        typer.secho(f"Error writing file '{filename}': {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from None

    # Open file in editor (if not using stdin input)
    if sys.stdin.isatty():
        ctx.invoke(edit, ctx=ctx, page_or_path=page_or_path)

    if vault.verbose:
        action = "Overwriting existing" if is_overwrite else "Created new"
        typer.echo(f"{action} file: {filename}")


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
    style: Annotated[
        QueryOutputStyle,
        typer.Option("--style", "-s", help="Output format style", case_sensitive=False),
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
    vault: Vault = ctx.obj

    # Check for conflicting options
    if value is not None and contains is not None:
        raise typer.BadParameter(
            "cannot specify both --value and --contains options",
            ctx=ctx,
        )

    if vault.verbose:
        typer.echo(f"Searching for frontmatter key: {key}")
        if value is not None:
            typer.echo(f"Filtering for exact value: {value}")
        if contains is not None:
            typer.echo(f"Filtering for substring: {contains}")
        if exists:
            typer.echo("Filtering for key existence")
        if missing:
            typer.echo("Filtering for key absence")

    # Find all markdown files in the vault
    matches = []
    for file_path in vault.path.rglob("*.md"):
        # Get relative path from vault root
        try:
            rel_path = file_path.relative_to(vault.path)
        except ValueError as e:
            typer.secho(
                f"Could not resolve relative path for {file_path}: {e}",
                err=True,
                fg=typer.colors.YELLOW,
            )
            continue

        # Skip files in blacklisted directories
        if _check_if_path_blacklisted(rel_path, vault.blacklist):
            if vault.verbose:
                typer.echo(f"Skipping excluded file: {rel_path}")
            continue

        try:
            post = _get_frontmatter(file_path)
        except ObsidianFileError as e:
            typer.secho(
                f"Could not parse frontmatter in {rel_path}: {e}", err=True, fg=typer.colors.YELLOW
            )
            continue

        # Check if key exists and apply filters
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

    # Display results
    if count:
        typer.echo(f"Found {len(matches)} matching files")
    else:
        _display_query_results(matches, style, key)


@cli.command()
def rm(
    ctx: typer.Context,
    page_or_path: PAGE_FILE,
    force: Annotated[bool, typer.Option(help="Skip confirmation prompt")] = False,
) -> None:
    """Remove a file from the Obsidian Vault."""
    vault: Vault = ctx.obj
    filename = _resolve_path(page_or_path, vault.path)

    if not force and not typer.confirm(f"Are you sure you want to delete '{filename}'?"):
        typer.echo("Operation cancelled.")
        return

    try:
        filename.unlink()
    except Exception as e:
        typer.secho(f"Error removing file: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from None

    if vault.verbose:
        typer.echo(f"File removed: {filename}")


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

    vault: Vault = ctx.obj

    if vault.verbose:
        typer.echo(f"Starting MCP server for vault: {vault.path}")
        typer.echo("Server will run until interrupted (Ctrl+C)")

    # Set up signal handling to suppress stack traces
    def signal_handler(signum, frame):
        if vault.verbose:
            typer.echo("MCP server stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Run the MCP server
        asyncio.run(serve_mcp(ctx, vault))
    except (KeyboardInterrupt, CancelledError):
        if vault.verbose:
            typer.echo("MCP server stopped.")
        # Ensure output is flushed before exiting
        sys.stdout.flush()
        sys.stderr.flush()
        # Return without raising to prevent any stack trace
        return
    except Exception as e:
        typer.secho(f"Error starting MCP server: {e}", err=True, fg=typer.colors.RED)
        if vault.verbose:
            typer.echo(f"Traceback: {traceback.format_exc()}")
        raise typer.Exit(1) from None


if __name__ == "__main__":
    cli()
