$ErrorActionPreference = "Stop"

docker compose up -d postgres-app | Out-Null
docker compose exec -T postgres-app sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/001_create_schemas.sql'
