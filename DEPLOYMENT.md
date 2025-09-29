# CITWIN API Deployment

## 1. Overview

| Deployment  | Git Branch | Folder                    | Conda Environment | Service        | Port | Web Route       | Environment File  |
|-------------|------------|---------------------------|-------------------|----------------|------|-----------------|-------------------|
| Production  | main       | C:\scripts\citwin-api     | citwin-api        | citwin-api     | 8002 | /api/citwin     | .env.prod.example |
| Development | dev        | C:\scripts\citwin-api-dev | citwin-api-dev    | citwin-api-dev | 9002 | /api/citwin/dev | .env.dev.example  |

## 2. Prerequisites

- Install NSSM: https://nssm.cc/download, install to C:\nssm, add to Path
- Install osm2pgsql: https://osm2pgsql.org, install to C:\osm2pgsql, add to Path

## 3. Set up NetAScore

```batch
git clone -b maintenance-25 https://github.com/plus-mobilitylab/netascore.git C:\scripts\netascore
```

```batch
cd /d C:\scripts\netascore
conda env create -f environment.yml
conda activate netascore
conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\netascore\Library\share\proj
```

```batch
cd /d C:\scripts\netascore
conda run -n netascore python generate_index.py data/settings.yml
```

## 4. Deploy CITWIN API: Production

```bash
ssh b1003527@zgis244.geo.sbg.ac.at 'powershell -Command -' < deploy.ps1 `
    -RepoPath "C:\scripts\citwin-api" `
    -CondaEnv "citwin-api" `
    -Database "citwin_api_netascore" `
    -Password "s2frA-7vWd9-qnFYr" ``
    -NssmService 'citwin-api' `
    -ApiPort '8002' `
    -ApiRootPath '/api/citwin' `
```

## 5. Deploy CITWIN API: Development

```bash
ssh b1003527@zgis244.geo.sbg.ac.at 'powershell -Command -' < deploy.ps1 `
    -RepoPath "C:\scripts\citwin-api-dev" `
    -CondaEnv "citwin-api-dev" `
    -Database "citwin_api_netascore_dev" `
    -Password "s2frA-7vWd9-qnFYr" 
    -NssmService 'citwin-api-dev' `
    -ApiPort '9002' `
    -ApiRootPath '/api/citwin-dev' `
```

## 6. Stop / Remove Environments / Services (Optional)

```batch
conda env remove -n citwin-api
```

```batch
nssm stop citwin-api
nssm remove citwin-api confirm
```

```batch
conda env remove -n citwin-api-dev
```

```batch
nssm stop citwin-api-dev
nssm remove citwin-api-dev confirm
```
