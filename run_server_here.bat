@echo off
setlocal

cd /d "%~dp0"

set "NODE_EXE=C:\Program Files\nodejs\node.exe"
if not exist "%NODE_EXE%" (
  where node >nul 2>nul
  if errorlevel 1 (
    echo Node.js is required to run the NFL app server.
    pause
    exit /b 1
  )
  set "NODE_EXE=node"
)

echo Running NFL All-Time app server in this window...
echo Open http://127.0.0.1:8765/teams/NFLHOMEPAGE_fixed_grid.html after you see the server message.
echo.
"%NODE_EXE%" serve_app.mjs

pause
