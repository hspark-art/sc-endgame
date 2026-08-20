@echo off
chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

rem === Apply Sheet Deletions (endgame automation) ===
rem Run this AFTER you intentionally delete matches/rows from the Google Sheet.
rem It previews what will be removed, asks for confirmation, then updates the site.

set "PY=python"
%PY% -c "import sys" >nul 2>&1
if errorlevel 1 set "PY=py -3"
%PY% -c "import sys" >nul 2>&1
if errorlevel 1 set "PY=python3"

%PY% "tools\apply_delete.py"
