#!/usr/bin/env sh
set -eu

host="${1:?uso: wait-for.sh HOST PORT [TIMEOUT]}"
port="${2:?uso: wait-for.sh HOST PORT [TIMEOUT]}"
timeout="${3:-60}"
elapsed=0

while ! nc -z "$host" "$port" >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$timeout" ]; then
    echo "timeout aguardando $host:$port" >&2
    exit 1
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done

echo "$host:$port disponível"
