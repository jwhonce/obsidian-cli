# Recent Changes

This document lists the significant recent changes to obsidian-cli.

## Version 0.1.20

### Added
- Added comprehensive tests for typer environment variable prefix functionality
- Added tests to verify OBSIDIAN_* environment variables work correctly for all CLI options

### Fixed  
- Fixed failing tests after _display_find_results() cleanup
- Fixed test imports to use new types.py structure

### Changed
- Cleaned up _display_find_results() function for better maintainability
- Updated all test files to import Configuration and State from types.py

---

## Version 0.1.19

### Enhanced Features

- **Comprehensive File Type Statistics**: MCP server now returns detailed statistics for all file types in the vault, not just markdown files
  - Tracks count and total size for each file extension (.md, .json, .txt, .png, .pdf, etc.)
  - Handles files without extensions as "no_extension" category
  - Maintains backward compatibility with existing `markdown_files` field
- **Improved File Size Display**: Fixed file size formatting in vault info output
  - Displays appropriate units (bytes, KB, MB, GB) instead of always showing "0.00 MB"
  - Accurate size calculation for small files

### Performance Optimizations

- **Optimized `_get_vault_info` Function**: Significantly improved performance for large vaults
  - Single-pass file processing eliminates redundant filesystem operations
  - Direct file type processing during iteration reduces memory usage
  - Uses `contextlib.suppress()` for cleaner exception handling
- **Reduced Processing Overhead**: File extension cleanup and categorization now happen during initial scan

### Code Quality Improvements

- **PEP 8 Compliance**: Formatted `mcp_server.py` to limit line length to <100 characters
  - Split long f-strings and JSON schema definitions for better readability
  - Improved function parameter formatting across multiple lines
- **Import Organization**: Moved all imports to the top of files following Python best practices
  - Resolved circular import issues between `mcp_server.py` and `main.py`
  - Maintained proper import ordering (standard library, third-party, local imports)
- **Method Organization**: Sorted method names alphabetically in both `utils.py` and `mcp_server.py`
  - Improved code maintainability and navigation
  - Consistent ordering ignores leading underscores for private functions

### Testing Improvements

- **Fixed Hanging Tests**: Resolved infinite loop issues in MCP server comprehensive tests
  - Modified `serve_mcp` tests to verify function properties without executing the server
  - Corrected mock patch targets for proper test isolation
- **Enhanced Test Coverage**: Added comprehensive tests for new file type statistics functionality
  - Tests validate diverse file types including edge cases (files without extensions)
  - Verification of size calculation accuracy across different file sizes

### Bug Fixes

- **File Size Calculation**: Fixed display of file sizes that were previously showing as 0
  - Proper handling of small files with accurate byte-level precision
  - Consistent size reporting across all file types
- **Exception Handling**: Improved error handling with `contextlib.suppress()` for file operations
  - Graceful handling of file access issues during vault scanning
  - Prevents crashes when encountering inaccessible files or directories

### Backward Compatibility

- **Maintained API Compatibility**: All existing MCP server tool interfaces remain unchanged
- **Legacy Support**: Existing `markdown_files` field preserved in vault info output
- **Configuration Compatibility**: No changes required to existing configuration files

### Developer Experience

- **Improved Code Documentation**: Enhanced inline comments and function documentation
- **Better Error Messages**: More descriptive error handling for common issues
- **Consistent Code Style**: Applied uniform formatting standards across the codebase

## Version 0.1.14

### Added

- **Comprehensive Test Suite**: Achieved 78% test coverage with 117 tests
- **Enhanced Test Infrastructure**: Added extensive test coverage for all major components
  - `tests/test_coverage_improvements.py` - 24 tests covering main.py functionality
  - `tests/test_mcp_server_comprehensive.py` - 17 tests covering MCP server functionality
  - `tests/test_utils_coverage.py` - Additional tests for utils module
- **Improved Makefile**: Enhanced coverage target with 75% threshold enforcement
- **Robust Error Handling**: Fixed stderr capture issues across all test files
- **Cross-platform Compatibility**: Tests now work consistently across different environments

### Changed

- **Import Organization**: All imports moved to top of files following Python best practices
- **Linting Improvements**: Fixed deprecated `logger.warn()` calls to use `logger.warning()`
- **Code Quality**: Merged nested if statements for better readability
- **Test Reliability**: Fixed date-dependent tests and assertion mismatches

### Fixed

- **Test Failures**: Resolved 4 failing tests related to stderr capture
- **Coverage Reporting**: Fixed inconsistent coverage calculations between different execution
  methods
- **CLI Runner Issues**: Updated test framework to work with current typer version

## Version 0.1.12

### Changed

- The CLI now uses default settings instead of raising an error when no configuration file is found.
  The `--vault` option is required in this case.

## Version 0.1.9

### Added

- **MCP (Model Context Protocol) server**: New `serve` command that starts an MCP server for AI
  assistant integration
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
- Journal command now only opens existing journal files and exits with an error if the file doesn't
  exist
- Users must create journal files manually using the `new` command before opening them with
  `journal`
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
- **Configurable directory filtering**: Added `ignored_directories` configuration option to exclude
  specific directories from query operations
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
