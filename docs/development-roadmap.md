# TODO: probably this is also too long and or unnecessary even? But okay start; let's just wait until ew get 1.0 done before we create something like this

# texout Development Roadmap

## Project Vision
Transform texout into a polished, user-friendly tool for the academic community to compile LaTeX tables and research outputs efficiently.

## Core Mission
Researchers generate many LaTeX table fragments that need compilation for review and sharing. texout automates this workflow with excellent error handling and multi-file support.

## Development Phases

### Phase 1: Stable CLI Tool (v1.0)
**Goal**: Professional command-line tool with excellent user experience
- Modern CLI interface with intuitive defaults
- Comprehensive error handling that guides users to solutions
- Multi-file compilation with batch processing
- PDF and PNG output support
- Optional API for web integration

### Phase 2: Enhanced Features (v1.1-1.2)
**Goal**: Quality of life improvements and additional formats
- SVG output support for web embedding
- Shell completion for better CLI experience
- Enhanced error suggestions with fix commands
- Configuration file support

### Phase 3: Research Workflow Integration (v1.3+)
**Goal**: Broader research output compilation
- Support for combining tables and figures into overview documents
- Integration with common research file formats
- Batch processing tools for large projects

# TOOD: mention the API and the front end over at texout-web

## Design Principles

### User Experience First
- Error messages must be helpful, not cryptic
- Defaults should work for most users out of the box
- Installation should be simple: `pip install texout`

### Academic Workflow Focus
- Designed for researchers who generate many table files
- Handles common LaTeX packages and environments
- Supports typical academic output formats

### Professional Standards
- Semantic versioning and stable releases
- Comprehensive testing and documentation
- Clean codebase following Python best practices

## Technical Strategy

### Package Distribution
- PyPI publication for easy installation
- Support for both pip and pipx
- Optional extras for API functionality

### Architecture
- Clean separation between CLI, API, and core logic
- Modular design for easy extension
- Standard Python package structure with src/ layout

This roadmap focuses on making LaTeX table compilation painless for researchers while maintaining professional development standards.