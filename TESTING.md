# CITWIN API Testing

## 1. Local Testing

```bash
uvicorn api.api:app --host localhost --port 8000 --workers 1 --reload
```

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" \
  -F "od_clusters_a=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/b_klynger.gpkg" \
  -F "od_clusters_b=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/a_klynger.gpkg" \
  -F "od_table=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/Data_2023_0099_Tabel_1.csv" \
  -F "stops=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/dynlayer.gpkg" \
  -F "od_clusters_a_id_field=klynge_id" \
  -F "od_clusters_a_count_field=Beboere" \
  -F "od_clusters_b_id_field=klynge_id" \
  -F "od_clusters_b_count_field=Arbejdere" \
  -F "od_table_a_id_field=Bopael_klynge_id" \
  -F "od_table_b_id_field=Arbejssted_klynge_id" \
  -F "od_table_trips_field=Antal" \
  -F "stops_id_field=stopnummer" \
  -F "netascore_gpkg=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/netascore_20251008_200432.gpkg" \
  -F "output_format=GPKG" | jq
```

```bash
curl -s http://localhost:8000/jobs/<JOB_ID> \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq
```

```bash
curl -s http://localhost:8000/jobs/<JOB_ID>/downloads \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq
```

```bash
curl -OJ http://localhost:8000/jobs/<JOB_ID>/download/netascore_gpkg \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq
  
curl -OJ http://localhost:8000/jobs/<JOB_ID>/download/stops_updated \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq
```

## 2. Remote Testing

```bash
curl -X POST https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" \
  -F "od_clusters_a=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/b_klynger.gpkg" \
  -F "od_clusters_b=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/a_klynger.gpkg" \
  -F "od_table=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/Data_2023_0099_Tabel_1.csv" \
  -F "stops=@/Users/robinwendel/Developer/mobility-lab/citwin-api/tests/data/dynlayer.gpkg" \
  -F "od_clusters_a_id_field=klynge_id" \
  -F "od_clusters_a_count_field=Beboere" \
  -F "od_clusters_b_id_field=klynge_id" \
  -F "od_clusters_b_count_field=Arbejdere" \
  -F "od_table_a_id_field=Bopael_klynge_id" \
  -F "od_table_b_id_field=Arbejssted_klynge_id" \
  -F "od_table_trips_field=Antal" \
  -F "output_format=GPKG" | jq
```

```bash
curl -s https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/<JOB_ID> \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq
```

```bash
curl -s https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/<JOB_ID>/downloads \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq
```

```bash
curl -OJ https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/<JOB_ID>/download/netascore_gpkg \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq

curl -OJ https://mobilitylab.geo.sbg.ac.at/api/citwin/jobs/<JOB_ID>/download/stops_updated \
  -H "Authorization: Bearer 59c65fda55209fffb2cdcdb3a374a47f15032cfee26090cbeacf6c8f032f5b1a" | jq
```
