# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.0] - 2026-06-15

### Added
- Auto-inject `\newcommand` definitions for non-package macros; built-in rule for `\sym` (esttab significance stars) (#22).
- `--preamble` flag (CLI / API / Python `compile_tex()`) for arbitrary preamble lines outside the curated rule set (#22).

### Changed
- Single-table compiles use the `standalone` document class; pages auto-fit the table (#21).
- PNG crop is now handled entirely by PyMuPDF clip-based re-render; Pillow is no longer a dependency.
- Build tooling migrated from Poetry to uv; lockfile is now `uv.lock` (#27).

### Removed
- Pillow dependency.

### Deprecated
- `--landscape` and `--no-resize` (and API/Python equivalents) are no-ops; removal in 2.0.

### Fixed
- Tabular validation strips LaTeX comments before counting `\begin`/`\end` pairs.

## [1.4.0] - 2026-05-04

### Added
- Multi-format output: request `pdf`, `png`, and `svg` in one call (`-f pdf -f png` CLI; `formats=pdf,png` API). Multi-format responses are a ZIP bundle, optionally with a `manifest.json` (`--manifest` / `manifest=true`) carrying page counts, detected packages, LaTeX warnings, and timings.
- Public types: `CompileResult`, `Format`, and a `TabwrapError` exception hierarchy (`InvalidLatexError`, `LatexCompilationError`, `ConversionError`, `DependencyError`).

### Changed
- **Breaking (Python API):** `compile_tex()` now returns a `CompileResult` (was `Path`); compilation errors raise `TabwrapError` subclasses (was `RuntimeError`). CLI and HTTP responses for single-format requests are unchanged.

### Removed
- Stale single-VPS deploy script (`scripts/deploy.sh`) and its README.

## [1.3.1] - 2026-01-24

### Added
- `--version` flag.
- Auto-detection of `caption`, `makecell`, and `bbm` packages.

### Fixed
- `--suffix ""` no longer filters out all files.
- Column-spec parser handles `p{}`, `m{}`, `b{}`, and tabularx `X`.
- Multi-line table rows parse correctly.

## [1.3.0] - 2025-12-09

### Added
- Support for full `\begin{table}...\end{table}` environments.

### Changed
- Table environments skip automatic `\resizebox` and `\begin{center}` wrapping.
- Production logging honours `TABWRAP_LOG_DIR`.

## [1.2.0] - 2025-12-08

### Added
- API rate limiting (SlowAPI) and `TABWRAP_*` environment configuration.
- Gunicorn production config; smoke-test script; Locust load tests.

### Changed
- API error responses split into 400 (user) vs 500 (system).
- API version sourced from package metadata.
- LaTeX log parsed even when pdflatex exits 0 (catches silent errors).

## [1.1.0] - 2025-10-18

### Added
- Support for `longtable` environment for multi-page tables
- Support for `threeparttable` environment for tables with notes
- Automatic detection of `\cmidrule` command for booktabs package
- Automatic detection of siunitx `S` column types, including edge cases like `{lScr}` and `{S[table-format=1.3]}`

### Fixed
- longtable incompatibility with `\resizebox` and `\begin{center}` environments

### Changed
- Refactored package detection into dedicated module with regex-based pattern matching

## [1.0.1] - 2025-09-27

### Changed
- Updated documentation and changelog for initial release

## [1.0.0] - 2025-09-27

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