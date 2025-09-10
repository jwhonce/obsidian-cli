# Installation Guide

## Prerequisites

- Python 3.11 or higher (required for TOML support)
- pip (Python package installer)
- An Obsidian vault you want to manage

## Installing from PyPI

The recommended way to install obsidian-cli is through PyPI:

```bash
# Standard installation (includes MCP support)
pip install obsidian-cli
```

The standard installation includes all necessary dependencies including MCP (Model Context Protocol) support for AI assistant integration.

### Installation Options

- **Standard**: `pip install obsidian-cli` - Complete functionality including MCP server
- **Development**: `pip install -e .` - Development installation from source

### Dependencies Included

The standard installation includes:

- Core CLI functionality
- MCP server for AI assistant integration  
- TOML configuration support
- Frontmatter parsing
- Rich terminal output
- All testing dependencies

## Installing from Source

For development purposes or to get the latest unreleased features, you can install from source:

```bash
# Clone the repository
git clone https://github.com/jhonce/obsidian-cli.git
cd obsidian-cli

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode (includes all dependencies)
pip install -e .

# Alternatively, use the Makefile for development setup
make dev
```

## Verifying Installation

After installation, you can verify that the tool was installed correctly:

```bash
# Check version (should show v0.1.14)
obsidian-cli --version

# Verify core functionality
obsidian-cli --help

# Test MCP server availability
obsidian-cli serve --help
```

### Installation Verification

To verify that all components are properly installed:

```bash
# Test with a sample vault (create a test directory)
mkdir -p /tmp/test-vault
obsidian-cli --vault /tmp/test-vault info

# Verify MCP server can start
obsidian-cli --vault /tmp/test-vault serve --help

# Check test coverage (for development installations)
make coverage  # if installed from source
```

This should display version 0.1.14 and show no errors.

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
