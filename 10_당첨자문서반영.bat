@echo off
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

rem === Import winners from the Google Doc into the admin winners sheet ===
rem Adds only new winners (already-listed ones are skipped). Safe to run anytime.

set "PY=python"
%PY% -c "import sys" >nul 2>&1
if errorlevel 1 set "PY=py -3"
%PY% -c "import sys" >nul 2>&1
if errorlevel 1 set "PY=python3"

%PY% "tools\gdoc_import.py"
echo.
pause
