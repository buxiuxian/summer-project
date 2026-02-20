@echo off
echo RS Agent 快速重启脚本
echo ========================

echo 检查模型预下载状态...
if not exist "%USERPROFILE%\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2" (
    echo.
    echo 警告：检测到未预下载embedding模型！
    echo 建议运行 download_models.bat 预下载模型以避免启动问题
    echo.
    set /p choice="是否现在下载模型？(Y/N): "
    if /i "!choice!"=="Y" call download_models.bat
    if /i "!choice!"=="y" call download_models.bat
)

echo 停止Python进程...
taskkill /F /IM python.exe 2>nul
echo 等待3秒...
timeout /t 3 /nobreak >nul

echo 检查端口占用...
netstat -ano | findstr :8000
if errorlevel 1 (
    echo 8000端口可用，启动服务器...
    echo.
    echo 服务器启动后将自动打开浏览器...
    echo.
    REM 在新窗口中启动延迟打开浏览器的命令
    start /min cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:8000/static/index.html"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
) else (
    echo 8000端口被占用，使用8001端口...
    echo.
    echo 服务器启动后将自动打开浏览器...
    echo.
    REM 在新窗口中启动延迟打开浏览器的命令
    start /min cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:8001/static/index.html"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
)

pause 