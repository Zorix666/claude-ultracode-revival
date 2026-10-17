@echo off
chcp 936 >nul
title Claude Desktop Ultracode Patch
cd /d "%~dp0"
echo [*] Starting Ultracode Patch...
python apply_patch.py
if %errorlevel% neq 0 (
    echo.
    echo [!] An error occurred, see output above.
    pause
)
