@echo off
REM Activate environment
CALL C:\ProgramData\miniconda3\Scripts\activate.bat citwin-api

REM Change to app directory
CD /D C:\scripts\citwin-api

REM Start Uvicorn server
python -m uvicorn api:app --host localhost --port 8002 --workers 1 --root-path /api/citwin
