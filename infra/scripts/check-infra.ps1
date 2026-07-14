$ErrorActionPreference = "Stop"

$services = @(
  "postgres-app",
  "redis",
  "rabbitmq",
  "minio",
  "temporal",
  "temporal-ui"
)

$failed = $false

foreach ($service in $services) {
  $containerId = docker compose ps -q $service
  if (-not $containerId) {
    Write-Output "${service}: ausente"
    $failed = $true
    continue
  }

  $status = docker inspect --format "{{.State.Status}}" $containerId
  $health = docker inspect --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}sem-healthcheck{{end}}" $containerId
  Write-Output "${service}: $status ($health)"

  if ($status -ne "running" -or $health -eq "unhealthy") {
    $failed = $true
  }
}

if ($failed) {
  exit 1
}
