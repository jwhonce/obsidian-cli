# Obsidian CLI Documentation

Welcome to the documentation for obsidian-cli, a command-line interface for interacting with Obsidian vaults.

## Overview

obsidian-cli is a Python package that provides a set of command-line tools to interact with Obsidian vaults. It facilitates tasks such as creating notes, editing content, querying metadata, and managing files from the terminal.

## Table of Contents

1. [Installation](installation.md) - How to install obsidian-cli
2. [Configuration](configuration.md) - How to configure obsidian-cli
3. [Commands](commands.md) - Detailed reference for all available commands
4. [MCP Integration](mcp-integration.md) - Model Context Protocol server for AI assistant integration
5. [Force Options](force-options.md) - Documentation on force flags and data safety
6. [Contributing](contributing.md) - Guidelines for contributing to the project

## Key Features

- **Create and edit** markdown files with proper frontmatter management
- **Query and search** files based on frontmatter metadata and content
- **Metadata management** - view and update YAML frontmatter in existing files
- **Unique ID generation** - add UUIDs to files for consistent referencing
- **Journal integration** - quick access to daily notes with template support
- **Vault information** - comprehensive vault statistics and configuration details
- **Flexible configuration** - TOML config files with environment variable support
- **Force options** - advanced operations and automation capabilities
- **AI Integration** - Production-ready MCP server for seamless AI assistant integration

## Quick Start

```bash
# Install the package with MCP support
pip install obsidian-cli[mcp]

# Configure your vault path
export OBSIDIAN_VAULT="/path/to/your/vault"

# Show information about your vault
obsidian-cli info

# Create a new note
obsidian-cli new "My New Note"

# Edit the note
obsidian-cli edit "My New Note"

# Query for notes with a specific tag
obsidian-cli query tags --contains "project"

# Start MCP server for AI assistant integration
obsidian-cli serve
```

## Project Status

obsidian-cli is under active development. Check the GitHub repository for the latest updates and features.
