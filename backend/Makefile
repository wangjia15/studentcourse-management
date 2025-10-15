.PHONY: help install dev test lint format clean run migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Install development dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo "  clean       Clean cache files"
	@echo "  run         Run development server"
	@echo "  migrate     Run database migrations"
	@echo "  db-init     Initialize database"

# Install dependencies
install:
	uv sync

# Install development dependencies
dev:
	uv sync --dev

# Run tests
test:
	uv run pytest

# Run linting
lint:
	uv run ruff check app/
	uv run mypy app/

# Format code
format:
	uv run black app/
	uv run ruff check --fix app/

# Clean cache files
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/

# Run development server
run:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
migrate:
	uv run alembic upgrade head

# Create new migration
migration:
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

# Initialize database
db-init:
	uv run alembic upgrade head

# Reset database
db-reset:
	rm -f grade_management.db
	uv run alembic upgrade head
