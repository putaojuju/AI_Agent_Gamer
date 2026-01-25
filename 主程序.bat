@echo off
setlocal

:: 1. 切换到当前批处理文件所在的目录 (项目根目录)
cd /d "%~dp0"

:: 2. 设置控制台编码为 UTF-8 (避免中文乱码)
chcp 65001

echoString ==========================================
echo       AI Game Agent 启动器
echo ==========================================

:: 3. 检查 Conda 环境是否激活
:: 这里假设你的环境名是 ai_agent_311，根据实际情况修改
call conda activate ai_agent_311
if %errorlevel% neq 0 (
    echo [ERROR] 无法激活 Conda 环境，请检查环境名称。
    pause
    exit /b
)

:: 4. 运行主程序
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 程序异常退出。
    pause
)