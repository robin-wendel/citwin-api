```bash
docker build -t citwin-api .
```

```bash
docker run -d -p 8000:8000 --name citwin-api-container citwin-api
```