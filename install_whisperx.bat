@echo off
chcp 65001 >nul
echo ========================================
echo 安装 WhisperX 依赖
echo ========================================
echo.

echo [1/3] 检查 Python 版本...
venv\Scripts\python --version
echo.

echo [2/3] 安装 WhisperX...
echo 注意: 这可能需要几分钟时间
echo.

venv\Scripts\pip install whisperx

if %errorlevel% neq 0 (
    echo.
    echo ❌ WhisperX 安装失败
    echo 可能需要手动安装一些依赖:
    echo   1. 确保 CUDA 已安装
    echo   2. 确保 FFmpeg 已安装
    echo   3. 尝试: pip install git+https://github.com/m-bain/whisperx.git
    pause
    exit /b 1
)

echo.
echo [3/3] 验证安装...
venv\Scripts\python -c "import whisperx; print('WhisperX 版本:', whisperx.__version__)"

if %errorlevel% neq 0 (
    echo ❌ WhisperX 导入失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ WhisperX 安装成功！
echo.
echo 使用方法:
echo   venv\Scripts\python txt2srt_whisperx.py [音频] [文本]
echo ========================================
pause

