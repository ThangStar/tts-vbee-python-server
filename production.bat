@echo off
echo ========================================
echo    TTS CLIENT SERVER - PRODUCTION
echo ========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting production server...
echo Server will be accessible from:
echo - Localhost: http://127.0.0.1:5000
echo - Network: http://192.168.10.5:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python waitress_server.py

pause
