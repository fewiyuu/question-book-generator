@echo off
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "%~dp0build_from_images.ps1"
if errorlevel 1 (
    echo.
    echo Build failed. Check images or LaTeX setup.
    pause
    exit /b 1
)

if exist "%~dp0main.pdf" (
    start "" "%~dp0main.pdf"
)

exit /b 0
