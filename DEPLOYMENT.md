# CITWIN API Deployment

## 1. Overview

| Deployment | Git Branch | Folder                    | Conda Environment | Service        | Port | Web Route       | .env File         |
|------------|------------|---------------------------|-------------------|----------------|------|-----------------|-------------------|
| Stable     | stable     | C:\scripts\citwin-api     | citwin-api        | citwin-api     | 8002 | /api/citwin     | config\stable.env |
| Dev        | dev        | C:\scripts\citwin-api-dev | citwin-api-dev    | citwin-api-dev | 9002 | /api/citwin/dev | config\dev.env    |

## 2. Prerequisites

- Install NSSM: https://nssm.cc/download, install to C:\nssm, add to Path
- Install osm2pgsql: https://osm2pgsql.org, install to C:\osm2pgsql, add to Path

## 3. Set up NetAScore

```powershell
git clone -b maintenance-25 https://github.com/plus-mobilitylab/netascore.git C:\scripts\netascore
cd C:\scripts\netascore
```

```powershell
conda env create -f environment.yml
conda activate netascore
conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\netascore\Library\share\proj
```

```powershell
conda run -n netascore python generate_index.py data/settings.yml
```

## 4. Deploy CITWIN API: Stable

```powershell
git clone -b stable https://github.com/robin-wendel/citwin-api.git C:\scripts\citwin-api
cd C:\scripts\citwin-api
```

```powershell
conda env create -n citwin-api -f environment.yml
conda activate citwin-api
conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\citwin-api\Library\share\proj
```

```powershell
nssm install citwin-api "C:\scripts\citwin-api\start.bat" stable
nssm set citwin-api AppDirectory "C:\scripts\citwin-api"
nssm set citwin-api AppExit Default Restart
nssm set citwin-api AppStdout "C:\logs\citwin-api-stable-out.log"
nssm set citwin-api AppStderr "C:\logs\citwin-api-stable-err.log"
nssm start citwin-api
```

## 5. Deploy CITWIN API: Dev

```powershell
git clone -b dev https://github.com/robin-wendel/citwin-api.git C:\scripts\citwin-api-dev
cd C:\scripts\citwin-api-dev
```

```powershell
conda env create -n citwin-api-dev -f environment.yml
conda activate citwin-api-dev
conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\citwin-api-dev\Library\share\proj
```

```powershell
nssm install citwin-api-dev "C:\scripts\citwin-api-dev\start.bat" dev
nssm set citwin-api-dev AppDirectory "C:\scripts\citwin-api-dev"
nssm set citwin-api-dev AppExit Default Restart
nssm set citwin-api-dev AppStdout "C:\logs\citwin-api-dev-out.log"
nssm set citwin-api-dev AppStderr "C:\logs\citwin-api-dev-err.log"
nssm start citwin-api-dev
```

## 6. Stop / Remove Services (Optional)

```powershell
nssm stop citwin-api
nssm remove citwin-api
```

```powershell
nssm stop citwin-api-dev
nssm remove citwin-api-dev
```
