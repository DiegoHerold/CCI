#!/usr/bin/env sh
set -eu

required="postgres-app redis rabbitmq minio temporal temporal-ui"
failed=0

for service in $required; do
  container_id="$(docker compose ps -q "$service")"
  if [ -z "$container_id" ]; then
    echo "$service: ausente"
    failed=1
    continue
  fi
  status="$(docker inspect --format '{{.State.Status}}' "$container_id")"
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}sem-healthcheck{{end}}' "$container_id")"
  echo "$service: $status ($health)"
  [ "$status" = "running" ] || failed=1
  [ "$health" != "unhealthy" ] || failed=1
done

exit "$failed"
