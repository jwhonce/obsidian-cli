"""MCP Server implementation for Obsidian CLI.

This module provides an MCP (Model Context Protocol) server interface
that exposes Obsidian vault operations as tools that can be used by
AI assistants and other MCP clients.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def serve_mcp(config) -> None:
    """Start the MCP server with the given configuration."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError as e:
        raise ImportError(
            f"MCP dependencies not installed. Please install with: pip install mcp. Details: {e}"
        ) from e

    # Create MCP server
    server = Server("obsidian-vault")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools"""
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
        """Handle tool calls"""
        try:
            if name == "create_note":
                return await handle_create_note(config, arguments)
            elif name == "find_notes":
                return await handle_find_notes(config, arguments)
            elif name == "get_note_content":
                return await handle_get_note_content(config, arguments)
            elif name == "get_vault_info":
                return await handle_get_vault_info(config, arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error(f"Error in tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        from mcp.server import InitializationOptions
        from mcp.types import ServerCapabilities

        init_options = InitializationOptions(
            server_name="obsidian-vault",
            server_version="0.1.8",
            capabilities=ServerCapabilities(tools={"enabled": True}),
        )
        await server.run(read_stream, write_stream, init_options)


async def handle_create_note(config, args: dict) -> list:
    """Create a new note in the vault"""
    from mcp.types import TextContent

    filename = args["filename"]
    content = args.get("content", "")
    force = args.get("force", False)

    try:
        from .main import _create_new_file

        vault_path = Path(config.vault)
        file_path = vault_path / f"{filename}.md"

        if file_path.exists() and not force:
            return [
                TextContent(
                    type="text",
                    text=f"File {filename}.md already exists. Use force=true to overwrite.",
                )
            ]

        _create_new_file(file_path, content)
        return [TextContent(type="text", text=f"Successfully created note: {filename}.md")]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to create note: {str(e)}")]


async def handle_find_notes(config, args: dict) -> list:
    """Find notes by name or title"""
    from mcp.types import TextContent

    term = args["term"]
    exact = args.get("exact", False)

    try:
        from .main import _find_matching_files

        vault_path = Path(config.vault)
        matches = _find_matching_files(vault_path, term, exact, config.ignored_directories)

        if not matches:
            return [TextContent(type="text", text=f"No files found matching '{term}'")]

        result = f"Found {len(matches)} file(s) matching '{term}':\n"
        for match in matches:
            result += f"- {match}\n"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error finding notes: {str(e)}")]


async def handle_get_note_content(config, args: dict) -> list:
    """Get the content of a specific note"""
    from mcp.types import TextContent

    filename = args["filename"]
    show_frontmatter = args.get("show_frontmatter", False)

    try:
        import frontmatter

        from .main import _resolve_path

        vault_path = Path(config.vault)
        file_path = _resolve_path(Path(filename), vault_path)

        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        if show_frontmatter:
            content = frontmatter.dumps(post)
        else:
            content = post.content

        return [TextContent(type="text", text=content)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error reading note: {str(e)}")]


async def handle_get_vault_info(config, args: dict) -> list:
    """Get information about the vault"""
    from mcp.types import TextContent

    try:
        vault_path = Path(config.vault)

        if not vault_path.exists():
            return [TextContent(type="text", text=f"Vault not found at: {vault_path}")]

        md_files = list(vault_path.rglob("*.md"))

        info = f"""Obsidian Vault Information:
- Path: {vault_path}
- Total Markdown files: {len(md_files)}
- Editor: {config.editor}
- Ignored directories: {", ".join(config.ignored_directories)}
- Journal template: {config.journal_template}
"""

        return [TextContent(type="text", text=info)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting vault info: {str(e)}")]
