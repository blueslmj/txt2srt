@echo off
setlocal
REM 启动Tkinter桌面界面

chcp 65001 > nul 2>&1
cd /d "%~dp0"

REM 所有模型和临时文件均保存在项目目录
set "TXT2SRT_PROJECT_ROOT=%~dp0"
set "TXT2SRT_MODELS_DIR=%~dp0models"
set "TXT2SRT_WHISPER_DOWNLOAD_ROOT=%~dp0models\openai-whisper"
set "HF_HOME=%~dp0models\huggingface"
set "HF_HUB_CACHE=%~dp0models\faster-whisper"
set "HUGGINGFACE_HUB_CACHE=%~dp0models\faster-whisper"
set "HF_ASSETS_CACHE=%~dp0models\huggingface-assets"
set "HF_XET_CACHE=%~dp0models\huggingface-xet"
set "TORCH_HOME=%~dp0models\torch"
set "XDG_CACHE_HOME=%~dp0models\misc"
set "GRADIO_TEMP_DIR=%~dp0.runtime\gradio"
set "NUMBA_CACHE_DIR=%~dp0.runtime\numba"
set "MPLCONFIGDIR=%~dp0.runtime\matplotlib"
set "CUDA_CACHE_PATH=%~dp0.runtime\nvidia"
set "TRITON_CACHE_DIR=%~dp0.runtime\triton"
set "TORCHINDUCTOR_CACHE_DIR=%~dp0.runtime\torchinductor"
set "TEMP=%~dp0.runtime\temp"
set "TMP=%~dp0.runtime\temp"

if not exist "models" mkdir "models"
if not exist ".runtime\temp" mkdir ".runtime\temp"

echo ========================================
echo 音频-文本对齐工具 - 启动桌面界面
echo ========================================
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先运行 setup.bat
    pause
    exit /b 1
)

echo 正在启动桌面界面...
echo.

REM 运行Tkinter UI
venv\Scripts\python.exe txt2srt_tkinter_ui.py

pause

