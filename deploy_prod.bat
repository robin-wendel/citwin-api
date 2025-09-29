@echo off

if not exist "C:\scripts\citwin-api" (
    echo clone repository
    git clone -b main https://github.com/robin-wendel/citwin-api.git C:\scripts\citwin-api
    cd /d C:\scripts\citwin-api
) else (
    echo update repository
    cd /d C:\scripts\citwin-api
    git fetch --all
    git reset --hard origin/main
)

if not exist "C:\scripts\citwin-api\.env" (
    echo copy .env file
    copy config\.env.prod.example .env
)

if not exist "C:\ProgramData\miniconda3\envs\citwin-api" (
    echo create conda environment
    conda env create -n citwin-api -f environment.yml
    call C:\ProgramData\miniconda3\Scripts\activate.bat citwin-api
    conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\citwin-api\Library\share\proj
) else (
    rem update conda environment
    rem conda env update -n citwin-api -f environment.yml
)

sc query citwin-api >nul 2>&1
if errorlevel 1060 (
    echo install service
    nssm install citwin-api "C:\scripts\citwin-api\start.bat" "citwin-api" "8002" "/api/citwin"
    nssm set citwin-api AppDirectory "C:\scripts\citwin-api"
    nssm set citwin-api AppExit Default Restart
    nssm set citwin-api AppStdout "C:\logs\citwin-api-out.log"
    nssm set citwin-api AppStderr "C:\logs\citwin-api-err.log"
    nssm start citwin-api
) else (
    echo restart service
    nssm restart citwin-api
)

echo done
pause
