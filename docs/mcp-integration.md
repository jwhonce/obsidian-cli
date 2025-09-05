# MCP (Model Context Protocol) Integration

Obsidian CLI includes a powerful MCP server that exposes vault operations as standardized tools for AI assistants and other MCP clients. This integration allows AI systems to directly interact with your Obsidian vault, enabling seamless note management, content retrieval, and vault organization through natural language interfaces.

## Overview

The Model Context Protocol (MCP) is an open standard that enables AI assistants to securely connect to external data sources and tools. By implementing an MCP server, Obsidian CLI makes your vault accessible to any MCP-compatible AI assistant, allowing for sophisticated knowledge management workflows.

### Key Benefits

- **Direct Vault Access**: AI assistants can create, read, and search notes without manual intervention
- **Standardized Interface**: Uses the open MCP protocol for broad compatibility
- **Secure Communication**: Operates over stdio with controlled access permissions
- **Real-time Interaction**: Immediate synchronization between AI actions and vault state
- **Workflow Integration**: Seamlessly integrates with existing Obsidian workflows

## Quick Start

### Installation Requirements

Ensure you have the MCP dependencies installed:

```bash
pip install obsidian-cli[mcp]
# OR if already installed:
pip install mcp>=1.0.0
```

### Starting the Server

```bash
# Basic usage with vault from configuration
obsidian-cli serve

# Specify vault path explicitly
obsidian-cli --vault /path/to/your/vault serve

# Enable verbose logging for debugging
obsidian-cli --verbose serve

# Using environment variables
export OBSIDIAN_VAULT="/path/to/your/vault"
obsidian-cli serve
```

The server will run indefinitely until interrupted with `Ctrl+C` or terminated by the MCP client.

## Available MCP Tools

The MCP server exposes four primary tools that cover the essential vault operations:

### 1. create_note

Creates new notes in the vault with proper frontmatter handling.

**Parameters:**

- `filename` (required): Name of the note file (without .md extension)
- `content` (optional): Initial content for the note
- `force` (optional, default: false): Overwrite existing files if they exist

**Examples:**

```json
{
  "filename": "meeting-notes-2025-01-15",
  "content": "# Meeting Notes\n\n## Agenda\n- Project updates\n- Next steps",
  "force": false
}
```

**Use Cases:**

- Creating daily notes with templates
- Generating meeting notes from AI conversations
- Automated content creation based on external data

### 2. find_notes

Searches for notes by filename or title with flexible matching options.

**Parameters:**

- `term` (required): Search term to match against filenames and titles
- `exact` (optional, default: false): Whether to require exact matches

**Examples:**

```json
{
  "term": "project",
  "exact": false
}
```

**Use Cases:**

- Locating related notes for research
- Finding specific topics across the vault
- Discovery of existing content before creating new notes

### 3. get_note_content

Retrieves the content of specific notes with optional frontmatter inclusion.

**Parameters:**

- `filename` (required): Name of the note file to retrieve
- `show_frontmatter` (optional, default: false): Include YAML frontmatter in output

**Examples:**

```json
{
  "filename": "project-alpha-status",
  "show_frontmatter": true
}
```

**Use Cases:**

- Reading note content for analysis or summary
- Extracting metadata for processing
- Content review and fact-checking

### 4. get_vault_info

Provides comprehensive information about the vault structure and statistics.

**Parameters:** None required

**Returns:**

- Total note count
- Vault path and configuration
- Recent activity summary
- Directory structure overview

**Use Cases:**

- Vault health monitoring
- Statistical analysis of note-taking patterns
- Configuration verification

## Configuration

### Server Configuration

The MCP server inherits all configuration from your Obsidian CLI setup:

```toml
# ~/.config/obsidian-cli/config.toml
vault = "/Users/username/Documents/MyVault"
editor = "code"
verbose = false

[templates]
daily_note = "templates/daily-note.md"
meeting = "templates/meeting.md"

[blacklist]
patterns = [".obsidian", "assets", "archive"]
```

### Environment Variables

```bash
# Required: Vault path
export OBSIDIAN_VAULT="/path/to/vault"

# Optional: Configuration file
export OBSIDIAN_CONFIG="/path/to/config.toml"

# Optional: Enable verbose logging
export OBSIDIAN_VERBOSE=true
```

## AI Assistant Integration

### Compatible AI Systems

The MCP server works with any AI assistant that supports the Model Context Protocol, including:

- Claude Desktop (with MCP configuration)
- Custom AI applications using MCP SDK
- Development tools with MCP integration
- Future MCP-compatible platforms

### Configuration Examples

#### Claude Desktop Configuration

Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "obsidian-cli",
      "args": ["--vault", "/path/to/your/vault", "serve"],
      "env": {
        "OBSIDIAN_VERBOSE": "false"
      }
    }
  }
}
```

#### Custom Python Application

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_obsidian_vault():
    server_params = StdioServerParameters(
        command="obsidian-cli",
        args=["--vault", "/path/to/vault", "serve"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            tools = await session.list_tools()

            # Create a new note
            result = await session.call_tool(
                "create_note",
                {
                    "filename": "ai-generated-note",
                    "content": "This note was created by an AI assistant!"
                }
            )
```

## Use Cases and Workflows

### 1. Intelligent Note Creation

AI assistants can create structured notes based on conversation context:

```
User: "Create a project status note for Alpha project"
AI: Creates "project-alpha-status-2025-01-15.md" with structured template
```

### 2. Content Discovery and Research

AI can search and analyze existing notes to provide insights:

```
User: "What notes do I have about machine learning?"
AI: Searches vault, finds related notes, and provides summary
```

### 3. Vault Maintenance

Automated vault organization and maintenance:

```
AI: Identifies orphaned notes, suggests linking opportunities,
    generates index pages, maintains tag consistency
```

### 4. Cross-Reference Analysis

AI can analyze relationships between notes:

```
User: "How does the Alpha project relate to my Q1 goals?"
AI: Searches both topics, analyzes connections, provides insights
```

## Security Considerations

### Access Control

- The MCP server only provides read/write access to the specified vault
- No file system access outside the vault directory
- Cannot execute arbitrary commands or access system resources
- Limited to vault operations through defined tools

### Data Privacy

- All communication occurs locally via stdio (no network access)
- No data transmission to external services
- Vault content remains on your local machine
- AI assistant interactions depend on the specific client's privacy policy

### Best Practices

1. **Vault Backups**: Maintain regular backups before extensive AI interaction
2. **Review Changes**: Monitor AI-generated content for accuracy
3. **Configuration Security**: Protect configuration files with appropriate permissions
4. **Testing Environment**: Use a test vault when experimenting with new AI workflows

## Troubleshooting

### Common Issues

#### MCP Dependencies Not Found

```bash
# Install MCP dependencies
pip install mcp>=1.0.0
```

#### Vault Path Issues

```bash
# Verify vault path exists and is accessible
ls -la /path/to/your/vault

# Check configuration
obsidian-cli info
```

#### Permission Errors

```bash
# Ensure write permissions to vault directory
chmod -R u+w /path/to/your/vault
```

#### Server Connection Issues

```bash
# Test server startup with verbose logging
obsidian-cli --verbose serve
```

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
obsidian-cli --verbose serve
```

This provides detailed information about:

- Tool registrations
- Client connections
- Request processing
- Error details

### Log Analysis

Monitor server behavior through structured logging:

```bash
# Redirect logs to file for analysis
obsidian-cli --verbose serve 2> mcp-server.log

# Monitor in real-time
tail -f mcp-server.log
```

## Advanced Usage

### Custom Tool Integration

The MCP server architecture allows for future extension with additional tools. Current implementation focuses on core vault operations, with planned expansions for:

- Template management
- Tag operations
- Link analysis
- Backup creation
- Plugin integration

### Performance Optimization

For large vaults:

1. **Index Patterns**: Use blacklist to exclude large asset folders
2. **Search Optimization**: Use exact matching when possible
3. **Batch Operations**: Group related operations in single sessions
4. **Connection Reuse**: Maintain persistent MCP connections for frequent operations

### Integration Examples

#### Daily Workflow Automation

```python
# Example: AI-powered daily note creation
async def create_daily_note():
    today = datetime.now().strftime("%Y-%m-%d")
    content = f"""# Daily Note - {today}

## Today's Goals
- [ ]

## Notes

## Reflections
"""

    await session.call_tool("create_note", {
        "filename": f"daily-{today}",
        "content": content
    })
```

#### Research Assistant

```python
# Example: AI research compilation
async def research_topic(topic):
    # Find existing notes
    results = await session.call_tool("find_notes", {
        "term": topic,
        "exact": False
    })

    # Analyze and compile research
    research_note = compile_research(results)

    # Create summary note
    await session.call_tool("create_note", {
        "filename": f"research-{topic}-summary",
        "content": research_note
    })
```

## Future Enhancements

The MCP integration is actively developed with planned features including:

- **Template Tools**: Create notes from predefined templates
- **Metadata Operations**: Advanced frontmatter manipulation
- **Link Management**: Create and analyze note relationships
- **Export Tools**: Generate reports and summaries
- **Batch Operations**: Efficient bulk operations
- **Plugin Support**: Integration with Obsidian plugins

## Contributing

Contributions to MCP functionality are welcome! Areas for improvement:

- Additional tool implementations
- Performance optimizations
- Security enhancements
- Documentation improvements
- Integration examples

See [Contributing Guidelines](contributing.md) for development setup and contribution process.
