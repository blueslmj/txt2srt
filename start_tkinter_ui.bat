@echo off
REM 启动Tkinter桌面界面

echo ========================================
echo 音频-文本对齐工具 - 启动桌面界面
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

echo 正在启动桌面界面...
echo.

REM 运行Tkinter UI
venv\Scripts\python txt2srt_tkinter_ui.py

pause

