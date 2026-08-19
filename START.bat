@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title 스타크래프트 기록실

echo.
echo   스타크래프트 기록실 - 준비를 시작합니다.
echo.

rem 파이썬 찾기. 윈도우는 python / py / python3 셋 중 하나입니다.
set "PY="
where python  >nul 2>&1 && set "PY=python"  && goto :check
where py      >nul 2>&1 && set "PY=py -3"   && goto :check
where python3 >nul 2>&1 && set "PY=python3" && goto :check
goto :nopython

:check
rem 마이크로소프트 스토어 껍데기가 잡히는 일이 있어 실제로 돌아가는지 봅니다.
%PY% -c "import sys" >nul 2>&1
if errorlevel 1 goto :nopython

%PY% "tools\start.py"
echo.
echo   이 창을 닫으셔도 됩니다.
pause
exit /b 0

:nopython
echo.
echo   [!] 파이썬이 없습니다.
echo.
echo       https://www.python.org/downloads/  에서 받아 설치해 주세요.
echo       설치 화면 맨 아래 "Add Python to PATH" 를 꼭 체크하셔야 합니다.
echo.
echo       설치가 끝나면 이 창을 닫고 START.bat 을 다시 더블클릭하세요.
echo.
pause
exit /b 1
