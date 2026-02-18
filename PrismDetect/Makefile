.PHONY: help install dev build test run docker-up docker-down clean

PROJECT_NAME=prismdetect
PYTHON=python3

help:
	@echo "🚀 $(PROJECT_NAME) Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  dev          Install development dependencies"
	@echo "  build        Build ONNX model"
	@echo "  test         Run tests"
	@echo "  run          Run API server"
	@echo "  docker-up    Start Docker Compose"
	@echo "  docker-down  Stop Docker Compose"
	@echo "  clean        Clean temporary files"

install:
	@echo "📦 Installing production dependencies..."
	$(PYTHON) -m pip install -r requirements.txt
	@echo "✅ Done"

dev: install
	@echo "🔧 Installing development dependencies..."
	$(PYTHON) -m pip install -r requirements-dev.txt
	@echo "✅ Done"

build:
	@echo "🔨 Building ONNX model..."
	$(PYTHON) scripts/build-models/build_onnx.py

test:
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest tests/ -v --cov=core --cov=api --cov-report=term-missing

run:
	@echo "🚀 Starting API server..."
	$(PYTHON) -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose -f docker/docker-compose.yml up -d
	@echo "✅ API available at http://localhost:8000"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose -f docker/docker-compose.yml down

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	@echo "✅ Done"

init: install download-models
	@echo "🚀 Project initialized! Run 'make run' to start."

download-models:
	@echo "📥 Downloading pre-built models..."
	chmod +x scripts/deploy/download_models.sh
	./scripts/deploy/download_models.sh
