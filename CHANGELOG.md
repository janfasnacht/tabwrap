# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- SVG output support with `--svg` flag
- FastAPI-based API with automatic OpenAPI documentation
- Interactive Swagger UI at `/api/docs` and ReDoc at `/api/redoc`
- Improved API error handling with proper HTTP status codes
- Type-safe API endpoints with Pydantic models
- Shell completion support for bash, zsh, and fish via `--completion` flag

### Changed
- Migrated API from Flask-RESTX to FastAPI for better maintainability
- Simplified API testing with FastAPI TestClient

## [1.0.0] - 2025-01-XX

### Added
- CLI interface with `tabwrap [input] [options]`
- PDF and PNG output support
- Batch processing with recursive directory option
- Automatic LaTeX package detection
- Combined PDF generation with table of contents
- Error recovery for multi-file compilation
- Web API (optional, install with `[api]` extra)
- Landscape orientation support
- Custom output suffixes and headers

### Dependencies
- Python 3.10+
- LaTeX distribution (TeX Live, MiKTeX, or MacTeX)
- ImageMagick (optional, for PNG output)
- pdf2svg (optional, for SVG output)