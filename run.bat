@echo off
REM Parali Mitra Windows Launcher
TITLE Parali Mitra - Paddy Straw Fuel & Compliance Platform

echo ========================================================
echo   Parali Mitra (Paddy Straw Co-Firing & Compliance)
echo   Windows Automatic Launcher
echo ========================================================

python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python launcher.py
    goto :eof
)

py --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py launcher.py
    goto :eof
)

echo [ERROR] Python was not found in your system PATH.
echo Please install Python 3.10+ from https://www.python.org/
echo Be sure to check 'Add Python to PATH' during installation.
pause
