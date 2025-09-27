# Makefile for tabwrap development tasks

.PHONY: help test test-verbose test-coverage clean lint format type-check install dev-install build publish

# Default target
help:
	@echo "Available commands:"
	@echo "  test           - Run all tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-watch     - Run tests in watch mode"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black and isort"
	@echo "  type-check     - Run type checking with mypy"
	@echo "  clean          - Clean up build artifacts and cache"
	@echo "  install        - Install package in development mode"
	@echo "  dev-install    - Install with dev dependencies"
	@echo "  build          - Build distribution packages"
	@echo "  publish        - Publish to PyPI"
	@echo "  check-deps     - Check for outdated dependencies"

# Test commands
test:
	poetry run pytest tests/ -x

test-verbose:
	poetry run pytest tests/ -v -s

test-coverage:
	poetry run pytest tests/ --cov=tabwrap --cov-report=html --cov-report=term

test-watch:
	poetry run pytest-watch tests/ -- -x

# Code quality
lint:
	poetry run flake8 tabwrap tests
	poetry run pylint tabwrap

format:
	poetry run black tabwrap tests
	poetry run isort tabwrap tests

type-check:
	poetry run mypy tabwrap

# Development setup
install:
	poetry install

dev-install:
	poetry install --with dev

# Build and publish
build:
	poetry build

publish:
	poetry publish

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
	poetry show --outdated

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
	@echo "Poetry version: $(shell poetry --version)"
	@echo "Dependencies:"
	@poetry show --tree

# Quick development workflow
dev: clean dev-install test lint

# Full CI workflow  
ci: clean dev-install test-coverage lint type-check