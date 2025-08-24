# Installation Guide

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- An Obsidian vault you want to manage

## Installing from PyPI

The recommended way to install obsidian-cli is through PyPI:

```bash
# Standard installation
pip install obsidian-cli

# Installation with MCP support for AI assistant integration
pip install obsidian-cli[mcp]
```

The `[mcp]` extra installs additional dependencies required for the MCP (Model Context Protocol) server functionality.

### Installation Options

- **Standard**: `pip install obsidian-cli` - Core CLI functionality only
- **Full with MCP**: `pip install obsidian-cli[mcp]` - Includes MCP server for AI assistant integration
- **Development**: `pip install obsidian-cli[dev]` - Includes development dependencies for contributing

### MCP Dependencies

If you installed the standard version and later want to add MCP support:

```bash
pip install mcp>=1.0.0
```

This will install the required Model Context Protocol dependencies for AI assistant integration.

## Installing from Source

For development purposes or to get the latest unreleased features, you can install from source:

```bash
# Clone the repository
git clone https://github.com/yourusername/obsidian-cli.git
cd obsidian-cli

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Verifying Installation

After installation, you can verify that the tool was installed correctly:

```bash
# Check version
obsidian-cli --version

# Verify core functionality
obsidian-cli --help

# Test MCP server availability (if MCP dependencies are installed)
obsidian-cli serve --help
```

### MCP Installation Verification

To verify that MCP dependencies are properly installed:

```bash
# Test MCP server startup (will show help if dependencies are missing)
obsidian-cli --vault /path/to/test/vault serve --help

# Check if MCP module is available
python -c "import mcp; print('MCP dependencies installed successfully')"
```

If MCP dependencies are missing, you'll see an error message with installation instructions.

This should display the current version of the tool.

## Configuration After Installation

After installing the tool, you have several options for configuration:

1. Use the `--vault` flag to specify your Obsidian vault path with each command
2. Set the `OBSIDIAN_VAULT` environment variable
3. Create a configuration file (see the Configuration section)

For example:

```bash
# Set up configuration file
echo 'vault = "~/Documents/ObsidianVault"' > obsidian-cli.toml

# Test the configuration
obsidian-cli info
```
