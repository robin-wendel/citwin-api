from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict

import geopandas as gpd
import pandas as pd

from pipeline.steps.build_graphs import build_graphs
from pipeline.steps.disaggregate_data import distribute_points_in_raster, disaggregate_table_to_edges
from pipeline.steps.handle_data import ensure_wgs84, concat_gdfs, compute_bbox_str, get_utm_srid
from pipeline.steps.netascore import update_settings, run_netascore
from pipeline.steps.snap_points import build_balltree, snap_with_balltree

SETTINGS_TEMPLATE = Path("../settings_template.yml")


def run_pipeline(
        od_clusters_a: Path,
        od_clusters_b: Path,
        od_table: Path,
        stops: Path,
        job_dir: Path,
        case_id: Optional[str] = None,
        netascore_dir: Optional[Path] = None,
        settings_template: Optional[Path] = None,
        netascore_gpkg: Optional[Path] = None,
        seed: Optional[int] = None,
) -> Dict[str, Path]:
    case_id = case_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # ==================================================================================================================
    # import data
    # ==================================================================================================================

    print("import data")
    od_clusters_a_gdf = ensure_wgs84(gpd.read_file(od_clusters_a))
    od_clusters_b_gdf = ensure_wgs84(gpd.read_file(od_clusters_b))
    od_table_df = pd.read_csv(od_table, delimiter=';')
    stops_gdf = ensure_wgs84(gpd.read_file(stops))

    # ==================================================================================================================
    # disaggregate data
    # ==================================================================================================================

    print("disaggregate data")
    print("  distribute points in raster")
    od_points_a_gdf = distribute_points_in_raster(od_clusters_a_gdf, "klynge_id", "Beboere", seed)
    od_points_b_gdf = distribute_points_in_raster(od_clusters_b_gdf, "klynge_id", "Arbejdere", seed)
    print("  disaggregate table to edges")
    od_edges_gdf = disaggregate_table_to_edges(od_points_a_gdf, od_points_b_gdf, od_table_df, "Bopael_klynge_id", "Arbejssted_klynge_id", "Antal", seed)

    # ==================================================================================================================
    # netascore
    # ==================================================================================================================

    if netascore_gpkg is None:
        print("netascore")
        print("  update settings")
        od_clusters_gdf = concat_gdfs(od_clusters_a_gdf, od_clusters_b_gdf)
        target_srid = get_utm_srid(od_clusters_gdf)
        bbox_str = compute_bbox_str(od_clusters_gdf)
        print("    target_srid:", target_srid)
        print("    bbox_str:", bbox_str)
        settings_template_path = settings_template or SETTINGS_TEMPLATE
        settings_path = netascore_dir / "data/settings.yml"
        update_settings(settings_template_path, settings_path, case_id, target_srid, bbox_str)

        print("  run netascore")
        run_netascore(netascore_dir)
        netascore_gpkg = netascore_dir / "data" / f"netascore_{case_id}.gpkg"

    netascore_edges_gdf = ensure_wgs84(gpd.read_file(netascore_gpkg, layer="edge"))
    netascore_nodes_gdf = ensure_wgs84(gpd.read_file(netascore_gpkg, layer="node"))

    # ==================================================================================================================
    # build graphs
    # ==================================================================================================================

    print("build graphs")
    G_base, G_base_reversed, G_quality, G_quality_reversed = build_graphs(netascore_edges_gdf, netascore_nodes_gdf, cache_dir=Path("../jobs/cache"))

    # ==================================================================================================================
    # snap points
    # ==================================================================================================================

    print("snap points")
    print("  building balltree on graph nodes")
    balltree_base, node_ids_base = build_balltree(G_base)
    balltree_quality, node_ids_quality = build_balltree(G_quality)

    print("  snapping points to graph nodes")
    od_points_a_gdf = snap_with_balltree(od_points_a_gdf, balltree_base, node_ids_base)
    od_points_b_gdf = snap_with_balltree(od_points_b_gdf, balltree_base, node_ids_base)
    stops_gdf = snap_with_balltree(stops_gdf, balltree_base, node_ids_base, node_id_field="node_id_base")
    stops_gdf = snap_with_balltree(stops_gdf, balltree_quality, node_ids_quality, node_id_field="node_id_quality")

    # ==================================================================================================================
    # export data
    # ==================================================================================================================

    print("export data")
    od_points_a_gdf.to_file(job_dir / "od_points_a.gpkg", driver="GPKG")
    od_points_b_gdf.to_file(job_dir / "od_points_b.gpkg", driver="GPKG")
    od_edges_gdf.to_file(job_dir / "od_edges.gpkg", driver="GPKG")
    stops_gdf.to_file(job_dir / "stops_updated.gpkg", driver="GPKG")
    netascore_edges_gdf.to_file(job_dir / "netascore_edges.gpkg", driver="GPKG")
    netascore_nodes_gdf.to_file(job_dir / "netascore_nodes.gpkg", driver="GPKG")

    return {
        "netascore_edges": job_dir / "netascore_edges.gpkg",
        "netascore_nodes": job_dir / "netascore_nodes.gpkg",
        "stops_updated": job_dir / "stops_updated.gpkg",
    }


def main():
    od_clusters_a = Path("../data/b_klynger.gpkg")
    od_clusters_b = Path("../data/a_klynger.gpkg")
    od_table = Path("../data/Data_2023_0099_Tabel_1.csv")
    stops = Path("../data/dynlayer.gpkg")
    job_dir = Path("../jobs/manual")
    # netascore_dir = Path("/Users/robinwendel/Developer/mobility-lab/netascore")
    netascore_gpkg = Path("../data/netascore_20250908_181654.gpkg")

    job_dir.mkdir(parents=True, exist_ok=True)

    run_pipeline(
        od_clusters_a=od_clusters_a,
        od_clusters_b=od_clusters_b,
        od_table=od_table,
        stops=stops,
        job_dir=job_dir,
        # netascore_dir=netascore_dir,
        netascore_gpkg=netascore_gpkg,
        seed=None,
    )


if __name__ == "__main__":
    main()
