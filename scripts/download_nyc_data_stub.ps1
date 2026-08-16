# Download Lower Manhattan public layers into data/raw/nyc/ (EPSG:4326).
# Uses ArcGIS/USGS mirrors when Socrata is blocked. Not executed in CI by default.
# Does NOT download or reproduce 7Analytics PFIb.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Fetching NYC Open Data / USGS mirrors for configs/nyc.yaml bbox…"
Write-Host "Target: data/raw/nyc/  (Lower Manhattan subset — not citywide 1ft DEM)"

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

& $py (Join-Path $Root "scripts\download_nyc_data.py") @args
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Download incomplete. Fixture fallback still works:"
    Write-Host "  python scripts\build_nyc_h3.py --fixtures"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Next:"
Write-Host "  python scripts\build_nyc_h3.py --no-fixtures"
Write-Host "  pluvial-nyc-smoke"
Write-Host "See data/raw/nyc/DOWNLOAD_MANIFEST.json and data/raw/DATA_SOURCES.md"
