import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import geopandas as gpd
import pandas as pd
import yaml

SETTINGS_TEMPLATE = Path("./settings_template.yml")

def get_utm_srid_from_bounds(minx: float, miny: float, maxx: float, maxy: float) -> int:
    center_lon = (minx + maxx) / 2
    center_lat = (miny + maxy) / 2

    zone = int((center_lon + 180) / 6) + 1

    if center_lat >= 0:
        return 32600 + zone
    else:
        return 32700 + zone

def update_settings(settings_template_path: Path, out_settings_path: Path, bbox_str: str, target_srid: int, case_id: str = None) -> None:
    with open(settings_template_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}
    if case_id is not None:
        settings["global"]["case_id"] = case_id
    settings["global"]["target_srid"] = int(target_srid)
    settings["import"]["bbox"] = bbox_str
    out_settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_settings_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False, allow_unicode=True)

def run_netascore(netascore_dir: Path) -> None:
    cmd = ["docker", "compose", "run", "--rm", "netascore", "data/settings.yml"]
    print(f"[compose] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=netascore_dir, check=True)

def export_netascore(netascore_path: Path, out_path: Path):
    if not netascore_path.exists():
        raise FileNotFoundError(f"GPKG file not found: {netascore_path}")
    gdf = gpd.read_file(netascore_path, layer="edge")
    if gdf.empty:
        raise ValueError(f"Layer 'edge' in {netascore_path} contains no features")
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GeoJSON")

def export_stops(stops_path: Path, out_path: Path):
    if not stops_path.exists():
        raise FileNotFoundError(f"Stops file not found: {stops_path}")
    gdf = gpd.read_file(stops_path)
    if gdf.empty:
        raise ValueError(f"{stops_path} contains no features")
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GeoJSON")

def run_pipeline(
    od_cluster_a: Path,
    od_cluster_b: Path,
    od_table: Path,
    stops: Path,
    job_dir: Path,
    case_id: str = None,
    target_srid: int = None,
    netascore_dir: Optional[Path] = None,
    settings_template: Optional[Path] = None,
    netascore_file: Optional[Path] = None,
) -> Dict[str, Path]:
    if netascore_file is None and netascore_dir is None:
        raise ValueError("You must provide either netascore_dir or netascore_file")

    case_id = case_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # 1) compute bbox
    gdf_a = gpd.read_file(od_cluster_a)
    gdf_b = gpd.read_file(od_cluster_b)

    if gdf_a.crs is None or gdf_a.crs.to_epsg() != 4326:
        gdf_a = gdf_a.to_crs(4326)
    if gdf_b.crs is None or gdf_b.crs.to_epsg() != 4326:
        gdf_b = gdf_b.to_crs(4326)

    gdf_combined = pd.concat([gdf_a, gdf_b], ignore_index=True)

    minx, miny, maxx, maxy = gdf_combined.total_bounds
    bbox_str = f"{miny:.4f},{minx:.4f},{maxy:.4f},{maxx:.4f}"
    print(f"[bbox] {bbox_str}")

    target_srid = target_srid or get_utm_srid_from_bounds(*gdf_combined.total_bounds)
    print(f"[target_srid] {target_srid}")

    if netascore_file is None:
        # 2) update settings
        settings_template = settings_template or SETTINGS_TEMPLATE
        settings_path = netascore_dir / "data" / "settings.yml"
        update_settings(settings_template, settings_path, bbox_str, target_srid, case_id)
        print(f"[settings] wrote {settings_path}")

        # 3) run NetAScore
        run_netascore(netascore_dir)
        print("[compose] finished")

        # 4) export NetAScore
        netascore = netascore_dir / "data" / f"netascore_{case_id}.gpkg"
    else:
        # 4) export NetAScore
        netascore = netascore_file

    # 4) export NetAScore
    out_netascore_path = job_dir / "export_netascore.geojson"
    export_netascore(netascore, out_netascore_path)
    print(f"[done] GeoJSON written: {out_netascore_path.resolve()}")

    # 5) export stops
    out_stops_path = job_dir / f"export_stops.geojson"
    export_stops(stops, out_stops_path)
    print(f"[done] GeoJSON written: {out_stops_path.resolve()}")

    return {
        "netascore": out_netascore_path,
        "stops": out_stops_path,
    }

def main():
    od_cluster_a = Path("./data/od_cluster_a.gpkg")
    od_cluster_b = Path("./data/od_cluster_b.gpkg")
    od_table = Path("./data/od_table.csv")
    stops = Path("./data/stops.gpkg")
    job_dir = Path("./jobs/manual")
    target_srid = 32632
    # netascore_dir = Path("/Users/robinwendel/Developer/mobility-lab/netascore")
    netascore_file = Path("./data/netascore.gpkg")

    job_dir.mkdir(parents=True, exist_ok=True)

    run_pipeline(
        od_cluster_a=od_cluster_a,
        od_cluster_b=od_cluster_b,
        od_table=od_table,
        stops=stops,
        job_dir=job_dir,
        target_srid=target_srid,
        # netascore_dir=netascore_dir,
        netascore_file=netascore_file,
    )

if __name__ == "__main__":
    main()
