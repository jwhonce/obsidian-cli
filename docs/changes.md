# Recent Changes

This document lists the significant recent changes to obsidian-cli.

## Version 0.1.9

### Added

- **MCP (Model Context Protocol) server**: New `serve` command that starts an MCP server for AI assistant integration
- MCP server exposes vault operations as standardized tools for AI assistants
- Available MCP tools: create_note, find_notes, get_note_content, get_vault_info
- Server runs over stdio using the MCP protocol until interrupted

### Changed

- Moved `serve` command to alphabetical position with other CLI commands in the source code
- Updated documentation to include comprehensive MCP server information
- Enhanced command reference with detailed serve command documentation

## Version 0.1.7

### Changed

- Updated documentation across all files to reflect current functionality
- Enhanced module docstring with comprehensive command descriptions and examples
- Improved configuration documentation with detailed journal template examples
- Updated README.md with current usage patterns and configuration options

### Added

- Comprehensive documentation for journal template variables and examples
- Enhanced command reference documentation in docs/commands.md
- Updated configuration guide with journal template configuration

## Version 0.1.6

### Changed

- **Journal command behavior**: Removed the `--create/--no-create` option from the journal command
- Journal command now only opens existing journal files and exits with an error if the file doesn't exist
- Users must create journal files manually using the `new` command before opening them with `journal`
- Improved boolean flag patterns across CLI commands using `--flag/--no-flag` syntax
- Enhanced CLI user experience with consistent flag handling

### Removed

- `--create` and `--no-create` options from the journal command
- Automatic journal file creation functionality

## Version 0.1.5

### Fixed

- **Version command compatibility**: Fixed version detection for wheel-installed packages
- Added dynamic version resolution using `importlib.metadata` with fallback strategies
- Version command now works correctly in both development and production installations

### Changed

- Enhanced version detection system with multiple fallback mechanisms
- Improved package metadata handling for different installation methods

## Version 0.1.4

### Changed

- **Configuration format migration**: Converted from YAML to TOML configuration files
- Updated configuration file names from `obsidian-cli.yaml` to `obsidian-cli.toml`
- Updated default configuration paths to use `.toml` extensions
- Replaced PyYAML dependency with Python's built-in `tomllib` library (Python 3.11+)
- Updated all documentation to reflect TOML usage instead of YAML
- Configuration examples now use TOML syntax

### Removed

- PyYAML dependency from requirements.txt and pyproject.toml
- Support for YAML configuration files

## Version 0.1.3

### Added

- Force option (`--force` or `-f`) to the `new` command to allow overwriting existing files
- **Configurable directory filtering**: Added `ignored_directories` configuration option to exclude specific directories from query operations
- Consistent type annotation with `PAGE_FILE` type used across all commands
- Improved help text clarity for query command options
- Makefile for simplified build, development, testing, and publishing
- Unit testing framework with dedicated unit test directory
- Code linting and formatting targets in Makefile
- Test coverage reporting with HTML output
- Clean targets for test artifacts
- Documentation generation with MkDocs
- Version management and release workflow targets
- Dependency update checking
- Comprehensive help output for all Makefile targets
- Ruff integration for fast Python linting and formatting
- Configuration for modern Python development practices in pyproject.toml

### Changed

- Replaced build.sh and publish.sh scripts with a comprehensive Makefile
- **Query command**: Now respects configurable ignored directories instead of hardcoded exclusions

### Removed

- Removed obsolete build.sh and publish.sh shell scripts

### Changed

- Updated version number to 0.1.3
- Improved documentation and help text clarity

## Version 0.1.2

### Added

- Apache 2.0 license replacing MIT license
- VS Code debugger configuration
- Improved error handling

### Changed

- Updated version number to 0.1.2
- Refactored code structure for better maintainability

## Version 0.1.1

### Added

- Comprehensive documentation in the docs/ directory
- Detailed command reference documentation
- Installation and configuration guides

### Changed

- Updated version number to 0.1.1
- Improved README with configuration details
- Enhanced documentation for force flag in rm command

## Version 0.1.0

### Added

- Force flag to the `rm` command to skip confirmation prompt (`--force` or `-f`)
- Custom YAML configuration file support
- PyYAML as a dependency for configuration parsing
- Command sorting for better maintainability
- Improved help documentation for CLI commands

### Changed

- Removed dependency on typer-config
- Implemented manual configuration loading using PyYAML
- Reorganized methods in main.py alphabetically
- Updated command documentation and help texts
- Enhanced force flag functionality in add-uid command

### Fixed

- Improved error handling for missing configuration
- Updated dependencies in setup.py and requirements.txt
- Added MANIFEST.in to include obsidian-cli.yaml in package

## Future Plans

- Add support for additional frontmatter operations
- Implement backup functionality
- Add support for template-based note creation
- Enhance search capabilities
