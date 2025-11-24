@echo off
REM 运行示例的快捷脚本

echo ========================================
echo 音频-文本对齐工具 - 运行示例
echo ========================================
echo.

REM 检查虚拟环境是否存在
if not exist "venv\" (
    echo [错误] 虚拟环境不存在，请先运行 setup.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

echo 使用方法示例:
echo.
echo 1. 基本使用（需要准备音频和文本文件）:
echo    venv\Scripts\python txt2srt.py audio.mp3 text.txt
echo.
echo 2. 指定输出文件:
echo    venv\Scripts\python txt2srt.py audio.mp3 text.txt -o output.srt
echo.
echo 3. 使用更大的模型:
echo    venv\Scripts\python txt2srt.py audio.mp3 text.txt -m medium
echo.
echo 4. 英文音频:
echo    venv\Scripts\python txt2srt.py audio.mp3 text.txt -l en
echo.
echo 请准备好音频文件和文本文件后运行上述命令
echo.

REM 如果提供了参数，直接运行
if "%~1"=="" (
    pause
) else (
    venv\Scripts\python txt2srt.py %*
)

