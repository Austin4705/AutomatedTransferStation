@echo off
REM Automated Transfer Station Launcher
REM This batch file launches the PowerShell script with proper execution policy

echo ========================================
echo   Automated Transfer Station
echo ========================================
echo.
echo Starting launcher...
echo.

REM Run PowerShell script with bypass execution policy for this session only
PowerShell -ExecutionPolicy Bypass -File "%~dp0launch.ps1"

REM Check if PowerShell script failed
if errorlevel 1 (
    echo.
    echo ERROR: Launcher failed to start
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

exit /b 0
