@echo off
REM 启动Gradio Web界面

REM 设置UTF-8编码，解决中文乱码问题
chcp 65001 > nul 2>&1

REM 清理Gradio临时文件（避免权限错误）
rd /s /q "%LOCALAPPDATA%\Temp\gradio" 2>nul

echo ========================================
echo 音频-文本对齐工具 - 启动UI界面
echo ========================================
echo.

REM 检查虚拟环境
if not exist "venv\" (
    echo [错误] 虚拟环境不存在，请先运行 setup.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM CUDA性能优化
set CUDA_LAUNCH_BLOCKING=0

echo 正在启动Web界面...
echo 请在浏览器中访问: http://127.0.0.1:7860
echo.
echo 按 Ctrl+C 可停止服务器
echo.

REM 运行UI
venv\Scripts\python txt2srt_ui.py

pause
