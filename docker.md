# Docker

## Docker Compose

```bash
export API_PORT=8001
docker compose up --build api
```

```bash
docker compose down
```

## Cleanup

```bash
docker builder prune -a -f
```

```bash
docker system prune -a --volumes -f
```
