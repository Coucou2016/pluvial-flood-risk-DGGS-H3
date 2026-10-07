"""Profile external endpoint ownership and the downloaded raw vector snapshots."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "审查输出" / "evidence" / "source_endpoint_audit.json"

SERVICES = {
    "dep_stormwater_mirror": "https://services.arcgis.com/g8EzU2gNHvGpFUGY/ArcGIS/rest/services/New_York_City_Map_WFL1/FeatureServer",
    "streetfloodtime_311_mirror": "https://services.arcgis.com/ximI3fAlai1oq9BZ/arcgis/rest/services/streetfloodtime/FeatureServer",
    "building_view": "https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services/BUILDING_view/FeatureServer",
}


def get_json(url: str) -> dict:
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(url + sep + "f=json", headers={"User-Agent": "paper-audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def service_profile(url: str) -> dict:
    service = get_json(url)
    item_id = service.get("serviceItemId")
    item = get_json(f"https://www.arcgis.com/sharing/rest/content/items/{item_id}") if item_id else {}
    modified = item.get("modified")
    return {
        "service_url": url,
        "service_item_id": item_id,
        "layers": [x.get("name") for x in service.get("layers", [])],
        "service_description": service.get("description"),
        "service_copyright": service.get("copyrightText"),
        "item_title": item.get("title"),
        "item_owner": item.get("owner"),
        "item_org_id": item.get("orgId"),
        "item_access": item.get("access"),
        "item_license_info": item.get("licenseInfo"),
        "item_access_information": item.get("accessInformation"),
        "item_modified_utc": datetime.fromtimestamp(modified / 1000, tz=timezone.utc).isoformat() if modified else None,
    }


def vector_profile(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features", [])
    properties = [f.get("properties") or {} for f in features]
    result = {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "n_features": len(features),
        "geometry_types": dict(Counter((f.get("geometry") or {}).get("type") for f in features)),
        "property_keys": sorted(set().union(*(p.keys() for p in properties))) if properties else [],
        "source_values": sorted({str(p.get("source")) for p in properties if p.get("source") is not None}),
    }
    if any("Flooding_Category" in p for p in properties):
        result["flooding_category_counts"] = dict(Counter(str(p.get("Flooding_Category")) for p in properties))
    if any("Created_Da" in p for p in properties):
        dates = pd.to_datetime([p.get("Created_Da") for p in properties], errors="coerce")
        result["created_date_min"] = dates.min().isoformat() if dates.notna().any() else None
        result["created_date_max"] = dates.max().isoformat() if dates.notna().any() else None
        result["invalid_created_dates"] = int(dates.isna().sum())
    return result


def main() -> None:
    raw_paths = []
    for sub in ("nyc", "nyc_expanded"):
        for name in (
            "dep_stormwater_flood.geojson",
            "dep_stormwater_flood_2050slr.geojson",
            "flooding_311.geojson",
            "usgs_ida_hwm.geojson",
            "building_footprints.geojson",
            "hydro_streams.geojson",
            "fema_sandy.geojson",
        ):
            path = ROOT / "data" / "raw" / sub / name
            if path.exists():
                raw_paths.append(path)
    evidence = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "arcgis_services": {name: service_profile(url) for name, url in SERVICES.items()},
        "raw_vectors": [vector_profile(path) for path in raw_paths],
        "interpretation": {
            "dep_stormwater_mirror": "Public ArcGIS item, but item owner is not an identified NYC institutional account; no org/license/copyright metadata returned.",
            "streetfloodtime_311_mirror": "Public ArcGIS item, but item owner is not an identified NYC institutional account; no org/license/copyright metadata returned.",
            "building_view": "Public item owned by maps.nyc.data in the NYC ArcGIS organisation and carrying NYC terms of use.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
