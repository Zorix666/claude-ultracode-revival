@echo off
chcp 65001 >nul
title Claude Desktop Ultracode 智能自适应永久固化修复工具
cd /d "%~dp0"

echo ===================================================================
echo   Claude Desktop Ultracode 智能自适应修复工具 (支持 v2 / v3 全系列)
echo ===================================================================
echo.
echo [*] 正在请求管理员权限并注入自适应补丁...
echo.

python "%~dp0apply_patch.py"
if errorlevel 1 (
    py -3.12 "%~dp0apply_patch.py"
)

echo.
pause
