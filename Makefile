# Makefile for REST Client Prototype

# Variables
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYINSTALLER = $(VENV_DIR)/bin/pyinstaller
PYTEST = $(VENV_DIR)/bin/pytest
SPEC_FILE = rest_client.spec
DIST_DIR = dist
BUILD_DIR = build
TARGET_NAME = rest_client
TARGET_BIN = $(DIST_DIR)/$(TARGET_NAME)/$(TARGET_NAME)
VERSION := $(shell PYTHONPATH=. $(PYTHON) -c "import app; print(app.__version__)" 2>/dev/null || echo "0.1.0")
ARCHIVE_NAME = $(TARGET_NAME)-v$(VERSION)-linux-x86_64.tar.gz

.PHONY: all install build clean run run-dist archive test help

# Default target
all: build

# Install dependencies
install:
	$(PIP) install -r requirements.txt
	$(PIP) install pyinstaller

# Run tests
test:
	PYTHONPATH=. $(PYTEST) tests

# Build the application using PyInstaller
build:
	$(PYINSTALLER) --clean --noconfirm $(SPEC_FILE)

# Create a compressed archive for distribution
archive: build
	@echo "Creating archive $(ARCHIVE_NAME)..."
	tar -czvf $(DIST_DIR)/$(ARCHIVE_NAME) -C $(DIST_DIR) $(TARGET_NAME)
	@echo "Archive created: $(DIST_DIR)/$(ARCHIVE_NAME)"

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run application from source
run:
	$(PYTHON) -m app.main

# Run the built application
run-dist:
	@if [ -f $(TARGET_BIN) ]; then \
		$(TARGET_BIN); \
	else \
		echo "Binary not found. Run 'make build' first."; \
		exit 1; \
	fi

# Show help
help:
	@echo "Available targets:"
	@echo "  install   - Install dependencies (including PyInstaller)"
	@echo "  build     - Build the application using PyInstaller"
	@echo "  archive   - Create a tar.gz archive for distribution"
	@echo "  test      - Run unit tests using pytest"
	@echo "  clean     - Remove build artifacts (build/, dist/, __pycache__)"
	@echo "  run       - Run the application from source code"
	@echo "  run-dist  - Run the built binary"
	@echo "  help      - Show this help message"
