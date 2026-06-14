@echo off
title AI Note Detector
echo ==============================================
echo       Starting AI Note Detector Web App
echo ==============================================
echo.
echo Please wait while the server loads...
echo.
echo Once started, open your web browser and go to: 
echo -^> http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server when you are done.
echo.
"%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe" -m uvicorn app:app
pause
