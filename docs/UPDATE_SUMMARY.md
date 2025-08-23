# Obsidian CLI - Documentation Update (August 2025)

The documentation for the Obsidian CLI project has been updated to reflect version 0.1.3. The following changes have been made:

## Build System Changes

- Replaced build.sh and publish.sh scripts with a comprehensive Makefile
- Added targets for build, test, clean, dev, install, and publish operations
- Updated documentation to reference the Makefile for development tasks

## Updates to Existing Documentation

1. **changes.md**

   - Added documentation for version 0.1.3 changes
   - Added documentation for version 0.1.2 changes
   - Reorganized change history in chronological order

2. **commands.md**

   - Added documentation for the `--force` option in the `new` command
   - Updated the description of the `query` command options for better clarity
   - Improved consistency in command documentation

3. **index.md**

   - Added "Force Options" to the Table of Contents
   - Added "Force options for advanced operations and automation" to Key Features

4. **README.md**
   - Updated GitHub repository URL from placeholder to actual URL
   - Updated usage examples to use `obsidian-cli` instead of `python -m src.main`

## New Documentation

1. **force-options.md**
   - Created comprehensive documentation about force options in various commands
   - Added best practices for using force options
   - Included safety considerations for data manipulation

## Documentation Structure

The documentation structure now includes:

1. `index.md` - Overview and quick start guide
2. `installation.md` - Detailed installation instructions
3. `configuration.md` - Configuration options and methods
4. `commands.md` - Complete command reference with options
5. `force-options.md` - Documentation on force flags and data safety
6. `contributing.md` - Guidelines for contributing to the project
7. `changes.md` - Recent changes and future plans

These updates ensure the documentation accurately reflects the current state of the project, including the new features in version 0.1.3.
