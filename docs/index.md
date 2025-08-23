# Obsidian CLI Documentation

Welcome to the documentation for obsidian-cli, a command-line interface for interacting with Obsidian vaults.

## Overview

obsidian-cli is a Python package that provides a set of command-line tools to interact with Obsidian vaults. It facilitates tasks such as creating notes, editing content, querying metadata, and managing files from the terminal.

## Table of Contents

1. [Installation](installation.md) - How to install obsidian-cli
2. [Configuration](configuration.md) - How to configure obsidian-cli
3. [Commands](commands.md) - Detailed reference for all available commands
4. [Force Options](force-options.md) - Documentation on force flags and data safety
5. [Contributing](contributing.md) - Guidelines for contributing to the project

## Key Features

- Create and edit markdown files with proper frontmatter
- Query files based on frontmatter metadata
- View and update metadata in existing files
- Add unique IDs to files
- Access journal entries
- Display information about the vault
- Configuration via environment variables and configuration files
- Force options for advanced operations and automation
- MCP (Model Context Protocol) server for AI assistant integration

## Quick Start

```bash
# Install the package
pip install obsidian-cli

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
