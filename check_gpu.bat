@echo off
REM GPU检查脚本

echo ========================================
echo GPU 检测工具
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

REM 运行检测脚本
venv\Scripts\python check_gpu.py

pause

