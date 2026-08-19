@echo off
cd /d "%~dp0"

rem Try each python launcher and actually RUN it -- the Microsoft Store stub
rem is named python.exe but does nothing, so "where python" is not enough.
set "PY=python"
%PY% -c "import sys" >nul 2>&1
if not errorlevel 1 goto :run

set "PY=py -3"
%PY% -c "import sys" >nul 2>&1
if not errorlevel 1 goto :run

set "PY=python3"
%PY% -c "import sys" >nul 2>&1
if not errorlevel 1 goto :run

goto :nopython

:run
chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
%PY% "tools\start.py"
echo.
pause
exit /b 0

:nopython
type "tools\no-python.txt"
echo.
pause
exit /b 1
