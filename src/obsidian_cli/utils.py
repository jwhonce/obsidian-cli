from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import frontmatter
import typer
from click import FileError
from rich.console import Console
from rich.markup import escape
from rich.table import Table

if TYPE_CHECKING:
    from .main import State


def _check_if_path_blacklisted(rel_path: Path, blacklist: list[str]) -> bool:
    """Check if a relative path should be blacklisted based on configured patterns.

    Args:
        rel_path: The relative path to check.
        blacklist: List of directory patterns to blacklist.

    Returns:
        bool: True if the path should be blacklisted, False otherwise.
    """
    path_str = str(rel_path)
    return any(path_str.startswith(pattern) for pattern in blacklist)


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
        typer.secho(f"No files found matching '{page_name}'", err=True, fg="red")
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

    from .main import QueryOutputStyle  # local import to avoid cycle at import time

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
        raise FileNotFoundError(e.errno, "Page or File does not exist.", filename) from None


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
        typer.secho("No frontmatter metadata found for this page", err=True, fg="red")
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

    e = FileError(page_or_path, f"Page or File not found in vault: {vault}")
    e.exit_code = 2
    raise e


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

    if verbose:
        typer.echo(f"Updated '{key}': '{value}' in {filename}")


def _get_vault_info(state: "State") -> dict[str, Any]:
    """Get vault information as structured data.

    Args:
        state: State object containing vault configuration

    Returns:
        Dictionary containing vault information
    """
    # Import version from main module to avoid duplication
    from .main import __version__

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
