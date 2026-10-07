import h3
from h3 import LatLngPoly

from pluvial_flood_risk.h3_grid import bbox_to_cells, cell_center, cell_centers


def test_bbox_to_cells_nonempty():
    cells = bbox_to_cells(10.70, 59.90, 10.75, 59.95, 9)
    assert len(cells) > 10
    lon, lat = cell_center(cells[0])
    assert 10.6 < lon < 10.9
    assert 59.8 < lat < 60.0


def test_bbox_to_cells_matches_geo_to_cells():
    bbox = (10.70, 59.90, 10.85, 59.98)
    min_lon, min_lat, max_lon, max_lat = bbox
    ring = [
        (min_lat, min_lon),
        (min_lat, max_lon),
        (max_lat, max_lon),
        (max_lat, min_lon),
        (min_lat, min_lon),
    ]
    expected = sorted(h3.geo_to_cells(LatLngPoly(ring), 9))
    assert bbox_to_cells(*bbox, 9) == expected


def test_cell_centers_batch():
    cells = bbox_to_cells(10.70, 59.90, 10.72, 59.92, 9)[:5]
    lons, lats = cell_centers(cells)
    assert len(lons) == len(cells)
    lon0, lat0 = cell_center(cells[0])
    assert lons[0] == lon0
    assert lats[0] == lat0
