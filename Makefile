.PHONY: setup build run dev stop clean test lint format

# Project configuration
PROJECT_NAME := tg-channel-parser
PYTHON := python3
DOCKER_COMPOSE := docker-compose

# Setup project
setup:
	$(PYTHON) -m pip install poetry
	poetry install

# Build Docker containers
build:
	$(DOCKER_COMPOSE) build

# Run application in Docker
run:
	$(DOCKER_COMPOSE) up -d

# Run application in development mode
dev:
	$(DOCKER_COMPOSE) up

# Stop application
stop:
	$(DOCKER_COMPOSE) down

# Clean Docker artifacts
clean:
	$(DOCKER_COMPOSE) down -v
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage

# Run tests
test:
	poetry run pytest

# Run linting
lint:
	poetry run flake8 src tests
	poetry run mypy src tests

# Format code
format:
	poetry run black src tests
	poetry run isort src tests

# Create .env file from example
env:
	cp .env.example .env

# Logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Enter the container shell
shell:
	$(DOCKER_COMPOSE) exec app bash