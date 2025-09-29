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
cd C:\scripts\netascore
conda env create -f environment.yml
conda activate netascore
conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\netascore\Library\share\proj
```

```batch
cd C:\scripts\netascore
conda run -n netascore python generate_index.py data/settings.yml
```

## 4. Deploy CITWIN API: Production

```batch
git clone -b prod https://github.com/robin-wendel/citwin-api.git C:\scripts\citwin-api
```

```batch
cd C:\scripts\citwin-api
git fetch --all
git reset --hard origin/prod
```

```batch
cd C:\scripts\citwin-api
copy config\.env.prod.example .env
```

```batch
cd C:\scripts\citwin-api
conda env create -n citwin-api -f environment.yml
conda activate citwin-api
conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\citwin-api\Library\share\proj
```

```batch
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE citwin_api_netascore"
```

```batch
nssm install citwin-api "C:\scripts\citwin-api\start.bat" "citwin-api" "8002" "/api/citwin"
nssm set citwin-api AppDirectory "C:\scripts\citwin-api"
nssm set citwin-api AppExit Default Restart
nssm set citwin-api AppStdout "C:\logs\citwin-api-out.log"
nssm set citwin-api AppStderr "C:\logs\citwin-api-err.log"
nssm start citwin-api
```

## 5. Deploy CITWIN API: Development

```batch
git clone -b dev https://github.com/robin-wendel/citwin-api.git C:\scripts\citwin-api-dev
```

```batch
cd C:\scripts\citwin-api-dev
git fetch --all
git reset --hard origin/dev
```

```batch
cd C:\scripts\citwin-api-dev
copy config\.env.dev.example .env
```

```batch
cd C:\scripts\citwin-api-dev
conda env create -n citwin-api-dev -f environment.yml
conda activate citwin-api-dev
conda env config vars set PROJ_LIB=C:\ProgramData\miniconda3\envs\citwin-api-dev\Library\share\proj
```

```batch
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE citwin_api_netascore_dev"
```

```batch
nssm install citwin-api-dev "C:\scripts\citwin-api-dev\start.bat" "citwin-api-dev" "9002" "/api/citwin-dev"
nssm set citwin-api-dev AppDirectory "C:\scripts\citwin-api-dev"
nssm set citwin-api-dev AppExit Default Restart
nssm set citwin-api-dev AppStdout "C:\logs\citwin-api-dev-out.log"
nssm set citwin-api-dev AppStderr "C:\logs\citwin-api-dev-err.log"
nssm start citwin-api-dev
```

## 6. Stop / Remove Services (Optional)

```batch
nssm stop citwin-api
nssm remove citwin-api confirm
```

```batch
nssm stop citwin-api-dev
nssm remove citwin-api-dev confirm
```
