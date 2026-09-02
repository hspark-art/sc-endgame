@echo off
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0.."
set "PY=python"
%PY% -c "import sys" >nul 2>&1
if errorlevel 1 set "PY=py -3"
%PY% -c "import sys" >nul 2>&1
if errorlevel 1 set "PY=python3"
if not exist logs mkdir logs
echo [%date% %time%] winners doc import >> logs\gdoc-import.log
%PY% "tools\gdoc_import.py" >> logs\gdoc-import.log 2>&1
