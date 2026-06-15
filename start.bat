@echo off
cd /d "%~dp0"
python src\main.py
if errorlevel 1 (
    echo.
    echo Ne zapustilos. Poprobuj: pip install -r requirements.txt
    pause
)
