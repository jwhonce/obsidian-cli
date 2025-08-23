# Installation Guide

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- An Obsidian vault you want to manage

## Installing from PyPI

The recommended way to install obsidian-cli is through PyPI:

```bash
pip install obsidian-cli
```

This will install the latest stable version of the package and all its dependencies.

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
obsidian-cli --version
```

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
