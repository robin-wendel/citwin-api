from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

import pandas as pd

from pipeline.steps.import_data import read_gdf, concat_geodataframes, compute_bbox
from pipeline.steps.netascore import update_settings, run_netascore
from pipeline.steps.export_data import export_geojson

SETTINGS_TEMPLATE = Path("../settings_template.yml")


def run_pipeline(
    od_cluster_a: Path,
    od_cluster_b: Path,
    od_table: Path,
    stops: Path,
    job_dir: Path,
    case_id: Optional[str] = None,
    target_srid: Optional[int] = None,
    netascore_dir: Optional[Path] = None,
    settings_template: Optional[Path] = None,
    netascore_file: Optional[Path] = None,
) -> Dict[str, Path]:
    if netascore_file is None and netascore_dir is None:
        raise ValueError("Provide either netascore_dir or netascore_file")

    case_id = case_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    gdf_a = read_gdf(od_cluster_a)
    gdf_b = read_gdf(od_cluster_b)
    df_t = pd.read_csv(od_table)
    gdf_s = read_gdf(stops)

    gdf_combined = concat_geodataframes(gdf_a, gdf_b)
    bbox_str, bbox_srid = compute_bbox(gdf_combined)
    print(f"[bbox_str] {bbox_str}")
    print(f"[bbox_srid] {bbox_srid}")

    target_srid = target_srid or bbox_srid
    print(f"[target_srid] {target_srid}")

    print(df_t.head())
    print(gdf_s.head())

    if netascore_file is None:
        settings_template = settings_template or SETTINGS_TEMPLATE
        settings_path = netascore_dir / "data/settings.yml"
        update_settings(settings_template, settings_path, case_id, target_srid, bbox_str)
        print(f"[settings] wrote {settings_path}")

        run_netascore(netascore_dir)
        print("[compose] finished")

        netascore = netascore_dir / "data" / f"netascore_{case_id}.gpkg"
    else:
        netascore = netascore_file

    netascore_output_path = job_dir / "export_netascore.geojson"
    export_geojson(netascore, netascore_output_path, layer="edge")
    print(f"[done] GeoJSON written: {netascore_output_path.resolve()}")

    stops_output_path = job_dir / "export_stops.geojson"
    export_geojson(stops, stops_output_path)
    print(f"[done] GeoJSON written: {stops_output_path.resolve()}")

    return {
        "netascore": netascore_output_path,
        "stops": stops_output_path,
    }


def main():
    od_cluster_a = Path("../data/od_cluster_a.gpkg")
    od_cluster_b = Path("../data/od_cluster_b.gpkg")
    od_table = Path("../data/od_table.csv")
    stops = Path("../data/stops.gpkg")
    job_dir = Path("../jobs/manual")
    target_srid = 32632
    # netascore_dir = Path("/Users/robinwendel/Developer/mobility-lab/netascore")
    netascore_file = Path("../data/netascore.gpkg")

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
