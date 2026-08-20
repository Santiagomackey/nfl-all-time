@echo off
setlocal

cd /d "%~dp0"

set "NODE_EXE=C:\Program Files\nodejs\node.exe"
if not exist "%NODE_EXE%" (
  where node >nul 2>nul
  if errorlevel 1 (
    echo Node.js is required to run the NFL app server.
    echo Install Node.js, then run this file again.
    pause
    exit /b 1
  )
  set "NODE_EXE=node"
)

echo Starting NFL All-Time app server on http://127.0.0.1:8765 ...
start "NFL All-Time Server" cmd /k "cd /d \"%~dp0\" && \"%NODE_EXE%\" serve_app.mjs"

timeout /t 4 >nul
start "" "http://127.0.0.1:8765/teams/NFLHOMEPAGE_fixed_grid.html"

exit /b 0
