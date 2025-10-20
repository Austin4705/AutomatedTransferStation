@echo off
REM Fast Docker build script for Automated Transfer Station (Windows)

echo Building Automated Transfer Station Docker image...
echo Using BuildKit for optimized builds...

REM Enable BuildKit for faster builds
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

REM Build the image
docker-compose build --parallel

echo.
echo Build complete!
echo.
echo To start the container, run:
echo   docker-compose up -d
echo.
echo To view logs:
echo   docker-compose logs -f

