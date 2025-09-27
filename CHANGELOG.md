# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### 🎉 Initial Release

#### Added
- **CLI Interface** with intuitive positional arguments and short flags
  - `tabwrap [input] [options]` - Process files or directories
  - Short flags: `-o`, `-p`, `-r`, `-c` for common operations
  - Smart defaults: output to current directory, auto-detect input type

- **Enhanced Error Handling & Recovery**
  - Multi-file batch processing with error recovery
  - Continue compilation even if some files fail
  - Structured error reporting with specific suggestions
  - LaTeX dependency checking (pdflatex, ImageMagick)
  - User-friendly error messages with fix recommendations

- **Comprehensive LaTeX Support**
  - Auto-detection of required packages (booktabs, tabularx, siunitx, multirow, etc.)
  - Smart package inclusion based on content analysis
  - Conditional loading of underscore package for filenames
  - Support for complex table environments

- **Flexible Output Options**
  - PDF output with automatic table resizing
  - PNG output with cropping and ImageMagick integration
  - Landscape orientation support
  - Combined PDFs with table of contents
  - Custom filename suffixes and headers

- **Batch Processing**
  - Directory processing with recursive option
  - File filtering to avoid double-compilation
  - Combine multiple PDFs into single document
  - Progress reporting and summary statistics

- **Professional Code Organization**
  - Domain-driven package structure (`latex/`, `output/`, `io/`, `config/`)
  - Comprehensive test suite (53 tests) with 100% success rate
  - Type hints and documentation throughout
  - Clean separation of concerns

- **API Support** (Optional)
  - Flask-based web API with OpenAPI documentation
  - Optional installation with `pip install tabwrap[api]`
  - Programmatic access via `TexCompiler` class

- **Development Infrastructure**
  - Poetry-based dependency management
  - Makefile for common development tasks
  - Comprehensive test coverage with error handling scenarios
  - CLI option tests and integration tests

#### Technical Features
- **Package Detection Engine**: Rule-based system recognizing 12+ LaTeX packages
- **Template System**: Modular LaTeX document templates
- **Validation Framework**: Input validation with helpful error messages
- **Multi-format Output**: PDF and PNG with automatic optimization
- **Cross-platform Support**: Windows, macOS, Linux compatibility

### Dependencies
- Python 3.9+
- click 8.1+ (CLI framework)
- PyMuPDF 1.24+ (PDF processing)
- NumPy 2.1+ (array operations)
- Pillow 10.4+ (image processing)

### Optional Dependencies
- Flask 3.1+ (API support)
- Flask-CORS 5.0+ (API CORS support)
- Flask-Swagger-UI 4.11+ (API documentation)

### External Dependencies
- **LaTeX Distribution** (required): TeX Live, MiKTeX, or MacTeX
- **ImageMagick** (optional): For PNG output support

---

## Development History

This project evolved from `tex_table_compiler` to `tabwrap` with significant architectural improvements:

### Pre-1.0 Development
- **0.1.0-alpha**: Initial concept and basic LaTeX compilation
- **0.2.0-alpha**: Added CLI interface and basic error handling  
- **0.3.0-alpha**: Package rename to `tabwrap` and CLI improvements
- **0.4.0-alpha**: Enhanced error handling and multi-file support
- **0.5.0-alpha**: Code reorganization and professional structure
- **0.9.0-beta**: Feature complete, comprehensive testing

### Architecture Evolution
1. **Utility-based structure** → **Domain-driven organization**
2. **Single-file processing** → **Batch processing with error recovery** 
3. **Basic error messages** → **Structured error reporting with suggestions**
4. **Manual package inclusion** → **Automatic package detection**
5. **Simple CLI** → **Professional CLI with short flags and smart defaults**

---

## Future Roadmap

### Planned Features (v1.x)
- conda-forge distribution for scientific computing community
- Docker image for reproducible research environments  
- Additional output formats (HTML, Word)
- Configuration file support
- Plugin architecture for custom templates

### Under Consideration (v2.x)
- GUI interface for non-technical users
- Cloud processing support
- Integration with popular statistical software
- Advanced table styling and theming
- Collaborative features for research teams

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/janfasnacht/tabwrap.git
cd tabwrap
poetry install
poetry run pytest
```

### Release Process
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with new features
3. Run full test suite: `make test`
4. Build and test: `poetry build && poetry run pip install dist/*.whl`
5. Create release tag: `git tag v1.0.0`
6. Publish to PyPI: `poetry publish`

## License

MIT License - See [LICENSE](LICENSE) for details.