@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
python -m app.ui.app
pause
