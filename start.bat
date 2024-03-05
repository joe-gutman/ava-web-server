@echo off

REM Change to the directory containing the script
cd /d %~dp0

REM Build the main server Docker image
docker build -t ava-server ../server

REM Start the main server in Docker
start /b docker run -d -p 8080:8080 ava-server

REM Activate the virtual environment and start the client
call client\venv\Scripts\activate.bat
start /b python client/src/main.py

REM Start the client server
start /b python client/client_server/src/main.py