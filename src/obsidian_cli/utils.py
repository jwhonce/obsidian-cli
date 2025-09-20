import json
from collections import defaultdict
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import humanize
import typer
from rich.console import Console
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from . import __version__
from .exceptions import ObsidianFileError
from .types import MCPOperation, MCPStatus, Vault


def _check_filename_match(file_path: Path, search_name: str, exact_match: bool) -> bool:
    """Check if a filename matches the search criteria.

    Args:
        file_path: The file path to check against (stem will be extracted).
        search_name: The search term to look for.
        exact_match: If True, requires exact equality; if False, performs a
                     case-insensitive substring match.

    Returns:
        bool: True if the filename matches the search criteria, False otherwise.
    """
    # Get the file stem (filename without extension) as the page name
    file_stem = file_path.stem

    if exact_match:
        return file_stem == search_name
    else:
        return search_name in file_stem.lower()


def _check_if_path_blacklisted(rel_path: Path, blacklist: list[str]) -> bool:
    """Check if a relative path should be blacklisted based on configured patterns.

    Args:
        rel_path: The relative path to check.
        blacklist: List of directory patterns to blacklist.

    Returns:
        bool: True if the path should be blacklisted, False otherwise.
    """
    return any(str(rel_path).startswith(pattern) for pattern in blacklist)


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


# MCP (Model Context Protocol) helper functions
def _create_mcp_error_response(
    text: str,
    operation: MCPOperation,
    **additional_meta: Any,
) -> list:
    """Create a standardized MCP error response.

    Args:
        text: Error message text
        operation: MCP operation type
        **additional_meta: Additional metadata fields

    Returns:
        List containing a single TextContent error response
    """
    return _create_mcp_response(text, operation, MCPStatus.ERROR, **additional_meta)


def _create_mcp_response(
    text: str,
    operation: MCPOperation,
    status: MCPStatus = MCPStatus.SUCCESS,
    **additional_meta: Any,
) -> list:
    """Create a standardized MCP TextContent response with metadata.

    Args:
        text: Response text content
        operation: MCP operation type
        status: Response status
        **additional_meta: Additional metadata fields

    Returns:
        List containing a single TextContent object with metadata
    """
    # Import here to avoid circular imports and handle optional MCP dependency
    try:
        from mcp.types import TextContent
    except ImportError as e:
        raise ImportError(
            f"MCP dependencies not installed. Please install with: pip install mcp. Details: {e}"
        ) from e

    meta = {
        "operation": operation.value,
        "status": status.value,
        **additional_meta,
    }

    return [TextContent(type="text", text=text, _meta=meta)]


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
        typer.secho(f"No files found matching '{page_name}'", err=True, fg="red")
        return

    for match in sorted(matches):
        typer.echo(match)

        # Show frontmatter title if verbose and it exists
        if verbose:
            with suppress(Exception):
                post = _get_frontmatter(vault / match)
                if "title" in post.metadata:
                    typer.echo(f"  title: {post.metadata['title']}")


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
    matches: list[tuple[Path, frontmatter.Post]], format_type, key: str
) -> None:
    """Display the results of a frontmatter query.

    Formats and displays the matching files based on the specified format type.

    Args:
        matches: List of tuples containing (relative_path, post) for each match.
        format_type: The output format to use ('path', 'title', 'table', or 'json').
        key: The frontmatter key that was queried.

    Returns:
        None: Results are printed directly to stdout.
    """
    from .types import QueryOutputStyle  # Runtime import to avoid circular dependency

    if not matches:
        typer.echo("No matching files found", err=True, color="yellow")
        return

    match format_type:
        case QueryOutputStyle.PATH:
            for rel_path, _ in sorted(matches, key=lambda x: x[0]):
                typer.echo(rel_path)

        case QueryOutputStyle.TITLE:
            for rel_path, post in sorted(matches, key=lambda x: x[0]):
                title = post.metadata.get("title", rel_path.stem)
                typer.echo(f"{rel_path}: {title}")

        case QueryOutputStyle.TABLE:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Path", style="cyan", header_style="bold cyan")
            table.add_column("Property")
            table.add_column("Value")

            for rel_path, post in sorted(matches, key=lambda x: x[0]):
                page = str(rel_path)
                for k, v in post.metadata.items():
                    table.add_row(page, k, escape(str(v)))
                    page = None  # Only show path on first row of section
                table.add_section()
            table.caption = f"Total matches: {len(matches)}"
            Console().print(table)

        case QueryOutputStyle.JSON:
            # Build a JSON-friendly structure
            result: list[dict[str, Any]] = []
            for rel_path, post in matches:
                entry: dict[str, Any] = {
                    "path": str(rel_path),
                    "frontmatter": post.metadata,
                }
                if key in post.metadata:
                    entry["value"] = post.metadata[key]
                result.append(entry)

            typer.echo(json.dumps(result, indent=2, default=str))

        case _:
            raise ValueError(
                f"Unknown format type: {format_type}."
                f" Supported types: {', '.join([e.value for e in QueryOutputStyle])}"
            )


def _display_vault_info(vault_info: dict[str, Any]) -> None:
    """Display vault information using Rich formatting.

    Args:
        vault_info: Dictionary containing vault information from _get_vault_info()
    """
    console = Console()

    # Title
    console.print("\n[bold blue]OBSIDIAN VAULT INFORMATION[/bold blue]\n")

    # Vault Summary Table
    summary_table = Table(
        title="[bold]Vault Summary[/bold]",
        show_header=False,
        box=None,
        padding=(0, 1),
        title_justify="left",
    )
    summary_table.add_column("Property", style="cyan", width=20)
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Path", vault_info["vault_path"])
    summary_table.add_row("Total Directories", str(vault_info["total_directories"]))

    console.print(summary_table)
    console.print()

    # File Types Table
    if vault_info.get("file_type_stats"):
        # Print title without padding (hangs left of table)
        console.print("[bold italic]Vault File Types by Extension[/italic bold]")

        file_table = Table(show_header=True, header_style="bold magenta", border_style="blue")
        file_table.add_column("Extension", style="green", width=15)
        file_table.add_column("Count", justify="right", style="yellow", width=10)
        file_table.add_column("Size", justify="right", style="cyan", width=12)
        file_table.add_column("Percentage", justify="right", style="white", width=12)

        total_files = vault_info["total_files"]
        for ext, stats in sorted(vault_info["file_type_stats"].items()):
            ext_display = ext if ext != "." else "(no extension)"
            size_str = _format_file_size(stats["total_size"])
            count = stats["count"]
            percentage = f"{(count / total_files * 100):.1f}%" if total_files > 0 else "0.0%"

            file_table.add_row(ext_display, str(count), size_str, percentage)

        # Add totals row
        if vault_info["file_type_stats"]:
            file_table.add_section()  # Add separator line
            total_size_str = _format_file_size(vault_info["usage_files"])
            file_table.add_row(
                "[bold]TOTAL[/bold]",
                f"[bold]{vault_info['total_files']}[/bold]",
                f"[bold]{total_size_str}[/bold]",
                "[bold]100.0%[/bold]",
            )

        console.print(Padding(file_table, (0, 0, 0, 1)))
        console.print()
    else:
        console.print("[yellow]No files found in vault[/yellow]\n")

    # Configuration Table
    config_table = Table(
        title="[bold]Configuration Details[/bold]",
        show_header=False,
        box=None,
        padding=(0, 1),
        title_justify="left",
    )

    config_table.add_column("Setting", style="cyan", width=20)
    config_table.add_column("Value", style="white", no_wrap=False)

    config_table.add_row("Vault Blacklist", vault_info["blacklist"])
    config_table.add_row("Config Dirs", vault_info["config_dirs"])
    config_table.add_row("Editor", str(vault_info["editor"]))

    journal_info = f"{vault_info['journal_template']} => [cyan]{vault_info['journal_path']}[/cyan]"
    config_table.add_row("Journal Template", journal_info)
    config_table.add_row("Verbose", "Yes" if vault_info["verbose"] else "No")
    config_table.add_row("Version", vault_info["version"])

    console.print(config_table)
    console.print()


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
    matches: list[Path] = []

    # Search for markdown files in the vault
    for file_path in vault.rglob("*.md"):
        # Get relative path from vault root
        rel_path = file_path.relative_to(vault)

        # Check for match in filename
        if _check_filename_match(file_path, search_name, exact_match):
            matches.append(rel_path)
            continue

        # Also check frontmatter for title field if not exact match
        if not exact_match:
            with suppress(Exception):
                post = _get_frontmatter(file_path)
                if _check_title_match(post, search_name) and rel_path not in matches:
                    matches.append(rel_path)

    return matches


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "1.5 KB", "2.3 MB")
    """
    return humanize.naturalsize(size_bytes)


def _get_frontmatter(filename: Path) -> frontmatter.Post:
    """Get frontmatter from a file.

    Parses the given file and extracts its frontmatter and content.

    Args:
        filename: Path to the file to read.

    Returns:
        frontmatter.Post: Object containing both metadata and content.

    Raises:
        ObsidianFileError: When the file doesn't exist.
    """
    try:
        return frontmatter.load(filename)
    except FileNotFoundError:
        typer.secho(f"Page or File '{filename}' does not exist.", err=True, fg=typer.colors.RED)
        raise ObsidianFileError(filename, "Page or File does not exist.") from None


def _get_journal_template_vars(date: datetime) -> dict[str, str | int]:
    """Get template variables for journal path formatting.

    Returns:
        dict: Dictionary containing template variables for journal path formatting.
    """
    return {
        "year": date.year,
        "month": date.month,
        "day": date.day,
        "month_name": date.strftime("%B"),
        "month_abbr": date.strftime("%b"),
        "weekday": date.strftime("%A"),
        "weekday_abbr": date.strftime("%a"),
    }


def _get_vault_info(vault: Vault) -> dict[str, Any]:
    """Get vault information as structured data.

    Args:
        vault: Vault object containing vault configuration

    Returns:
        Dictionary containing vault information
    """

    # MCP server uses this function with vault.path as a string
    vault_path = Path(vault.path)

    if not vault_path.exists():
        return {
            "error": f"Vault not found at: {vault_path}",
            "vault_path": str(vault_path),
            "exists": False,
        }

    def __walk_vault(path: Path):
        """Recursively walks a directory and yields Path objects for directories and files,
        respecting the configured blacklist."""
        yield path

        for entry in path.iterdir():
            # Get relative path for blacklist checking
            rel_path = entry.relative_to(vault_path)

            # Check if this path or any parent path is blacklisted
            # For directories, also check if the directory itself matches a blacklist pattern
            is_blacklisted = _check_if_path_blacklisted(rel_path, vault.blacklist)
            if not is_blacklisted and entry.is_dir():
                # For directories, also check if adding a trailing slash matches any pattern
                dir_path_with_slash = str(rel_path) + "/"
                is_blacklisted = any(
                    dir_path_with_slash.startswith(pattern) for pattern in vault.blacklist
                )

            # Skip blacklisted paths
            if is_blacklisted:
                continue

            if entry.is_dir():
                # Recursively call for subdirectories (only if not blacklisted)
                yield from __walk_vault(entry)
            else:
                # Yield file Path object (only if not blacklisted)
                yield entry

    summary: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "total_size": 0})
    file_type_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "total_size": 0})

    for entry in __walk_vault(vault_path):
        if entry.is_dir():
            summary["directories"]["count"] += 1
            with suppress(Exception):
                summary["directories"]["total_size"] += entry.lstat().st_size

        elif entry.is_file():
            summary["files"]["count"] += 1

            suffix = entry.suffix.lstrip(".") if entry.suffix else "."
            file_type_stats[suffix]["count"] += 1
            with suppress(Exception):
                st_size = entry.lstat().st_size
                summary["files"]["total_size"] += st_size
                file_type_stats[suffix]["total_size"] += st_size

    # Get journal template information
    template_vars = _get_journal_template_vars(datetime.now())
    journal_path_str = vault.journal_template.format(**template_vars)

    return {
        "blacklist": ":".join(vault.blacklist),
        "config_dirs": ":".join(vault.config_dirs),
        "editor": vault.editor,
        "exists": True,
        "file_type_stats": file_type_stats,
        "journal_path": journal_path_str,
        "journal_template": vault.journal_template,
        "markdown_files": file_type_stats.get("md", {}).get(
            "count", 0
        ),  # Keep for backward compatibility
        "total_directories": summary["directories"]["count"],
        "total_files": summary["files"]["count"],
        "usage_directories": summary["directories"]["total_size"],
        "usage_files": summary["files"]["total_size"],
        "vault_path": str(vault_path),
        "verbose": vault.verbose,
        "version": __version__,
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
        typer.secho("No frontmatter metadata found for this page", err=True, fg=typer.colors.RED)
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
        ObsidianFileError: When the file cannot be found at either location.
    """
    filename = page_or_path.with_suffix(".md")
    if filename.exists():
        return page_or_path

    filename = vault / page_or_path.with_suffix(".md")
    if filename.exists():
        return filename

    typer.secho(
        f"Page or File '{page_or_path}' not found in vault: {vault}", err=True, fg=typer.colors.RED
    )
    raise typer.BadParameter(f"Page or File not found in vault: {vault}", param_hint="page_or_path")


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

    try:
        # Write back to the file
        with open(filename, "w") as f:
            f.write(frontmatter.dumps(post))
    except FileNotFoundError as e:
        typer.secho(
            f"Error updating file '{filename}' with frontmatter metadata "
            f"{{'{key}': '{value}'}}: {e}",
            err=True,
            fg=typer.colors.RED,
        )
        raise ObsidianFileError(
            filename, f"Unable to update frontmatter metadata {{'{key}':'{value}'}} in {filename}"
        ) from e

    if verbose:
        typer.echo(
            "Updated frontmatter metadata"
            f" {{ '{key}': '{value}', 'modified': '{post['modified']}' }} in {filename}"
        )
