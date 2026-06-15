# Makefile for tabwrap development tasks

.PHONY: help test test-verbose test-coverage clean lint format install dev-install build publish release

# Default target
help:
	@echo "Available commands:"
	@echo "  test           - Run all tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with ruff"
	@echo "  clean          - Clean up build artifacts and cache"
	@echo "  install        - Install package dependencies"
	@echo "  dev-install    - Install with api extras (dev group always included)"
	@echo "  build          - Build distribution packages"
	@echo "  publish        - Publish to PyPI"
	@echo "  check-deps     - Check for outdated dependencies"
	@echo "  release        - Bump version, commit, tag (push manually). Usage: make release VERSION=1.4.1"

# Test commands
test:
	uv run pytest tests/ -x

test-verbose:
	uv run pytest tests/ -v -s

test-coverage:
	uv run pytest tests/ --cov=tabwrap --cov-report=html --cov-report=term

# Code quality
lint:
	uv run ruff check tabwrap tests

format:
	uv run ruff format tabwrap tests

# Development setup
install:
	uv sync

dev-install:
	uv sync --extra api

# Build and publish
build:
	uv build

publish:
	uv publish

# Bump version in pyproject, commit, and tag. Push is manual so the
# diff can be reviewed before CI fires (PyPI publish + GHCR build).
# Usage: make release VERSION=1.4.1
release:
	@test -n "$(VERSION)" || (echo "Usage: make release VERSION=x.y.z"; exit 1)
	uv version $(VERSION)
	git add pyproject.toml
	git commit -m "Release v$(VERSION)"
	git tag v$(VERSION)
	@echo
	@echo "Tagged v$(VERSION). Push with:"
	@echo "  git push origin main && git push origin v$(VERSION)"

# Maintenance
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

check-deps:
	uv pip list --outdated

# LaTeX development helpers
test-latex:
	@echo "Testing LaTeX installation..."
	@which pdflatex || echo "❌ pdflatex not found"
	@which convert || echo "❌ ImageMagick convert not found (needed for PNG output)"
	@pdflatex --version | head -1

# Project info
info:
	@echo "Project: tabwrap"
	@echo "Python version: $(shell python --version)"
	@echo "uv version: $(shell uv --version)"
	@echo "Dependencies:"
	@uv tree

# Quick development workflow
dev: clean dev-install test lint

# Full CI workflow
ci: clean dev-install test-coverage lint
