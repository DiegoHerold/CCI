$ErrorActionPreference = "Stop"

if ($env:CONFIRM_RESET -ne "yes") {
  $answer = Read-Host "Esta acao remove bancos, filas e buckets locais. Digite RESET para continuar"
  if ($answer -ne "RESET") {
    Write-Output "Reset cancelado."
    exit 1
  }
}

docker compose down -v --remove-orphans
