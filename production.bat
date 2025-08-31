@echo off
echo ========================================
echo    TTS CLIENT SERVER - PRODUCTION
echo ========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting production server with Socket.IO support...
echo Server will be accessible from:
echo - Localhost: http://127.0.0.1:5000
echo - Network: http://192.168.10.5:5000
echo.
echo Socket.IO is enabled for real-time communication
echo Press Ctrl+C to stop the server
echo.

python eventlet_server.py

pause
