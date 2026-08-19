$ErrorActionPreference = "Stop"
$dir = "E:\Projects\20260522-pluvial-flood-risk-DGGS-H3\.upload_chunks"
if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
New-Item -ItemType Directory -Path $dir | Out-Null
$files = @{
  "manuscript.md" = "docs\paper\manuscript.md";
  "audit.md"      = "docs\paper\audit.md";
  "figures.py"    = "src\pluvial_flood_risk\figures.py"
}
foreach ($name in $files.Keys) {
  $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $files[$name]))
  $b64 = [Convert]::ToBase64String($bytes)
  $chunkSize = 40000
  $parts = [Math]::Ceiling($b64.Length / $chunkSize)
  for ($k = 0; $k -lt $parts; $k++) {
    $start = $k * $chunkSize
    $len = [Math]::Min($chunkSize, $b64.Length - $start)
    $chunk = $b64.Substring($start, $len)
    [System.IO.File]::WriteAllText("$dir\$name.$k.txt", $chunk, (New-Object System.Text.UTF8Encoding($false)))
  }
  Write-Host ("{0}: {1} chunk(s), base64 length {2}" -f $name, $parts, $b64.Length)
}
