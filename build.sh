#!/bin/bash
# Fast Docker build script for Automated Transfer Station

set -e

echo "Building Automated Transfer Station Docker image..."
echo "Using BuildKit for optimized builds..."

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build the image
docker-compose build --parallel

echo "Build complete!"
echo ""
echo "To start the container, run:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"

