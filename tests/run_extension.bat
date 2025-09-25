@echo off
cd /d "%~dp0"
python key_movement.py --port %1
pause