@echo off
cd /d "%~dp0"
py -3 workbench.py serve --open
if errorlevel 1 pause
