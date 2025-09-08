```bash
uvicorn api:app --workers 1 --reload
```

```bash
curl -X POST http://localhost:8000/jobs \
  -F "od_clusters_a=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/b_klynger.gpkg" \
  -F "od_clusters_b=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/a_klynger.gpkg" \
  -F "od_table=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/Data_2023_0099_Tabel_1.csv" \
  -F "stops=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/dynlayer.gpkg" \
  -F "target_srid=32632" \
  # -F "seed=42"
```

```bash
# curl http://localhost:8000/jobs/<job_id>
curl -s http://localhost:8000/jobs/e005aa49-88ac-46b7-bc07-109129e5d3e4 | jq
```

```bash
# curl -s http://localhost:8000/jobs/<job_id>/downloads
curl -s http://localhost:8000/jobs/ab88d1c9-c280-4a27-904f-de0707aa6680/downloads | jq
```

```bash
# curl -OJ http://localhost:8000/jobs/<job_id>/downloads/<key>
curl -OJ http://localhost:8000/jobs/ab88d1c9-c280-4a27-904f-de0707aa6680/download/netascore
curl -OJ http://localhost:8000/jobs/ab88d1c9-c280-4a27-904f-de0707aa6680/download/stops
```
