#!/usr/bin/env sh
set -eu

compose="${COMPOSE_COMMAND:-docker compose}"
$compose exec -T postgres-app psql \
  -v ON_ERROR_STOP=1 \
  -U "${POSTGRES_USER:-cci}" \
  -d "${POSTGRES_DB:-cci_platform}" \
  -f /docker-entrypoint-initdb.d/001_create_schemas.sql
