@echo off
REM GPU深度诊断脚本

echo ========================================
echo GPU 深度诊断工具
echo ========================================
echo.
echo 这个工具会详细检查你的GPU配置
echo 并提供针对性的优化建议
echo.

REM 检查虚拟环境
if not exist "venv\" (
    echo [错误] 虚拟环境不存在，请先运行 setup.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 运行诊断脚本
venv\Scripts\python diagnose_gpu.py

echo.
echo ========================================
echo 建议操作:
echo ========================================
echo.
echo 如果GPU加速效果不佳:
echo 1. 参考 GPU_SETUP.md 重新配置
echo 2. 更新NVIDIA驱动
echo 3. 重新安装PyTorch GPU版本
echo.

pause

