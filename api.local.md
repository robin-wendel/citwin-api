```bash
uvicorn api:app --host localhost --port 8001 --workers 1 --reload
```

```bash
curl -X POST http://localhost:8001/jobs \
  -F "od_clusters_a=@/Users/robinwendel/Developer/mobility-lab/citwin-api/data/b_klynger.gpkg" \
  -F "od_clusters_b=@/Users/robinwendel/Developer/mobility-lab/citwin-api/data/a_klynger.gpkg" \
  -F "od_table=@/Users/robinwendel/Developer/mobility-lab/citwin-api/data/Data_2023_0099_Tabel_1.csv" \
  -F "stops=@/Users/robinwendel/Developer/mobility-lab/citwin-api/data/dynlayer.gpkg" \
  -F "od_clusters_a_id_field=klynge_id" \
  -F "od_clusters_a_count_field=Beboere" \
  -F "od_clusters_b_id_field=klynge_id" \
  -F "od_clusters_b_count_field=Arbejdere" \
  -F "od_table_a_id_field=Bopael_klynge_id" \
  -F "od_table_b_id_field=Arbejssted_klynge_id" \
  -F "od_table_trips_field=Antal" \
  -F "netascore_gpkg=@/Users/robinwendel/Developer/mobility-lab/citwin-api/data/netascore_20250908_181654.gpkg"
```

```bash
curl -s http://localhost:8001/jobs/2d219f5f-cb63-4089-98d7-4632aaaa4dde | jq
```

```bash
curl -s http://localhost:8001/jobs/2d219f5f-cb63-4089-98d7-4632aaaa4dde/downloads | jq
```

```bash
curl -OJ http://localhost:8001/jobs/2d219f5f-cb63-4089-98d7-4632aaaa4dde/download/netascore_edges
curl -OJ http://localhost:8001/jobs/2d219f5f-cb63-4089-98d7-4632aaaa4dde/download/netascore_nodes
curl -OJ http://localhost:8001/jobs/2d219f5f-cb63-4089-98d7-4632aaaa4dde/download/stops_updated
```
