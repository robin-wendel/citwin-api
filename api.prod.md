```bash
uvicorn api:app --host localhost --port 8002 --workers 1 --root-path /api/citwin
```

```bash
curl -X POST https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" \
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
  -F "od_table_trips_field=Antal"
```

```bash
curl -s https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/8c9351e0-56a3-4b07-b7c1-ddc0e2aae0fe | jq
```

```bash
curl -s https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/8c9351e0-56a3-4b07-b7c1-ddc0e2aae0fe/downloads | jq
```

```bash
curl -OJ https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/8c9351e0-56a3-4b07-b7c1-ddc0e2aae0fe/download/netascore_gpkg
curl -OJ https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/8c9351e0-56a3-4b07-b7c1-ddc0e2aae0fe/download/stops_updated
```
