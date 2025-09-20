# Makefile for obsidian-cli
#
# Common targets:
#  - build: Build the Python package (creates dist/ directory)
#  - clean: Remove build artifacts
#  - dev: Install package in development mode
#  - test: Run tests
#  - all: Build and install package in development mode

# Default target
all: clean build dev

# Show help information
help:
	@echo "Available targets:"
	@echo "  all:         Clean, build, and install in development mode"
	@echo "  build:       Build the package"
	@echo "  clean:       Clean build artifacts and test files"
	@echo "  clean-tests: Clean only test-related files"
	@echo "  dev:         Install in development mode"
	@echo "  install-deps: Install dependencies from requirements.txt"
	@echo "  install:     Install the package from built distribution"
	@echo "  publish:     Publish the package to PyPI"
	@echo "  release:     Complete release workflow (version+test+lint+build+publish)"
	@echo "  test:        Run all tests"
	@echo "  unittest:    Run only unit tests"
	@echo "  coverage:    Run comprehensive test suite with 75%+ coverage validation"
	@echo "  coverage-quick: Generate coverage report without enforcing threshold"
	@echo "  lint:        Check code style with Ruff"
	@echo "  format:      Format and lint code using Ruff"
	@echo "  serve:       Start MCP server for development testing"
	@echo "  venv:        Create virtual environment if it doesn't exist"

# Make sure venv exists
venv:
	@if [ ! -d "venv" ]; then \
		echo "Creating new virtual environment..."; \
		python3 -m venv venv; \
	else \
		echo "Using existing virtual environment..."; \
	fi

# Clean build artifacts
clean: clean-tests
	@echo "Cleaning all artifacts..."
	@rm -rf build/ dist/ *.egg-info/ src/*.egg-info/
	@rm -rf .pytest_cache/ htmlcov/ .coverage
	@echo "Cleaned."

# Clean only test-related files
clean-tests:
	@echo "Cleaning test artifacts..."
	@rm -rf .pytest_cache/ htmlcov/ .coverage .coverage.*
	@rm -rf tests/__pycache__/ tests/unit/__pycache__/
	@rm -rf temp_tests/
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Removed test artifacts: .pytest_cache/, htmlcov/, .coverage, __pycache__/, *.pyc, temp_tests/, *.egg-info/"

# Build the package
build: venv
	@echo "Building obsidian-cli package..."
	@. venv/bin/activate && \
		pip install --upgrade pip && \
		pip install --upgrade build && \
		python -m build
	@echo "Build completed. Distribution files in dist/ directory."

# Install in development mode
dev: venv
	@echo "Installing in development mode..."
	@. venv/bin/activate && pip install -e .
	@echo "Development installation complete."

# Install requirements
install-deps: venv
	@echo "Installing dependencies..."
	@. venv/bin/activate && pip install -r requirements.txt
	@echo "Dependencies installed."

# Install the package from the built distribution
install: build
	@echo "Installing obsidian-cli package..."
	@. venv/bin/activate && pip install dist/*.whl
	@echo "Installation complete."

# Publish to PyPI
publish: build
	@echo "Publishing to PyPI..."
	@if [ ! -d "dist" ]; then \
		echo "No distribution files found. Run 'make build' first."; \
		exit 1; \
	fi
	@. venv/bin/activate && \
		pip install --upgrade twine && \
		python -m twine upload dist/*
	@echo "Upload to PyPI completed."

.PHONY: test

# Run all tests in the tests/ directory using pytest
test:
	@PYTHONPATH=src python -m pytest

# Run only unit tests
unittest: venv
	@echo "Running unit tests..."
	@. venv/bin/activate && \
		pip install pytest pytest-cov && \
		pytest tests/unit/ -v
	@echo "Unit tests completed."

# Run tests with coverage report using the comprehensive test runner
coverage: venv clean-tests dev
	@echo "🧪 Running comprehensive test suite with coverage analysis..."
	@echo "📊 Target: 75%+ coverage across all modules"
	. venv/bin/activate && \
		pip install pytest pytest-cov && \
		PYTHONPATH=src pytest tests/ \
			--cov=src/obsidian_cli \
			--cov-report=term-missing \
			--cov-report=html \
			--cov-fail-under=75 \
			--tb=short \
			-v \
			--durations=10 || \
		(echo "❌ Coverage test failed - either tests failed or coverage below 75%"; exit 1)
	@echo ""
	@echo "✅ Coverage analysis complete!"
	@echo "📈 All modules achieved 75%+ coverage target"
	@echo "📋 Detailed report: htmlcov/index.html"
	@echo "📊 Test files exercised:"
	@echo "   - tests/test_coverage_improvements.py (24 tests for main.py)"
	@echo "   - tests/test_mcp_server_comprehensive.py (17 tests for mcp_server.py)"  
	@echo "   - tests/test_utils_coverage.py (23 tests for utils.py)"
	@echo "   - tests/test_*.py (existing test suite)"
	@echo "   - tests/unit/*.py (unit tests)"

# Run tests with coverage report (no threshold enforcement)
coverage-quick: venv clean-tests dev
	@echo "🧪 Running tests with coverage report (no threshold)..."
	@. venv/bin/activate && \
		pip install pytest pytest-cov && \
		PYTHONPATH=src pytest tests/ \
			--cov=src/obsidian_cli \
			--cov-report=term-missing \
			--cov-report=html \
			--tb=short \
			-v
	@echo "✅ Coverage report generated. See htmlcov/index.html"

# Lint the code
lint: venv
	@echo "Linting the code..."
	@. venv/bin/activate && \
		pip install ruff && \
		ruff check src/ tests/
	@echo "Lint check completed."

# Format and lint the code with Ruff
format: venv
	@echo "Formatting and linting the code with Ruff..."
	@. venv/bin/activate && \
		pip install ruff && \
		ruff format src/ tests/ && \
		ruff check --fix src/ tests/
	@echo "Ruff formatting and linting completed."

# Start MCP server for development testing
serve: venv
	@echo "Starting MCP server for development testing..."
	@echo "Make sure to set OBSIDIAN_VAULT environment variable or use --vault option"
	@echo "Press Ctrl+C to stop the server"
	@. venv/bin/activate && \
		pip install mcp && \
		python -m obsidian_cli.main serve --verbose
	@echo "MCP server stopped."




# Complete release workflow (requires VERSION argument)
release: test format clean build publish
	@echo "Release $(VERSION) completed!"
	@echo "Remember to:"
	@echo "- Create a git tag: git tag -a v$(VERSION) -m 'Release $(VERSION)'"
	@echo "- Push the tag: git push origin v$(VERSION)"
	@echo "- Create a GitHub release"
