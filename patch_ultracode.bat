@echo off
chcp 936 >nul
title 永久开启 Claude 桌面端 Ultracode 6 档滑块

:: 1. 自动请求管理员提权
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo [>] 正在请求管理员权限，请在 UAC 弹窗中点击【是】...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B
)
if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )

pushd "%CD%"
CD /D "%~dp0"

echo ========================================================
echo        Claude Desktop Ultracode 滑块永久固化补丁
echo ========================================================
echo.

:: 2. 关闭正在运行的 Claude
echo [*] 正在关闭运行中的 Claude 客户端...
taskkill /F /IM Claude.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: 3. 搜索 WindowsApps 目录下的目标文件
for /d %%D in ("%PROGRAMFILES%\WindowsApps\Claude_*") do (
    if exist "%%D\app\resources\ion-dist\assets\v1\c593f7513-DQShcHgn.js" (
        set "TARGET=%%D\app\resources\ion-dist\assets\v1\c593f7513-DQShcHgn.js"
        set "CLAUDE_EXE=%%D\app\Claude.exe"
    )
)

if not defined TARGET (
    echo [!] 未在默认路径找到 Claude 安装文件！
    pause
    exit /B
)

echo [*] 解除 WindowsApps 系统写保护: %TARGET%
takeown /f "%TARGET%" /a >nul 2>&1
takeown /f "%TARGET%" >nul 2>&1
icacls "%TARGET%" /grant:r administrators:F >nul 2>&1
icacls "%TARGET%" /grant:r Everyone:F >nul 2>&1

:: 4. 调用 Python 脚本精准注入
echo [*] 执行补丁注入...
python "%~dp0apply_patch.py"
if '%errorlevel%' NEQ '0' (
    echo [!] 注入过程遇到异常，请检查上方日志。
    pause
    exit /B
)

echo.
echo ========================================================
echo   [OK] 永久固化完成！滑块已拥有 6 个圆点！
echo   第 6 档正是 ULTRACORDE，已支持双向自由拖动！
echo ========================================================
echo.
echo [*] 正在重新拉起 Claude...
if defined CLAUDE_EXE (
    start "" "%CLAUDE_EXE%"
)
timeout /t 3 >nul
