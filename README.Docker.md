# Docker Deployment Guide

This guide explains how to build and run the Automated Transfer Station using Docker with optimized fast bootup.

## Quick Start

### Build the Docker image:
```bash
docker build -t automated-transfer-station:latest .
```

### Run with Docker Compose (Recommended):
```bash
docker-compose up -d
```

### Run with Docker directly:
```bash
docker run -d \
  -p 5000:5000 \
  -p 8765:8765 \
  -v $(pwd)/src/config.json:/app/src/config.json:ro \
  --name transfer-station \
  automated-transfer-station:latest
```

## Performance Optimizations

This Dockerfile is optimized for **extremely fast bootup** with the following techniques:

### 1. **Multi-stage Build**
   - Separates dependency installation from the final image
   - Reduces final image size by ~40-60%

### 2. **Layer Caching**
   - Dependencies are copied before application code
   - Stable dependencies installed first
   - Rebuilds are faster when only code changes

### 3. **Minimal Base Image**
   - Uses `python:3.11-slim` instead of full Python image
   - Only installs required system packages
   - Cleans up apt cache immediately

### 4. **Pre-compilation**
   - Python files are pre-compiled to `.pyc`
   - Eliminates compilation overhead at runtime
   - Faster import times

### 5. **No Cache Installation**
   - `PIP_NO_CACHE_DIR=1` reduces image size
   - Faster builds with less disk I/O

### 6. **Optimized .dockerignore**
   - Excludes unnecessary files from context
   - Faster Docker build times
   - Smaller images

## Build Arguments

Enable faster builds with BuildKit:
```bash
DOCKER_BUILDKIT=1 docker build -t automated-transfer-station:latest .
```

## Viewing Logs

```bash
# Follow logs
docker-compose logs -f

# View specific service logs
docker logs -f transfer-station
```

## Stopping the Service

```bash
# With Docker Compose
docker-compose down

# With Docker
docker stop transfer-station
docker rm transfer-station
```

## Health Checks

The container includes a health check that monitors the Flask server:
```bash
docker ps  # Shows health status
```

## Troubleshooting

### Container exits immediately
Check logs: `docker logs transfer-station`

### Cannot connect to ports
Ensure ports 5000 and 8765 are not in use:
```bash
# Windows
netstat -ano | findstr "5000"
netstat -ano | findstr "8765"
```

### Camera not detected
- Ensure the container has access to USB devices (Linux)
- Use `privileged: true` in docker-compose.yml
- Mount `/dev/bus/usb:/dev/bus/usb`

### Performance tuning
Adjust resource limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'  # Increase CPU
      memory: 4G  # Increase memory
```

## Expected Bootup Time

- **Cold start (first build)**: 2-5 minutes
- **Warm start (cached layers)**: 10-30 seconds
- **Container startup**: 3-8 seconds
- **Application ready**: 5-15 seconds after container starts

Total bootup time after initial build: **~8-23 seconds**

## Production Deployment

For production, consider:
1. Using a container orchestrator (Kubernetes, Docker Swarm)
2. Setting up monitoring (Prometheus, Grafana)
3. Implementing log aggregation (ELK stack)
4. Using secrets management for sensitive config
5. Setting up automated backups of configuration

## Next Steps

1. Copy `.env.example` to `.env` and customize
2. Review and update `src/config.json` for your environment
3. Build and test the container
4. Set up monitoring and logging
5. Deploy to production

## Support

For issues or questions, refer to the main README.md or create an issue in the repository.

