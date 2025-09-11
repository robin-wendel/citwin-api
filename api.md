```bash
uvicorn api:app --workers 1 --reload
```

```bash
curl -X POST http://localhost:8000/jobs \
  -F "od_clusters_a=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/b_klynger.gpkg" \
  -F "od_clusters_b=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/a_klynger.gpkg" \
  -F "od_table=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/Data_2023_0099_Tabel_1.csv" \
  -F "stops=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/dynlayer.gpkg" \
```

```bash
curl -s http://localhost:8000/jobs/296c1ca6-5480-49aa-aed3-20c77b26665c | jq
```

```bash
curl -s http://localhost:8000/jobs/296c1ca6-5480-49aa-aed3-20c77b26665c/downloads | jq
```

```bash
curl -OJ http://localhost:8000/jobs/296c1ca6-5480-49aa-aed3-20c77b26665c/download/netascore_edges
curl -OJ http://localhost:8000/jobs/296c1ca6-5480-49aa-aed3-20c77b26665c/download/netascore_nodes
curl -OJ http://localhost:8000/jobs/296c1ca6-5480-49aa-aed3-20c77b26665c/download/stops_updated
```
