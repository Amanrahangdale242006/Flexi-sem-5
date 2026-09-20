@echo off
title AutoSchedule AI - Public Server Launcher
cd /d "%~dp0"

echo =====================================================================
echo           Starting AutoSchedule AI & Public Cloudflare Tunnel
echo =====================================================================
echo.

:: 1. Start Python FastAPI Server in background
echo [*] Starting Python backend server...
start /B python run.py > server.log 2>&1

:: Wait 3 seconds for server to start
timeout /t 3 /nobreak >nul

:: 2. Start Cloudflare Public Tunnel
echo [*] Starting Public Cloudflare Tunnel...
echo.
echo =====================================================================
echo  Your website is being published to the internet!
echo =====================================================================
echo.

.\cloudflared.exe tunnel --url http://127.0.0.1:8000
