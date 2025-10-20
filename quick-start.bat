@echo off
REM Quick start script for Automated Transfer Station (Windows)

echo ============================================
echo  Automated Transfer Station - Quick Start
echo ============================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/3] Building Docker image...
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1
docker-compose build

if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Starting container...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ERROR: Failed to start container!
    pause
    exit /b 1
)

echo.
echo [3/3] Waiting for application to be ready...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo  Application is starting!
echo ============================================
echo.
echo Web Server:    http://localhost:5000
echo Health Check:  http://localhost:5000/health
echo Available Cameras: http://localhost:5000/available_cameras
echo.
echo To view logs:  docker-compose logs -f
echo To stop:       docker-compose down
echo.

REM Try to open health check in browser
start http://localhost:5000/health

echo Press any key to view live logs...
pause >nul

docker-compose logs -f

