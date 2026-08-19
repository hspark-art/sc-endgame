chcp 65001 >nul 2>&1
set "PYTHONUTF8=1"
cd /d "%~dp0"

rem Practice mode - fake chat, no live broadcast needed
start "" http://localhost:8144
python tools\prizewatch.py --demo
pause
