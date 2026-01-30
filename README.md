# REST Client Prototype

A desktop REST API client built with Python 3.14 and PySide6 (Qt for Python).
Designed for Rocky Linux 9 environments.

## Features

- **Collection Management**: Organize requests in collections and folders.
- **Request Editor**: Support for GET, POST, PUT, DELETE, PATCH, and more.
  - Headers, Params, Body (JSON, Text), Auth (Basic, Bearer).
  - **File Upload**: Multipart/Form-data support for uploading files.
- **Response Viewer**: View status, elapsed time, headers, and body.
- **Environment Management**: Global variables and variable substitution (e.g., `{{base_url}}`).
- **Workspace Support**: Save and load workspaces to/from JSON files (Atomic write).
- **History**: Local history of executed requests saved in JSONL format.
- **Wayland Support**: Optimized dialog handling (overlay) for Wayland environments.

## Requirements

- **OS**: Rocky Linux 9 (x86_64)
- **Python**: 3.14+
- **GUI Framework**: PySide6 6.10.1+

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd kkj_restclient
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.14 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   make install
   # or manually:
   pip install -r requirements.txt
   pip install pyinstaller
   ```

## Usage

### Running from Source

To run the application directly from the source code:

```bash
make run
# or manually:
python -m app.main
```

### Building for Distribution

To build a standalone executable using PyInstaller:

```bash
make build
```
The executable will be generated at `dist/rest_client/rest_client`.

### Creating a Release Archive

To build and package the application into a `.tar.gz` archive for distribution:

```bash
make archive
```
The archive will be created in the `dist/` directory (e.g., `dist/rest_client-v0.1.0-linux-x86_64.tar.gz`).

## Project Structure

- `app/`: Application source code (UI components, Main entry point).
- `core/`: Core business logic (Data models, HTTP client, Storage, Logging).
- `workers/`: Background workers for asynchronous tasks.
- `resources/`: Static resources (Images, Icons).
- `docs/`: Project documentation and task plans.
- `logs/`: Application logs (Created at runtime).
- `dist/`: Build artifacts (Created during build).

## Development

- **Logging**: Logs are saved to `logs/rest_client.log`.
- **History**: Request history is saved to `history.jsonl`.

### Running Tests

To execute unit tests:

```bash
make test
```
