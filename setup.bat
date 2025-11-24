@echo off
REM 自动设置虚拟环境和安装依赖

echo ========================================
echo 音频-文本对齐工具 - 安装脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10-3.13
    echo.
    echo 推荐版本: Python 3.12 或 3.13
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 显示Python版本
echo 检测到的Python版本:
python --version
echo.

REM 检查Python版本（简单警告）
python -c "import sys; exit(0 if sys.version_info >= (3,10) and sys.version_info < (3,14) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [警告] 检测到不兼容的Python版本！
    echo.
    echo 本项目需要 Python 3.10-3.13
    echo 当前版本可能不支持，建议安装 Python 3.12 或 3.13
    echo.
    echo 详细解决方案请查看: INSTALL_FIX.md
    echo.
    echo 是否继续尝试安装？ [按Ctrl+C取消]
    pause
)

echo [1/3] 创建虚拟环境...
if not exist "venv\" (
    python -m venv venv
    echo ✅ 虚拟环境创建完成
) else (
    echo ✅ 虚拟环境已存在
)

echo.
echo [2/3] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [3/3] 安装完成！
echo.
echo ========================================
echo 使用方法:
echo ========================================
echo 1. 激活虚拟环境:
echo    venv\Scripts\activate
echo.
echo 2. 运行程序:
echo    venv\Scripts\python txt2srt.py [音频文件] [文本文件]
echo.
echo 示例:
echo    venv\Scripts\python txt2srt.py audio.mp3 text.txt
echo ========================================
echo.
pause

