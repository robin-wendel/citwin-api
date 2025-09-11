```bash
docker build -t citwin-api .
```

```bash
docker run -d -p 8000:8000 --name citwin-api citwin-api
```

```bash
docker start citwin-api
```

```bash
docker stop citwin-api
```

```bash
docker rm citwin-api
```