# Contributing to Obsidian CLI

Thank you for your interest in contributing to obsidian-cli! This document provides guidelines and
instructions for contributing to the project.

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally

   ```bash
   git clone https://github.com/your-username/obsidian-cli.git
   cd obsidian-cli
   ```

3. Set up the development environment using the Makefile (recommended)

   ```bash
   make dev
   ```

   Or manually:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

## Code Organization

The project structure is organized as follows:

```
obsidian-cli/
├── docs/               # Documentation
├── src/
│   └── obsidian_cli/   # Main package
│       ├── __init__.py
│       ├── configuration.py    # Configuration class and TOML loading
│       ├── exceptions.py       # Custom exception classes
│       ├── main.py            # CLI commands and Vault management
│       ├── mcp_server.py      # MCP server functionality
│       └── utils.py           # Utility functions
├── tests/              # Test files
├── Makefile            # Build automation
├── obsidian-cli.toml   # Example configuration
├── README.md
├── pyproject.toml      # Package metadata
└── MANIFEST.in         # Package files inclusion
```

The functionality is distributed across multiple modules:

- **`main.py`**: CLI commands and Vault management
- **`configuration.py`**: Configuration class with TOML file loading and validation
- **`exceptions.py`**: Project-specific exception classes (ObsidianFileError)
- **`utils.py`**: Utility functions for file operations, display, and vault management
- **`mcp_server.py`**: Model Context Protocol server functionality

## Coding Style

- Follow PEP 8 guidelines
- Use type hints to improve readability and enable static type checking
- Write docstrings for all public functions, classes, and methods
- Keep CLI commands in alphabetical order for better maintainability
- Keep helper functions in alphabetical order in their own section

## Using the Makefile

The project includes a Makefile to simplify common development tasks:

```bash
# Show available targets
make help

# Install in development mode
make dev

# Build the package
make build

# Run tests
make test

# Run unit tests only
make unittest

# Generate code coverage report
make coverage

# Lint the code
make lint

# Format the code with Black
make format

# Generate documentation
make docs

# Serve documentation locally
make docs-serve

# Check for outdated dependencies
make outdated

# Update version number (maintainers only)
make version VERSION=1.2.3

# Complete release workflow (maintainers only)
make release VERSION=1.2.3

# Publish to PyPI (maintainers only)
make publish

# Clean build artifacts and test files
make clean

# Clean only test-related files
make clean-tests

# Run all (clean, build, dev)
make all
```

## Testing

1. Write tests for new functionality:
   - Integration tests in `tests/`
   - Unit tests in `tests/unit/`

2. Run the tests using the Makefile:

   ```bash
   # Run all tests
   make test

   # Run only unit tests
   make unittest

   # Generate test coverage report
   make coverage
   ```

3. Check code style:

   ```bash
   # Lint the code with Ruff
   make lint

   # Format the code with Black
   make format

   # Format the code with Ruff
   make ruff-format

   # Format and lint code with Ruff (recommended)
   make ruff
   ```

   Or manually:

   ```bash
   pytest tests/
   ```

## Pull Request Process

1. Make your changes in a new git branch
2. Follow the coding style guidelines
3. Add tests for your changes
4. Run the tests to ensure they pass
5. Update the documentation as needed
6. Submit a pull request

## Documentation

When adding new features or making changes, please update:

1. Function and method docstrings
2. Command help text
3. The relevant documentation files in the `docs/` directory
4. The README.md if necessary

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## License

By contributing your code, you agree to license your contribution under the same license as the
project.
