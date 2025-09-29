@echo off

REM Usage: start.bat [CONDA_ENV] [API_PORT] [API_ROOT_PATH]

SET CONDA_ENV=%1 IF "%CONDA_ENV%"=="" SET CONDA_ENV="citwin-api"
SET API_PORT=%2 IF "%API_PORT%"=="" SET API_PORT="8000"
SET API_ROOT_PATH=%3 IF "%API_ROOT_PATH%"=="" SET API_ROOT_PATH="/"

REM Activate Conda environment
CALL C:\ProgramData\miniconda3\Scripts\activate.bat "%CONDA_ENV%"

REM Change to app directory
CD /D "%~dp0"

REM Start Uvicorn server
python -m uvicorn api:app --host localhost --port "%API_PORT%" --root-path "%API_ROOT_PATH%" --workers 1
