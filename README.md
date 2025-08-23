# Obsidian CLI

A command-line interface for interacting with an [Obsidian](https://obsidian.md) vault. This tool
allows you to create, manage, and organize your Markdown notes with YAML frontmatter, view vault
information, and work with journal entries.

## Installation

### From PyPI (Recommended, Future)

```bash
# Install from PyPI
pip install obsidian-cli
```

### From Source

```bash
# Clone the repository
git clone https://github.com/jwhonce/obsidian-cli.git
cd obsidian-cli

# Using the Makefile (recommended)
make dev

# OR manually:
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Usage

After installation, you can use the CLI in the following ways:

```bash
# Activate the virtual environment if not already active
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Show help information
obsidian-cli --help

# Show version information
obsidian-cli --version

# Enable verbose output
obsidian-cli --verbose info

# Display information about the Obsidian vault
obsidian-cli info

# Create a new note in the vault (automatically includes a unique ID)
obsidian-cli new "My New Note.md"

# Work with an existing journal entry
obsidian-cli journal

# Note: The journal command opens existing journal files only.
# Use 'new' command to create journal files first if they don't exist.
obsidian-cli new "Calendar/2025/08/2025-08-20"  # Create today's journal
obsidian-cli journal  # Then open it

# Edit any file in the vault with the configured editor
obsidian-cli edit "My Note.md"

# Add a unique ID to an existing note
obsidian-cli add_uid "Existing Note.md"

# Force replace an existing unique ID
obsidian-cli add_uid "Existing Note.md" --force

# View all frontmatter metadata in a file
obsidian-cli meta "My Note.md"

# View a specific metadata key in a file
obsidian-cli meta "My Note.md" title

# Update a metadata key in a file
obsidian-cli meta "My Note.md" tags "productivity, notes"

# Display the contents of a file (without frontmatter)
obsidian-cli cat "My Note.md"

# Display the contents of a file including frontmatter
obsidian-cli cat "My Note.md" --show-frontmatter

# Find files by page name (partial match)
obsidian-cli find "Meeting Notes"

# Find files by page name (exact match)
obsidian-cli find "Meeting Notes" --exact

# Remove a file from the vault
obsidian-cli rm "Unwanted Note.md"

# Remove a file from the vault without confirmation
obsidian-cli rm "Unwanted Note.md" --force

# Query frontmatter across the vault
obsidian-cli query tags --exists
obsidian-cli query status --value "published"
obsidian-cli query priority --missing
obsidian-cli query tags --exists --count
obsidian-cli query tags --contains "project" --format json
obsidian-cli query status --exists --format full
```

Once fully installed, you can also use the command directly:

```bash
# Show help information
obsidian-cli --help

# Enable verbose output
obsidian-cli -v info
obsidian-cli --verbose info

# Use any of the commands directly
obsidian-cli info
obsidian-cli new "My Note.md"
obsidian-cli edit "My Note.md"
obsidian-cli cat "My Note.md"
obsidian-cli meta "My Note.md"
obsidian-cli find "Meeting Notes"
obsidian-cli add-uid "My Note.md"
obsidian-cli rm "Unwanted Note.md"
obsidian-cli rm "Unwanted Note.md" --force
```

## Options

The CLI supports the following global options:

- `--config`: Path to an alternative configuration file
- `--vault`: Path to the Obsidian vault
- `--editor`: Text editor to use when opening journals
- `--verbose`, `-v`: Enable verbose output with detailed logging
- `--version`: Display the version number and exit

## Configuration

The CLI can be configured in multiple ways:

### Environment Variables

The CLI uses the following environment variables:

- `OBSIDIAN_VAULT`: Path to your Obsidian vault (required if not specified in config or command line)
- `EDITOR`: Text editor to use when opening files (defaults to 'vi')

You can set these permanently in your shell profile or specify them for each command:

```bash
# Set for the current session
export OBSIDIAN_VAULT="/path/to/your/vault"
export EDITOR="code"

# Or specify inline
OBSIDIAN_VAULT="/path/to/vault" obsidian-cli info
```

### Configuration File

You can also use a TOML configuration file. By default, the CLI looks for:

- `./obsidian-cli.toml` in the current directory, or
- `~/.config/obsidian-cli/config.toml` in your home directory

Or specify a custom path with the `--config` option:

```toml
# obsidian-cli.toml
vault = "~/path/to/vault"
editor = "vim"
verbose = false
ident_key = "uid"
ignored_directories = [
  ".obsidian/",
  ".git/",
  "Templates/"
]
journal_template = "Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}"
```

#### Configuration Options

- **vault**: Path to your Obsidian vault (required)
- **editor**: Text editor to use when opening files (defaults to 'vi')
- **verbose**: Enable verbose output (defaults to false)
- **ident_key**: Frontmatter key for unique identifiers (defaults to 'uid')
- **ignored_directories**: List of directory patterns to exclude from query operations. These patterns are matched against the beginning of relative file paths within the vault. Useful for excluding archived content, assets, templates, or system directories.
- **journal_template**: Template for journal file paths (defaults to 'Calendar/{year}/{month:02d}/{year}-{month:02d}-{day:02d}'). Supports variables: {year}, {month}, {month:02d}, {day}, {day:02d}, {month_name}, {month_abbr}, {weekday}, {weekday_abbr}

Command line arguments take precedence over environment variables, which take precedence over configuration file settings.

## Dependencies

This project uses:

- [Typer](https://typer.tiangolo.com/) - For building the CLI interface
- [Rich](https://rich.readthedocs.io/en/stable/) - For rich text and formatting in the terminal
- [Python-Frontmatter](https://github.com/eyeseast/python-frontmatter) - For parsing and manipulating YAML frontmatter in Markdown files
- [tomllib](https://docs.python.org/3/library/tomllib.html) - Built-in Python library for parsing TOML configuration files (Python 3.11+)
- [UUID](https://docs.python.org/3/library/uuid.html) - Standard library module for generating unique IDs
- [MDUtils](https://github.com/didix21/mdutils) - For markdown file creation and formatting

## Development

### Using the Makefile

The project includes a Makefile with several useful targets:

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

# Format the code with Ruff
make ruff-format

# Format and lint code with Ruff (recommended)
make ruff

# Generate documentation
make docs

# Serve documentation locally
make docs-serve

# Check for outdated dependencies
make outdated

# Update version number
make version VERSION=1.2.3

# Complete release workflow
make release VERSION=1.2.3

# Publish to PyPI
make publish

# Clean build artifacts and test files
make clean

# Clean only test-related files
make clean-tests

# Run all (clean, build, dev)
make
```

### Manual Development

```bash
# Run tests
pytest tests/
```

## Development Status

**Current Version**: 0.1.8 (Stable)

This project is now fully version controlled with Git and hosted on GitHub at [jwhonce/obsidian-cli](https://github.com/jwhonce/obsidian-cli). The development follows semantic versioning and maintains a comprehensive test suite.

### Project Milestones

- ✅ **Initial Release (v0.1.8)**: Core CLI functionality implemented
- ✅ **Comprehensive Testing**: 76 unit tests with full coverage
- ✅ **Configuration System**: Frozen dataclass with TOML support
- ✅ **Git Integration**: Repository initialized with proper .gitignore
- ✅ **GitHub Hosting**: Public repository with complete documentation
- ✅ **Build Infrastructure**: Makefile with development, testing, and packaging targets
- ✅ **Code Quality**: Linting with Ruff, proper error handling

### Current Status

- **Functionality**: All 9 CLI commands working correctly (info, new, edit, meta, journal, query, cat, rm, add-uid, find)
- **Testing**: 76/76 tests passing consistently
- **Code Quality**: Clean codebase with comprehensive error handling and validation
- **Documentation**: Complete README with usage examples and development instructions
- **Repository**: Clean Git history with conventional commit messages

### Recent Updates

- **August 23, 2025**: Repository published to GitHub with comprehensive documentation
- **August 23, 2025**: Enhanced Makefile clean-tests target for comprehensive artifact removal
- **August 23, 2025**: Fixed critical UnboundLocalError bug in ignored_dirs_list handling
- **August 23, 2025**: Added comprehensive Configuration class with TOML support and 10 new unit tests

### Repository Information

- **Repository**: [jwhonce/obsidian-cli](https://github.com/jwhonce/obsidian-cli)
- **License**: MIT (see LICENSE file)
- **Issues**: Report bugs and feature requests on GitHub
- **Contributions**: Welcome via pull requests (see docs/contributing.md)

### Next Steps

- [ ] **PyPI Publishing**: Prepare for public distribution
- [ ] **CI/CD Pipeline**: Set up GitHub Actions for automated testing
- [ ] **Documentation**: Generate API documentation
- [ ] **Feature Enhancements**: Based on user feedback and requirements
- [ ] **Performance Optimization**: Profile and optimize for large vaults

## AI-Assisted Development

This project was developed with significant assistance from **GitHub Copilot**, demonstrating the powerful capabilities of AI-assisted software development. Here's how Copilot contributed to the project:

### Code Generation and Implementation

- **Core CLI Structure**: Copilot helped generate the initial Typer-based CLI framework and command structure
- **Configuration System**: Assisted in creating the frozen dataclass Configuration system with TOML file support
- **Command Implementations**: Generated boilerplate and logic for all CLI commands (find, new, edit, meta, journal, query, cat, rm, add-uid)
- **Error Handling**: Helped implement comprehensive error handling patterns throughout the application

### Testing and Quality Assurance

- **Comprehensive Test Suite**: Copilot generated 76 comprehensive unit tests covering all functionality
- **Test Patterns**: Created consistent testing patterns and helper methods for test simplification
- **Edge Case Coverage**: Identified and implemented tests for edge cases and error conditions
- **Configuration Testing**: Generated thorough tests for the Configuration class including file loading, type conversion, and validation

### Build and Development Infrastructure

- **Makefile Targets**: Created comprehensive Makefile with development, testing, and packaging targets
- **Package Configuration**: Assisted with pyproject.toml setup including dependencies, build system, and tool configurations
- **Git Integration**: Helped set up proper .gitignore patterns and repository structure
- **Documentation**: Generated comprehensive README with usage examples and development instructions

### Code Quality and Maintenance

- **Bug Detection and Fixes**: Identified and fixed critical bugs (e.g., UnboundLocalError in ignored_dirs_list)
- **Code Refactoring**: Assisted in improving code structure and maintainability
- **Linting Configuration**: Set up Ruff configuration with appropriate excludes and formatting rules
- **Version Management**: Helped coordinate version updates across multiple files

### Development Workflow

- **Project Structure**: Organized codebase into logical modules and directories
- **Dependency Management**: Identified and configured appropriate Python dependencies
- **Virtual Environment Setup**: Created proper development environment configuration
- **Package Distribution**: Set up wheel and source distribution packaging

### Key Benefits Observed

1. **Rapid Prototyping**: Accelerated initial development from concept to working CLI
2. **Comprehensive Testing**: Achieved high test coverage with minimal manual test writing
3. **Best Practices**: Applied Python packaging and development best practices consistently
4. **Documentation Quality**: Generated thorough, accurate documentation and examples
5. **Error Prevention**: Caught potential issues before they became problems

This project serves as an example of how AI-assisted development can significantly accelerate software creation while maintaining high code quality, comprehensive testing, and professional development practices.
