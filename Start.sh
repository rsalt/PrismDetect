#!/bin/bash

# start.sh - Universal Start Script for PrismDetect
# Usage: ./start.sh [local|prod]

MODE=${1:-local}
PROJECT_ROOT=$(pwd)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting PrismDetect in ${MODE} mode...${NC}"

# 1. Check Prerequisites
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed.${NC}"
    exit 1
fi

# 2. Environment Setup
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from default...${NC}"
    
    if [ "$MODE" == "prod" ]; then
        # Production Defaults
        cat > .env <<EOL
DEBUG=False
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
CORS_ORIGINS=["https://your-domain.com"]
CONFIG_PATH=config/products.json
MODEL_PATH=models/clip_int8.onnx
INDEX_PATH=data/index/product_index.faiss
MIN_CONFIDENCE=0.80
# Fixes for stability
Tokenizers_PARALLELISM=false
OMP_NUM_THREADS=1
EOL
    else
        # Local Defaults
        cat > .env <<EOL
DEBUG=True
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
CORS_ORIGINS=["*"]
CONFIG_PATH=config/products.json
MODEL_PATH=models/clip_int8.onnx
INDEX_PATH=data/index/product_index.faiss
MIN_CONFIDENCE=0.75
# Fixes for stability
Tokenizers_PARALLELISM=false
OMP_NUM_THREADS=1
EOL
    fi
    echo -e "${GREEN}✅ Created .env file.${NC}"
fi

# 3. Model Checks
MODEL_FILE="PrismDetect/models/clip_int8.onnx"
if [ ! -f "$MODEL_FILE" ]; then
    echo -e "${YELLOW}⚠️  Model file not found at $MODEL_FILE.${NC}"
    echo -e "${YELLOW}🔄 Attempting to download/build model...${NC}"
    
    # Check if we can build it locally (requires python env) or if we should rely on Docker build
    if [ "$MODE" == "local" ] && command -v python3 &> /dev/null; then
         # Try to run the build script if we are local and have python
         echo -e "Attempting local build..."
         (cd PrismDetect && python3 -m pip install -r requirements-build.txt && python3 scripts/build-models/build_onnx.py)
    else
         echo -e "${YELLOW}ℹ️  Model will be downloaded/built inside the Docker container.${NC}"
    fi
fi

# 4. Start Application
echo -e "${GREEN}🐳 Starting Docker containers...${NC}"

if [ "$MODE" == "prod" ]; then
    # Production: Build and Run Detached
    docker-compose -f PrismDetect/docker/docker-compose.prod.yml up --build -d
    echo -e "${GREEN}✅ PrismDetect Production started!${NC}"
    echo -e "Logs: docker-compose -f PrismDetect/docker/docker-compose.prod.yml logs -f"
else
    # Local: Build and Run Interactive
    docker-compose -f PrismDetect/docker/docker-compose.yml up --build -d
    echo -e "${GREEN}✅ PrismDetect Local started!${NC}"
    echo -e "API: http://localhost:8000/docs"
    echo -e "Frontend: http://localhost:8501"
    echo -e "Logs: docker-compose -f PrismDetect/docker/docker-compose.yml logs -f"
fi
