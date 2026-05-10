# Automated Transfer Station Launcher
# This script sets up the database, launches the client, and runs the Python environment

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if a command exists
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Test-DockerRunning {
    try {
        # Fast path for Windows: check Docker named pipe or DOCKER_HOST pipe
        $dockerHost = $env:DOCKER_HOST
        if ([string]::IsNullOrWhiteSpace($dockerHost)) {
            if (Test-Path '\\.\pipe\docker_engine') {
                return $true
            }
        }
        elseif ($dockerHost -like 'npipe://*') {
            $pipePath = $dockerHost -replace '^npipe://', ''
            if (Test-Path $pipePath) {
                return $true
            }
        }

        # Fall back to probing the daemon via docker CLI with a short wait window
        $maxWaitSeconds = 60
        $retryIntervalSeconds = 2
        $deadline = (Get-Date).AddSeconds($maxWaitSeconds)

        while ((Get-Date) -lt $deadline) {
            & docker version --format "{{.Server.Version}}" 1>$null 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $true
            }
            Start-Sleep -Seconds $retryIntervalSeconds
        }

        return $false
    }
    catch {
        return $false
    }
}

# Print header
Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "  Automated Transfer Station Launcher" "Cyan"
Write-ColorOutput "========================================`n" "Cyan"

# Step 1: Check prerequisites
Write-ColorOutput "[1/6] Checking prerequisites..." "Yellow"

if (-not (Test-CommandExists "conda")) {
    Write-ColorOutput "ERROR: Conda is not installed or not in PATH" "Red"
    Write-ColorOutput "Please install Miniconda and ensure it's in your PATH" "Red"
    exit 1
}

if (-not (Test-CommandExists "docker")) {
    Write-ColorOutput "ERROR: Docker is not installed or not in PATH" "Red"
    Write-ColorOutput "Please install Docker Desktop" "Red"
    exit 1
}

if (-not (Test-CommandExists "npm")) {
    Write-ColorOutput "ERROR: npm is not installed or not in PATH" "Red"
    Write-ColorOutput "Please install Node.js" "Red"
    exit 1
}

Write-ColorOutput "All prerequisites met!" "Green"

# Step 2: Check if Docker Desktop is running
Write-ColorOutput "`n[2/6] Checking Docker Desktop..." "Yellow"
if (-not (Test-DockerRunning)) {
    Write-ColorOutput "ERROR: Docker Desktop is not running" "Red"
    Write-ColorOutput "Please start Docker Desktop and try again" "Red"
    exit 1
}
Write-ColorOutput "Docker Desktop is running!" "Green"

# Step 3: Start OMERO database
Write-ColorOutput "`n[3/6] Starting OMERO database..." "Yellow"
try {
    docker compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "Database started successfully!" "Green"
        Write-ColorOutput "OMERO Web UI available at: http://localhost:4080/" "Cyan"
        Write-ColorOutput "Login credentials - username: root, password: omero" "Cyan"
    } else {
        Write-ColorOutput "WARNING: Database may already be running or encountered an issue" "Yellow"
    }
} catch {
    Write-ColorOutput "ERROR: Failed to start database" "Red"
    Write-ColorOutput $_.Exception.Message "Red"
    exit 1
}

# Step 4: Install and start client
Write-ColorOutput "`n[4/6] Setting up client..." "Yellow"
Push-Location client

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-ColorOutput "Installing client dependencies (this may take a while)..." "Yellow"
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "ERROR: Failed to install client dependencies" "Red"
        Pop-Location
        exit 1
    }
}

Write-ColorOutput "Starting client development server..." "Yellow"
$clientProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev" -PassThru -NoNewWindow
Write-ColorOutput "Client started with PID: $($clientProcess.Id)" "Green"
Pop-Location

# Wait a moment for the client to start
Start-Sleep -Seconds 1

# Step 5: Check conda environment
Write-ColorOutput "`n[5/6] Checking Python environment..." "Yellow"

# Get conda info
$condaEnvs = conda env list | Out-String

if ($condaEnvs -notmatch "automatedTransfer") {
    Write-ColorOutput "ERROR: Conda environment 'automatedTransfer' not found" "Red"
    Write-ColorOutput "Please create it using:" "Yellow"
    Write-ColorOutput "  conda create -n automatedTransfer python=3.11.9" "Yellow"
    Write-ColorOutput "  conda activate automatedTransfer" "Yellow"
    Write-ColorOutput "  pip install -r requirements.txt" "Yellow"

    # Kill client process before exiting
    Stop-Process -Id $clientProcess.Id -Force
    exit 1
}

Write-ColorOutput "Python environment found!" "Green"

# Step 6: Launch Python application
Write-ColorOutput "`n[6/6] Launching Python application..." "Yellow"
Write-ColorOutput "========================================`n" "Cyan"

# Run as a package from the project root: PYTHONPATH=src python -m ats
$env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH

try {
    & cmd /c "conda activate automatedTransfer && python -m ats"
} catch {
    Write-ColorOutput "ERROR: Failed to launch Python application" "Red"
    Write-ColorOutput $_.Exception.Message "Red"
    Stop-Process -Id $clientProcess.Id -Force
    exit 1
}

# Cleanup function
function Cleanup {
    Write-ColorOutput "`n`nShutting down..." "Yellow"

    # Kill client process
    if ($clientProcess -and -not $clientProcess.HasExited) {
        Write-ColorOutput "Stopping client..." "Yellow"
        Stop-Process -Id $clientProcess.Id -Force
    }

    # Optionally stop docker
    $stopDocker = Read-Host "Stop OMERO database? (y/n)"
    if ($stopDocker -eq "y") {
        Write-ColorOutput "Stopping database..." "Yellow"
        docker compose down
    }

    Write-ColorOutput "Cleanup complete!" "Green"
}

# Register cleanup on exit
Register-EngineEvent PowerShell.Exiting -Action { Cleanup }

# Wait for user to press Enter to exit (this is handled by the Python script)
# The script will exit when python -m ats exits
