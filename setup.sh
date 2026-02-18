#!/bin/bash
# setup.sh - Complete project setup

echo "🚀 Setting up PrismDetect..."

# Create project root
mkdir -p PrismDetect
cd PrismDetect

# Create directory structure
mkdir -p .github/workflows
mkdir -p api/routes
mkdir -p core/validators core/learning
mkdir -p models
mkdir -p data/references/pride-of-cows data/index data/logs
mkdir -p config
mkdir -p scripts/build-models scripts/deploy scripts/dev
mkdir -p tests/unit tests/integration tests/fixtures/test_images
mkdir -p docker
mkdir -p docs/images
mkdir -p kubernetes
mkdir -p monitoring/prometheus monitoring/grafana/dashboards
mkdir -p examples

# Create __init__.py files
touch api/__init__.py
touch api/routes/__init__.py
touch core/__init__.py
touch core/validators/__init__.py
touch core/learning/__init__.py
touch config/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

echo "✅ Directory structure created"
