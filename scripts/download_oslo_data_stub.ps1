# Stub: download/open Norway-Oslo datasets (user-run, not executed in CI)
# See data/raw/DATA_SOURCES.md for URLs and CRS notes.

Write-Host "Production data is not bundled. Suggested steps:"
Write-Host "1. DEM: Kartverket / hoydedata.no -> data/raw/dem/"
Write-Host "2. Buildings: Oslo kommune open data -> data/raw/buildings/"
Write-Host "3. Hydro: NVE elvenett (Geonorge) -> data/raw/hydro/"
Write-Host "4. Flood labels: municipal polygons -> data/raw/floods/"
Write-Host "5. Reproject to EPSG:4326 or 25833 before raster.zonal_mean_raster_to_h3"
Write-Host "6. Set label_source=observed in processed Parquet before pluvial-train"
