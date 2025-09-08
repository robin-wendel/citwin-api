from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

import geopandas as gpd
import pandas as pd

from pipeline.steps.disaggregate_data import distribute_points_in_raster, disaggregate_table_to_edges
from pipeline.steps.import_data import ensure_wgs84, concat_geodataframes, compute_bbox
from pipeline.steps.netascore import update_settings, run_netascore

SETTINGS_TEMPLATE = Path("../settings_template.yml")


def run_pipeline(
        od_clusters_a: Path,
        od_clusters_b: Path,
        od_table: Path,
        stops: Path,
        job_dir: Path,
        case_id: Optional[str] = None,
        target_srid: Optional[int] = None,
        netascore_dir: Optional[Path] = None,
        settings_template: Optional[Path] = None,
        netascore_file: Optional[Path] = None,
        seed: Optional[int] = None,
) -> Dict[str, Path]:
    od_clusters_a_gdf = ensure_wgs84(gpd.read_file(od_clusters_a))
    od_clusters_b_gdf = ensure_wgs84(gpd.read_file(od_clusters_b))
    od_table_df = pd.read_csv(od_table, delimiter=';')

    od_points_a_gdf = distribute_points_in_raster(
        polygon_gdf=od_clusters_a_gdf,
        id_field="klynge_id",
        count_field="Beboere",
        seed=seed,
    )

    od_points_b_gdf = distribute_points_in_raster(
        polygon_gdf=od_clusters_b_gdf,
        id_field="klynge_id",
        count_field="Arbejdere",
        seed=seed,
    )

    od_edges_gdf = disaggregate_table_to_edges(
        od_points_a_gdf=od_points_a_gdf,
        od_points_b_gdf=od_points_b_gdf,
        od_table_df=od_table_df,
        od_table_a_id_field="Bopael_klynge_id",
        od_table_b_id_field="Arbejssted_klynge_id",
        od_table_trips_field="Antal",
        seed=seed,
    )

    od_points_a_gdf.to_file(job_dir / "od_points_a.gpkg", driver="GPKG")
    od_points_b_gdf.to_file(job_dir / "od_points_b.gpkg", driver="GPKG")
    print("[od_points] finished")
    od_edges_gdf.to_file(job_dir / "od_edges.gpkg", driver="GPKG")
    print("[od_edges] finished")

    od_clusters_gdf = concat_geodataframes(od_clusters_a_gdf, od_clusters_b_gdf)
    bbox_str, bbox_srid = compute_bbox(od_clusters_gdf)
    print(f"[bbox_str] {bbox_str}")
    print(f"[bbox_srid] {bbox_srid}")

    target_srid = target_srid or bbox_srid
    print(f"[target_srid] {target_srid}")

    # netascore
    if netascore_file is None and netascore_dir is None:
        raise ValueError("provide either netascore_dir or netascore_file")

    case_id = case_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

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

    graph_edges_gdf = ensure_wgs84(gpd.read_file(netascore, layer="edge"))
    graph_edges_gdf.to_file(job_dir / "graph_edges.gpkg", driver="GPKG")
    print("[graph_edges] finished")

    graph_nodes_gdf = ensure_wgs84(gpd.read_file(netascore, layer="node"))
    graph_nodes_gdf.to_file(job_dir / "graph_nodes.gpkg", driver="GPKG")
    print("[graph_nodes] finished")

    stops_gdf = ensure_wgs84(gpd.read_file(stops))
    stops_gdf.to_file(job_dir / "stops_updated.gpkg", driver="GPKG")
    print("[stops_updated] finished")

    return {
        "graph_edges": job_dir / "graph_edges.gpkg",
        "graph_nodes": job_dir / "graph_nodes.gpkg",
        "stops_updated": job_dir / "stops_updated.gpkg",
    }


def main():
    od_clusters_a = Path("../data/b_klynger.gpkg")
    od_clusters_b = Path("../data/a_klynger.gpkg")
    od_table = Path("../data/Data_2023_0099_Tabel_1.csv")
    stops = Path("../data/dynlayer.gpkg")
    job_dir = Path("../jobs/manual")
    target_srid = 32632
    # netascore_dir = Path("/Users/robinwendel/Developer/mobility-lab/netascore")
    netascore_file = Path("../data/netascore_20250908_181654.gpkg")

    job_dir.mkdir(parents=True, exist_ok=True)

    run_pipeline(
        od_clusters_a=od_clusters_a,
        od_clusters_b=od_clusters_b,
        od_table=od_table,
        stops=stops,
        job_dir=job_dir,
        target_srid=target_srid,
        # netascore_dir=netascore_dir,
        netascore_file=netascore_file,
        seed=None,
    )


if __name__ == "__main__":
    main()
