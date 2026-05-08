@echo off
chcp 65001 > nul
echo 启动文件中转站服务...
echo 访问地址: http://localhost:5200
echo 按 Ctrl+C 停止服务
echo.
cd /d "%~dp0"
D:\soft\Python\python.exe app.py
pause
