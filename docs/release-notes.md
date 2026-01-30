# Release Notes

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- File Upload support (Multipart/Form-data) in Request Editor.
- Support for `files` and `form_fields` in request data model and storage.

## [0.1.0] - 2026-01-30
### Added
- Initial prototype release.
- Main window with Collection Tree, Request Editor, and Response Viewer.
- Environment management (Global variables).
- Workspace Save/Load (JSON format).
- Request History (JSONL format).
- Request execution via `httpx` with support for methods, headers, body, and auth.
- Manage Environment dialog with overlay support for Wayland.
