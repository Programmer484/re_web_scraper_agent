#!/bin/bash
# Simple startup script for the property agent

echo "🏠 Starting PropertySearch Agent..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Copy env.example to .env and add your APIFY_TOKEN"
    echo "cp env.example .env"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed!"
    echo "📦 Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Build and run
echo "🔨 Building Docker image..."
docker build -t property-agent .

echo "🚀 Starting container..."
docker run -d \
    --name property-agent \
    -p 8000:8000 \
    --env-file .env \
    -v $(pwd):/app \
    -v $(pwd)/logs:/app/logs \
    property-agent

echo "✅ PropertySearch Agent running at http://localhost:8000"
echo "🩺 Health check: curl http://localhost:8000/"
echo "📖 API docs: http://localhost:8000/docs" 