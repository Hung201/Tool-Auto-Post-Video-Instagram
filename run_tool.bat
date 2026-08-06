@echo off
REM ===== Chay tool dang Instagram tu dong + tu khoi dong lai neu loi =====
REM Dat PYTHONIOENCODING=utf-8 de khong crash khi in emoji tren console Windows.
set PYTHONIOENCODING=utf-8
cd /d E:\Hung\tool-dang-insta-tu-dong
if not exist logs mkdir logs

:loop
echo [%date% %time%] === BAT DAU TOOL ===>> logs\tool.log
python main.py >> logs\tool.log 2>&1
echo [%date% %time%] === TOOL THOAT - khoi dong lai sau 60s ===>> logs\tool.log
timeout /t 60 /nobreak >nul
goto loop
