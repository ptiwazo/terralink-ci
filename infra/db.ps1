# Pilote l'instance PostgreSQL portable locale (dev sans Docker).
# Usage : .\db.ps1 start | stop | status
#
# NOTE : ce script suppose les binaires déjà présents dans infra/pg/
# (téléchargés une fois) et le cluster initialisé dans infra/pgdata/.
# Voir README.md § « PostgreSQL portable » pour l'installation initiale.

param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("start", "stop", "status")]
  [string]$Action
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pgCtl = Join-Path $root "pg\bin\pg_ctl.exe"
$data = Join-Path $root "pgdata"
$log = Join-Path $data "server.log"

if (-not (Test-Path $pgCtl)) {
  Write-Error "Binaires Postgres absents ($pgCtl). Voir README.md."
  exit 1
}

switch ($Action) {
  "start"  { & $pgCtl -D $data -l $log -o "-p 5432" start }
  "stop"   { & $pgCtl -D $data stop -m fast }
  "status" { & $pgCtl -D $data status }
}
