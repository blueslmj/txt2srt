@echo off
REM Python版本检查工具

echo ========================================
echo Python 版本检查
echo ========================================
echo.

echo 正在检查Python版本...
echo.

REM 使用 py launcher 列出所有版本
echo 系统中已安装的Python版本:
echo ----------------------------------------
py --list 2>nul
if errorlevel 1 (
    echo 未找到 py launcher，尝试直接检查...
    python --version 2>nul
    if errorlevel 1 (
        echo [错误] 未找到Python安装
        goto :no_python
    )
)

echo.
echo ----------------------------------------
echo 当前默认版本:
python --version

echo.
echo ========================================
echo 版本兼容性检查
echo ========================================
echo.

REM 检查版本是否兼容
python -c "import sys; v=sys.version_info; print(f'Python {v.major}.{v.minor}.{v.micro}'); exit(0 if v>=(3,10) and v<(3,14) else 1)" 2>nul
if errorlevel 1 (
    echo ❌ 不兼容！
    echo.
    echo 本项目需要 Python 3.10-3.13
    echo 推荐：Python 3.12 或 3.13
    echo.
    echo 📖 解决方案请查看: INSTALL_FIX.md
    echo 💾 下载地址: https://www.python.org/downloads/
) else (
    echo ✅ 版本兼容！可以正常使用
    echo.
    echo 您可以继续运行 setup.bat 安装依赖
)

echo.
goto :end

:no_python
echo.
echo 未检测到Python安装
echo.
echo 请先安装 Python 3.12 或 3.13
echo 下载地址: https://www.python.org/downloads/
echo.
echo 安装时请注意勾选:
echo   ✅ Add Python to PATH
echo   ✅ Install pip

:end
echo ========================================
pause

