import subprocess
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import yaml

SETTINGS_TEMPLATE = Path("./settings_template.yml")

def compute_bbox(vector_path: Path):
    gdf = gpd.read_file(vector_path)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    minx, miny, maxx, maxy = gdf.total_bounds
    return minx, miny, maxx, maxy

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

def export_result(gpkg_path: Path, out_geojson_path: Path):
    if not gpkg_path.exists():
        raise FileNotFoundError(f"GPKG file not found: {gpkg_path}")
    gdf = gpd.read_file(gpkg_path, layer="edge")
    if gdf.empty:
        raise ValueError(f"Layer 'edge' in {gpkg_path} contains no features")
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    out_geojson_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_geojson_path, driver="GeoJSON")

def run_pipeline(vector_path: Path, netascore_dir: Path, job_dir: Path, target_srid: int, settings_template: Path = SETTINGS_TEMPLATE, case_id: str = None) -> Path:
    case_id = case_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # 1) compute bbox
    minx, miny, maxx, maxy = compute_bbox(vector_path)
    bbox_str = f"{miny:.4f},{minx:.4f},{maxy:.4f},{maxx:.4f}"
    print(f"[bbox] {bbox_str}")

    # 2) update settings
    settings_path = netascore_dir / "data" / "settings.yml"
    update_settings(settings_template, settings_path, bbox_str, target_srid, case_id)
    print(f"[settings] wrote {settings_path}")

    # 3) run NetAScore
    run_netascore(netascore_dir)
    print("[compose] finished")

    # 4) export result
    gpkg_name = f"netascore_{case_id}.gpkg"
    gpkg_path = netascore_dir / "data" / gpkg_name
    out_geojson_path = job_dir / f"netascore_edge_{case_id}.geojson"

    export_result(gpkg_path, out_geojson_path)
    print(f"[done] GeoJSON written: {out_geojson_path.resolve()}")

    return out_geojson_path

def main():
    vector_path = Path("./data/b_klynger_select.gpkg")
    netascore_dir = Path("/Users/robinwendel/Developer/mobility-lab/netascore")
    job_dir = Path("./jobs/manual")
    target_srid = 32632

    job_dir.mkdir(parents=True, exist_ok=True)

    output_geojson = run_pipeline(vector_path=vector_path, netascore_dir=netascore_dir, job_dir=job_dir, target_srid=target_srid)
    print(f"GeoJSON created at: {output_geojson}")

if __name__ == "__main__":
    main()
