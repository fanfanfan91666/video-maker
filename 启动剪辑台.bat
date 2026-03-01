@echo off
title 自动化视频剪辑工作台
color 0A
echo 🚀 正在启动视频剪辑工作台，请稍候...
echo.

:: 切换到脚本所在的当前目录
cd /d "%~dp0"

:: 激活 PyCharm 的虚拟环境 (确保调用正确的库)
call .venv\Scripts\activate

:: 启动 Streamlit
streamlit run web_ui.py

pause