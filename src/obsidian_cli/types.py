"""Common types and type definitions for Obsidian CLI.

This module contains shared type definitions that are used across multiple modules
to avoid circular imports and code duplication.
"""

from functools import partial
import functools
import tomllib
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Optional, Tuple

import typer
from typing_extensions import Doc

from .exceptions import ObsidianFileError

# Common type for page/file arguments used across commands
PAGE_FILE = Annotated[
    Annotated[Path, typer.Argument(help="Obsidian page name or Path to file")],
    Doc("Obsidian page name or Path to markdown file."),
]


@dataclass(frozen=True)
class Configuration:
    """Record configuration for obsidian-cli application.

    Default order of precedence (highest precedence first):
    - user-specified path(s) via --config option
    - ./obsidian-cli.toml (current directory)
    - (OS-specific user's config directory) /.config/obsidian-cli/config.toml
    - ~/.config/obsidian-cli/config.toml
    - Hand-coded defaults
    """

    blacklist: list[str] = field(
        default_factory=lambda: ["Assets/", ".obsidian/", ".git/"],
        metadata={
            "description": "Directories to exclude from `query`, `ls`, and other vault operations."
        },
    )
    config_dirs: list[str] = field(
        default_factory=lambda: [
            str(Path.cwd()),
            str(Path(typer.get_app_dir("obsidian-cli"))),
            str(Path.home() / ".config" / "obsidian-cli"),
        ],
        metadata={"description": "Search paths for a configuration file."},
    )
    editor: Path = field(
        default_factory=lambda: Path("vi"),
        metadata={"description": "Command to use for opening files with the `edit` command."},
    )
    ident_key: str = field(
        default="uid",
        metadata={
            "description": "Frontmatter key used for unique identifiers by the `add-uid` command."
        },
    )
    journal_template: str = field(
        default="Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}",
        metadata={
            "description": (
                "Template for generating journal file paths."
                " Supports various date formatting variables."
            )
        },
    )
    vault: Optional[Path] = field(
        default=None,
        metadata={"description": "Path to the Obsidian vault."},
    )
    verbose: bool = field(
        default=False, metadata={"description": "Enable verbose / debugging output."}
    )

    @classmethod
    def from_path(
        cls, path: Optional[Path] = None, verbose: bool = False
    ) -> Tuple[bool, "Configuration"]:
        """Load configuration from a TOML file or colon-separated list of files.

        Configuration entries are loaded in order of precedence, with the first file found
        taking precedence, missing entries will use hard-coded defaults.

        Args:
            path: Path to a TOML file
            verbose: Whether to print parsing messages

        Raises:
            ObsidianFileError: When configuration file is not found
            tomllib.TOMLDecodeError: When TOML parsing fails

        Returns:
            Tuple[bool, Configuration]: (
                True if config was read from file,
                False if using hard-coded defaults,
                Configuration
            )
        """

        # Instantiate default configuration values
        default = cls()

        config_found = False
        config_data = {}
        if path:
            config_data = cls._load_toml_config(path, verbose)
            config_found = True
        else:
            # Resolve config paths in order of precedence
            paths = []
            for entry in default.config_dirs:
                path = Path(entry)
                if path == Path.cwd():
                    paths.append(path / ".obsidian-cli.toml")
                else:
                    paths.append(path / "config.toml")

            for entry in paths:
                with suppress(ObsidianFileError):
                    config_data = cls._load_toml_config(entry, verbose)
                    config_found = True
                    break

        return (
            config_found,
            cls(
                blacklist=config_data.get(
                    "blacklist", config_data.get("ignored_directories", default.blacklist)
                ),
                editor=Path(config_data.get("editor", default.editor)),
                ident_key=config_data.get("ident_key", default.ident_key),
                journal_template=config_data.get("journal_template", default.journal_template),
                vault=Path(config_data["vault"]) if config_data.get("vault") else None,
                verbose=config_data.get("verbose", default.verbose),
            ),
        )

    @staticmethod
    def _load_toml_config(path: Path, verbose: bool = False) -> dict[str, Any] | None:
        """Load TOML configuration from the specified path or default locations.

        Args:
            path: Specific config file path
            verbose: Whether to print parsing messages

        Returns:
            dict: Configuration dictionary

        Raises:
            ObsidianFileError: When configuration file is not found
        """
        if verbose:
            typer.echo(f"Attempting to load configuration from: {path}")

        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            typer.secho(f"Error parsing {path}: {e}", err=True, fg=typer.colors.RED)
            raise
        except FileNotFoundError as e:
            raise ObsidianFileError(path, "Configuration file not found") from e


@dataclass(frozen=True)
class State:
    """Record running state for obsidian-cli application."""

    blacklist: list[str]
    config_dirs: list[str]
    editor: Path
    ident_key: str
    journal_template: str
    vault: Path
    verbose: bool
