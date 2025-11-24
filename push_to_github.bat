@echo off
chcp 65001 >nul
echo ========================================
echo 正在推送到GitHub...
echo ========================================
echo.

echo [1/4] 检查远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/blueslmj/txt2srt.git
if %errorlevel% neq 0 (
    echo 错误: 无法添加远程仓库
    pause
    exit /b 1
)
echo ✓ 远程仓库已添加

echo.
echo [2/4] 检查分支...
git branch -M main
echo ✓ 分支已设置为 main

echo.
echo [3/4] 推送代码到GitHub（强制覆盖远程仓库）...
echo 注意: 这会覆盖GitHub上的README文件
git push -u origin main --force
if %errorlevel% neq 0 (
    echo.
    echo 错误: 推送失败
    echo 可能需要在GitHub上进行身份验证
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ 推送完成！
echo ========================================
echo.
echo 你的项目已发布到: https://github.com/blueslmj/txt2srt
echo.
pause

