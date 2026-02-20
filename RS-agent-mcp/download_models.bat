@echo off
chcp 65001
echo.
echo ================================================
echo         RAG模型预下载工具
echo ================================================
echo.
echo 此脚本将预下载RAG知识库所需的5个embedding模型
echo 这样可以避免每次启动服务器时从网络下载模型
echo.
echo 需要下载的模型：
echo - all-MiniLM-L6-v2 (推荐)
echo - paraphrase-MiniLM-L6-v2
echo - paraphrase-multilingual-MiniLM-L12-v2
echo - distiluse-base-multilingual-cased  
echo - all-MiniLM-L12-v2
echo.
echo 预计下载时间：3-5分钟 (取决于网络速度)
echo 占用磁盘空间：约200MB
echo.
set /p choice="是否继续下载？(Y/N): "
if /i "%choice%"=="Y" goto :download
if /i "%choice%"=="y" goto :download
echo 下载已取消。
pause
exit /b

:download
echo.
echo 开始下载模型...
python download_models.py

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo           下载完成！
    echo ================================================
    echo.
    echo 现在您可以：
    echo 1. 离线使用RAG系统
    echo 2. 快速启动服务器（无需等待模型下载）
    echo 3. 在网络不稳定时正常使用
    echo.
    echo 下次启动服务器时，系统将自动使用本地缓存的模型。
    echo.
) else (
    echo.
    echo ================================================
    echo           下载失败！
    echo ================================================
    echo.
    echo 可能的原因：
    echo 1. 网络连接问题
    echo 2. 磁盘空间不足
    echo 3. 缺少必要的Python包
    echo.
    echo 解决方案：
    echo 1. 检查网络连接
    echo 2. 运行: pip install sentence-transformers
    echo 3. 确保有至少200MB的磁盘空间
    echo 4. 稍后重试
    echo.
)

echo 按任意键退出...
pause >nul 