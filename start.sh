#!/bin/bash
# Enhanced startup script for the property agent with debugging

set -e  # Exit on any error

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

# Create logs directory if it doesn't exist
mkdir -p logs

# Clean up any existing container
echo "🧹 Cleaning up existing containers..."
docker stop property-agent 2>/dev/null || true
docker rm property-agent 2>/dev/null || true

# Build and run
echo "🔨 Building Docker image..."
docker build -t property-agent .

echo "🚀 Starting container with debug logging..."
docker run -d \
    --name property-agent \
    -p 8000:8000 \
    --env-file .env \
    -v $(pwd)/logs:/app/logs \
    property-agent

echo "⏳ Waiting for service to start..."
sleep 10

# Health check
echo "🩺 Performing health check..."
if curl -f http://localhost:8000/health; then
    echo "✅ PropertySearch Agent is healthy and running!"
    echo "🌐 API available at: http://localhost:8000"
    echo "📖 API docs: http://localhost:8000/docs"
    echo "🔍 Test search: curl -X POST http://localhost:8000/search -H 'Content-Type: application/json' -d '{\"listing_type\":\"both\",\"latitude\":30.2672,\"longitude\":-97.7431}'"
    echo ""
    echo "📊 To view logs in real-time:"
    echo "   docker logs -f property-agent"
    echo ""
    echo "🛑 To stop the service:"
    echo "   docker stop property-agent"
else
    echo "❌ Health check failed!"
    echo "📋 Container logs:"
    docker logs property-agent
    exit 1
fi 