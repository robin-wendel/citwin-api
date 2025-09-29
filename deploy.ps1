param(
    [string]$RepoPath = 'C:\scripts\citwin-api',
    [string]$EnvFile = ".env.prod.example",
    [string]$CondaEnv = "citwin-api",
    [string]$CondaPath = "C:\ProgramData\miniconda3",
    [string]$Database = "citwin_api_netascore",
    [string]$Password = "<password>",
    [string]$NssmService = 'citwin-api',
    [string]$ApiPort = '8000'
    [string]$ApiRootPath = '/api/citwin'
    [string]$LogPath = 'C:\logs'
)

if (-Not (Test-Path $RepoPath)) {
    Write-Host "clone repository"
    git clone -b main https://github.com/robin-wendel/citwin-api.git $RepoPath
} else {
    Write-Host "update repository"
    Set-Location $RepoPath
    git fetch --all
    git reset --hard origin/main
}

if (-Not (Test-Path "$RepoPath\.env")) {
    Write-Host "copy .env file"
    Copy-Item "$RepoPath\config\$EnvFile" "$RepoPath\.env" -Force
}

$CondaEnvPath = "$CondaPath\envs\$CondaEnv"
if (-Not (Test-Path $CondaEnvPath)) {
    Write-Host "create conda environment"
    conda env create -n $CondaEnv -f "$RepoPath\environment.yml"
    conda run -n citwin-api conda env config vars set PROJ_LIB="$CondaEnvPath\Library\share\proj"
} else {
    # Write-Host "update conda environment"
    # conda env update -n $CondaEnv -f "$RepoPath\environment.yml"
}

$env:PGPASSWORD = $Password
$exists = psql -U postgres -h localhost -p 5432 -tAc "SELECT 1 FROM pg_database WHERE datname='$Database';"
if ($exists -ne "1") {
    Write-Host "create database"
    psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE $Database"
}

$service = Get-Service -Name $NssmService -ErrorAction SilentlyContinue
if (-Not $service) {
    Write-Host "install service"
    nssm install $NssmService "$RepoPath\start.bat" $CondaEnv $ApiPort $ApiRootPath
    nssm set $NssmService AppDirectory $RepoPath
    nssm set $NssmService AppExit Default Restart
    nssm set $NssmService AppStdout "$LogPath\$NssmService-out.log"
    nssm set $NssmService AppStderr "$LogPath\$NssmService-err.log"
    nssm start $NssmService
} else {
    Write-Host "restart service"
    nssm stop $NssmService
    nssm start $NssmService
}

Write-Host "done"
Pause
