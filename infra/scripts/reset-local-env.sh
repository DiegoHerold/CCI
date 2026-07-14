#!/usr/bin/env sh
set -eu

if [ "${CONFIRM_RESET:-}" != "yes" ]; then
  printf 'Esta ação remove bancos, filas e buckets locais. Digite RESET para continuar: '
  read -r answer
  [ "$answer" = "RESET" ] || { echo "Reset cancelado."; exit 1; }
fi

docker compose down -v --remove-orphans
