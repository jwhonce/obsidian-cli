"""MCP Server implementation for Obsidian CLI.

This module provides an MCP (Model Context Protocol) server interface
that exposes Obsidian vault operations as tools that can be used by
AI assistants and other MCP clients.
"""

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

import typer

from . import __version__
from .types import MCPOperation, State
from .utils import (
    _create_mcp_error_response,
    _create_mcp_response,
    _format_file_size,
    _get_vault_info,
)

# MCP imports with error handling
try:
    from mcp.server import InitializationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import ServerCapabilities, TextContent, Tool
except ImportError as e:
    raise ImportError(
        f"MCP dependencies not installed. Please install with: pip install mcp. Details: {e}"
    ) from e


async def serve_mcp(ctx: typer.Context, state: State) -> None:
    """Start the MCP server with the given configuration.

    Args:
        ctx: Typer context for accessing CLI functionality
        state: State object containing vault configuration
    """
    # Create MCP server
    server = Server("obsidian-vault")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="create_note",
                description="Create a new note in the Obsidian vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Name of the note file"},
                        "content": {
                            "type": "string",
                            "description": "Initial content",
                            "default": "",
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Overwrite if exists",
                            "default": False,
                        },
                    },
                    "required": ["filename"],
                },
            ),
            Tool(
                name="find_notes",
                description="Find notes by name or title",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {"type": "string", "description": "Search term"},
                        "exact": {
                            "type": "boolean",
                            "description": "Exact match only",
                            "default": False,
                        },
                    },
                    "required": ["term"],
                },
            ),
            Tool(
                name="get_note_content",
                description="Get the content of a specific note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Name of the note file"},
                        "show_frontmatter": {
                            "type": "boolean",
                            "description": "Include frontmatter",
                            "default": False,
                        },
                    },
                    "required": ["filename"],
                },
            ),
            Tool(
                name="get_vault_info",
                description="Get information about the Obsidian vault",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        try:
            match name:
                case "create_note":
                    return await handle_create_note(ctx, state, arguments)
                case "find_notes":
                    return await handle_find_notes(ctx, state, arguments)
                case "get_note_content":
                    return await handle_get_note_content(ctx, state, arguments)
                case "get_vault_info":
                    return await handle_get_vault_info(ctx, state, arguments)
                case _:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            typer.secho(f"Error in tool {name}: {e}", err=True, fg=typer.colors.RED)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="obsidian-vault",
            server_version=__version__,
            capabilities=ServerCapabilities(tools={"enabled": True}),
        )
        await server.run(read_stream, write_stream, init_options)


async def handle_create_note(ctx: typer.Context, state: State, args: dict[str, Any]) -> list:
    """Create a new note in the vault."""
    filename = args["filename"]
    content = args.get("content", "")
    force = args.get("force", False)

    # Normalize filename for metadata
    normalized_filename = f"{filename}.md" if not filename.endswith(".md") else filename

    try:
        # Import inside function to avoid circular import (main.py imports serve_mcp)
        from .main import new

        # Convert filename to Path object
        # (remove .md if present, new() will add it)
        filename_path = Path(filename)
        if filename_path.suffix == ".md":
            filename_path = filename_path.with_suffix("")

        # If content is provided, we need to simulate stdin input
        if content:
            # Mock sys.stdin to simulate piped content
            with (
                patch.object(sys.stdin, "isatty", return_value=False),
                patch.object(sys.stdin, "read", return_value=content),
            ):
                new(ctx, filename_path, force=force)
        else:
            # Call the new command without content (will use default template)
            new(ctx, filename_path, force=force)

        success_msg = f"Successfully created note: {filename_path.with_suffix('.md')}"
        return _create_mcp_response(
            success_msg, MCPOperation.CREATE_NOTE, filename=normalized_filename
        )

    except typer.Exit as e:
        # Handle typer exits (like file already exists)
        if e.exit_code == 1:
            return _create_mcp_error_response(
                f"File {filename}.md already exists. Use force=true to overwrite.",
                MCPOperation.CREATE_NOTE,
                filename=normalized_filename,
                exit_code=str(e.exit_code),
            )
        else:
            return _create_mcp_error_response(
                f"Command exited with code {e.exit_code}",
                MCPOperation.CREATE_NOTE,
                filename=normalized_filename,
                exit_code=str(e.exit_code),
            )
    except Exception as e:
        return _create_mcp_error_response(
            f"Failed to create note: {str(e)}",
            MCPOperation.CREATE_NOTE,
            filename=normalized_filename,
        )


async def handle_find_notes(ctx: typer.Context, state: State, args: dict[str, Any]) -> list:
    """Find notes by name or title."""
    term = args["term"]
    exact = args.get("exact", False)

    try:
        # Import inside function to avoid circular import (main.py imports serve_mcp)
        from .main import _find_matching_files

        vault_path = Path(state.vault)
        matches = _find_matching_files(vault_path, term, exact)

        if not matches:
            return _create_mcp_response(
                f"No files found matching '{term}'",
                MCPOperation.FIND_NOTES,
                term=term,
                exact=exact,
                result_count=0,
            )

        file_list = "\n".join(f"- {match}" for match in matches)
        result = f"Found {len(matches)} file(s) matching '{term}':\n{file_list}\n"

        return _create_mcp_response(
            result, MCPOperation.FIND_NOTES, term=term, exact=exact, result_count=len(matches)
        )

    except Exception as e:
        return _create_mcp_error_response(
            f"Error finding notes: {str(e)}", MCPOperation.FIND_NOTES, term=term, exact=exact
        )


async def handle_get_note_content(ctx: typer.Context, state: State, args: dict[str, Any]) -> list:
    """Get the content of a specific note."""
    filename = args["filename"]
    show_frontmatter = args.get("show_frontmatter", False)

    try:
        # Import inside function to avoid circular import (main.py imports serve_mcp)
        from .main import cat

        # Convert filename to Path object
        filename_path = Path(filename)

        # Capture the output from cat command instead of printing to stdout
        output_buffer = io.StringIO()

        with redirect_stdout(output_buffer):
            # Call the cat command directly
            cat(ctx, filename_path, show_frontmatter=show_frontmatter)

        content = output_buffer.getvalue()
        return _create_mcp_response(
            content,
            MCPOperation.GET_NOTE_CONTENT,
            filename=filename,
            show_frontmatter=show_frontmatter,
        )

    except typer.Exit as e:
        # Handle typer exits (like file not found)
        if e.exit_code == 2:
            return _create_mcp_error_response(
                f"File not found: {filename}",
                MCPOperation.GET_NOTE_CONTENT,
                filename=filename,
                show_frontmatter=show_frontmatter,
                exit_code=str(e.exit_code),
            )
        else:
            return _create_mcp_error_response(
                f"Error reading note: exit code {e.exit_code}",
                MCPOperation.GET_NOTE_CONTENT,
                filename=filename,
                show_frontmatter=show_frontmatter,
                exit_code=str(e.exit_code),
            )
    except Exception as e:
        return _create_mcp_error_response(
            f"Error reading note: {str(e)}",
            MCPOperation.GET_NOTE_CONTENT,
            filename=filename,
            show_frontmatter=show_frontmatter,
        )


async def handle_get_vault_info(ctx: typer.Context, state: State, args: dict[str, Any]) -> list:
    """Get information about the vault."""

    try:
        vault_info = _get_vault_info(state)
        if vault_info.get("error"):
            return _create_mcp_error_response(vault_info["error"], MCPOperation.GET_VAULT_INFO)
    except Exception as e:
        return _create_mcp_error_response(
            f"Error retrieving vault information: {str(e)}", MCPOperation.GET_VAULT_INFO
        )

    if not vault_info["exists"]:
        return _create_mcp_error_response(vault_info["error"], MCPOperation.GET_VAULT_INFO)

    # Build file type statistics section
    try:
        file_type_section = ""
        if "file_type_stats" in vault_info and vault_info["file_type_stats"]:
            file_types = "\n".join(
                f"  - {ext}: {stats['count']} files ({_format_file_size(stats['total_size'])})"
                for ext, stats in sorted(vault_info["file_type_stats"].items())
            )
            file_type_section = f"\n- File Types by Extension:\n{file_types}\n"
        else:
            file_type_section = "\n- File Types: No files found\n"
    except Exception as e:
        file_type_section = f"\n- File Types: Error processing file statistics: {str(e)}\n"

    # Build vault information string
    try:
        info = (
            f"Obsidian Vault Information:\n"
            f"- Path: {vault_info['vault_path']}\n"
            f"- Total files: {vault_info['total_files']}\n"
            f"- Usage files: {_format_file_size(vault_info['usage_files'])}\n"
            f"- Total directories: {vault_info['total_directories']}"
            f"- Usage directories: {_format_file_size(vault_info['usage_directories'])}\n"
            f"{file_type_section}"
            f"- Editor: {vault_info['editor']}\n"
            f"- Blacklist: {vault_info['blacklist']}\n"
            f"- Config Dirs: {vault_info['config_dirs']}\n"
            f"- Journal template: {vault_info['journal_template']}\n"
            f"- Version: {vault_info['version']}\n"
        )
    except KeyError as e:
        return _create_mcp_error_response(
            f"Error: Missing vault info key: {str(e)}", MCPOperation.GET_VAULT_INFO
        )
    except Exception as e:
        return _create_mcp_error_response(
            f"Error formatting vault information: {str(e)}", MCPOperation.GET_VAULT_INFO
        )

    return _create_mcp_response(info, MCPOperation.GET_VAULT_INFO)
