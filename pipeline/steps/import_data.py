from typing import Tuple

import geopandas as gpd
import pandas as pd


def ensure_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        return gdf.to_crs(4326)
    return gdf


def concat_geodataframes(*gdfs: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    df = pd.concat(gdfs, ignore_index=True)
    return gpd.GeoDataFrame(df)


def compute_bbox(gdf: gpd.GeoDataFrame) -> Tuple[str, int]:
    minx, miny, maxx, maxy = gdf.total_bounds
    bbox = f"{miny:.4f},{minx:.4f},{maxy:.4f},{maxx:.4f}"
    return bbox, get_utm_srid_from_bbox(minx, miny, maxx, maxy)


def get_utm_srid_from_bbox(minx: float, miny: float, maxx: float, maxy: float) -> int:
    center_lon = (minx + maxx) / 2
    center_lat = (miny + maxy) / 2
    zone = int((center_lon + 180) / 6) + 1
    return 32600 + zone if center_lat >= 0 else 32700 + zone
