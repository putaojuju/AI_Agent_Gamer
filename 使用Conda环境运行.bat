@echo off

rem 激活 ai_agent_311 环境
call "E:\Tools\Miniconda\Scripts\activate.bat" ai_agent_311

rem 显示当前环境信息
echo 当前环境:
conda info --envs | findstr "*"
python --version

rem 运行主程序
echo 运行主程序...
python main.py

rem 暂停
pause