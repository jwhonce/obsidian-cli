"""Exceptions for obsidian-cli application."""

from pathlib import Path
from typing import Optional, Union

from click import FileError


class ObsidianFileError(FileError):
    """Project-specific FileError with enhanced functionality.

    Encapsulates click.FileError with improved handling of file paths, messages,
    and exit codes for obsidian-cli specific operations.

    Attributes:
        file_path: Path to the file that caused the error
        message: Human-readable error message
        exit_code: Exit code to use when this error causes program termination

    Example:
        >>> error = ObsidianFileError("config.toml", "Configuration file not found", 12)
        >>> raise error
    """

    def __init__(self, file_path: Union[str, Path], message: Optional[str], exit_code: int = 12):
        """Initialize the ObsidianFileError.

        Args:
            file_path: Path to the file that caused the error (str or Path)
            message: Human-readable error message describing the issue
            exit_code: Exit code to use when this error terminates the program (default: 12)
        """
        # Call parent FileError constructor
        super().__init__(str(file_path), message)

        # Store additional attributes from grandparent Exception
        self.exit_code = exit_code

    def __str__(self) -> str:
        """Return a formatted error message."""
        return f"{self.message}: {self.ui_filename}"

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"filename={self.ui_filename!r}, "
            f"message={self.message!r}, "
            f"exit_code={self.exit_code})"
        )
