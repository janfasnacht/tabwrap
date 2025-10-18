# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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