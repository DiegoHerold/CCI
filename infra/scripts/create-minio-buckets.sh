#!/usr/bin/env sh
set -eu

alias_name="${MINIO_ALIAS:-local}"
endpoint="${MINIO_ENDPOINT:-http://minio:9000}"
buckets_file="${MINIO_BUCKETS_FILE:-/config/buckets.txt}"

mc alias set "$alias_name" "$endpoint" "${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY obrigatória}" "${MINIO_SECRET_KEY:?MINIO_SECRET_KEY obrigatória}"
while IFS= read -r bucket; do
  [ -n "$bucket" ] || continue
  mc mb --ignore-existing "$alias_name/$bucket"
done < "$buckets_file"
