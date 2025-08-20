```bash
uvicorn api:app --reload
```

```bash
curl -X POST http://localhost:8000/jobs \
  -F "file=@/Users/robinwendel/Developer/mobility-lab/netascore-api/data/b_klynger_select.gpkg" \
  -F "target_srid=32632"
```

```bash
curl http://localhost:8000/jobs/<job_id>
```
