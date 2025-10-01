## Veritix Python Service

### Run with Docker

Prerequisites: Docker and Docker Compose installed.

1) Build the image:
```bash
docker compose build
```

2) Start the stack (app + Postgres):
```bash
docker compose up -d
```

The API will be available at `http://localhost:8000`.

Health check:
```bash
curl http://localhost:8000/health
```

### Environment Variables

- `QR_SIGNING_KEY`: Secret used to sign and validate QR payloads. Defaults to `test_signing_key` in development.

### Stop and Clean Up
```bash
docker compose down
```


