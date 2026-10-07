# Reconstruct the original directory tree from the flat repository.
#
# Reads FILE_INDEX.csv (flat_name -> original_path) and COPIES every file into
# its original location under -Destination (default ./_restored). The flat
# folder is never modified.
#
# CSV mirrors (category == "data_mirror") and flat-review docs (category ==
# "review_doc", which have no original path) are skipped.
[CmdletBinding()]
param(
    [string]$Destination = "./_restored",
    [string]$Index = "$PSScriptRoot/FILE_INDEX.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Index)) {
    throw "FILE_INDEX.csv not found at $Index"
}

$destRoot = [System.IO.Path]::GetFullPath((Join-Path $PWD $Destination))
New-Item -ItemType Directory -Force -Path $destRoot | Out-Null

$restored = 0
$skipped = 0
$missing = 0

Import-Csv -LiteralPath $Index | ForEach-Object {
    if ($_.category -in @("data_mirror", "review_doc")) { $skipped++; return }
    $src = Join-Path $PSScriptRoot $_.flat_name
    if (-not (Test-Path -LiteralPath $src)) { $missing++; return }
    $dst = Join-Path $destRoot ($_.original_path -replace '/', [IO.Path]::DirectorySeparatorChar)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $script:restored++
}

Write-Host "restored $restored files into $destRoot"
Write-Host "skipped  $skipped csv mirrors"
if ($missing -gt 0) { Write-Host "missing  $missing (flat file absent)" }
