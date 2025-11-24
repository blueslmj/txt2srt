@echo off
REM 启动Gradio Web界面

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

echo 正在启动Web界面...
echo 浏览器将自动打开 http://127.0.0.1:7860
echo.
echo 按 Ctrl+C 可停止服务器
echo.

REM 运行UI
venv\Scripts\python txt2srt_ui.py

pause

