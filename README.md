```bash
uvicorn api:app --workers 1 --reload
```

```bash
curl -X POST http://localhost:8000/jobs \
  -F "od_cluster_a=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/od_cluster_a.gpkg" \
  -F "od_cluster_b=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/od_cluster_b.gpkg" \
  -F "od_table=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/od_table.csv" \
  -F "stops=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/stops.gpkg" \
  -F "target_srid=32632"
```

```bash
# curl http://localhost:8000/jobs/<job_id>
curl -s http://localhost:8000/jobs/ab88d1c9-c280-4a27-904f-de0707aa6680 | jq
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
