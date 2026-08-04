@echo off
setlocal
chcp 65001 > nul 2>&1
cd /d "%~dp0"

set "PROFILE=%~1"
if "%PROFILE%"=="" set "PROFILE=auto"

echo ============================================================
echo  txt2srt 硬件感知安装
echo ============================================================
echo.
echo 安装模式: %PROFILE%
echo   auto             自动检测（推荐）
echo   cpu              强制 CPU 通用版
echo   nvidia-modern    RTX 50 / Blackwell
echo   nvidia-legacy    其他受支持的 NVIDIA 显卡
echo.
echo 依赖、模型和临时文件均保存在本项目目录，不使用用户级缓存。
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Profile "%PROFILE%"
if errorlevel 1 (
    echo.
    echo [错误] 安装失败。请查看上方错误信息。
    pause
    exit /b 1
)

echo.
echo [完成] 现在可以运行 start_ui.bat。
pause
exit /b 0
