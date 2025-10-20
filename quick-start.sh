#!/bin/bash
# Quick start script for Automated Transfer Station

set -e

echo "============================================"
echo " Automated Transfer Station - Quick Start"
echo "============================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "[1/3] Building Docker image..."
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
docker-compose build

echo ""
echo "[2/3] Starting container..."
docker-compose up -d

echo ""
echo "[3/3] Waiting for application to be ready..."
sleep 5

echo ""
echo "============================================"
echo " Application is starting!"
echo "============================================"
echo ""
echo "Web Server:    http://localhost:5000"
echo "Health Check:  http://localhost:5000/health"
echo "Available Cameras: http://localhost:5000/available_cameras"
echo ""
echo "To view logs:  docker-compose logs -f"
echo "To stop:       docker-compose down"
echo ""

# Check health
echo "Checking application health..."
for i in {1..10}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✓ Application is healthy!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "⚠ Health check timeout. Check logs with: docker-compose logs"
    else
        echo "  Waiting... ($i/10)"
        sleep 2
    fi
done

echo ""
echo "View live logs? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker-compose logs -f
fi

