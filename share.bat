@echo off
echo ========================================================
echo   Starting BPS Data Parser Web & Cloudflare Tunnel...
echo ========================================================
start "BPS Web Server (Port 3000)" cmd /k "npm start"
timeout /t 2 /nobreak >nul
echo.
echo Menghubungkan ke Cloudflare Tunnel...
echo Link public akan muncul di bawah:
echo --------------------------------------------------------
.\cloudflared.exe tunnel --url http://localhost:3000

