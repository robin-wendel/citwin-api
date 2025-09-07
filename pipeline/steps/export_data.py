from pathlib import Path
from typing import Optional

import geopandas as gpd


def export_geojson(input_path: Path, output_path: Path, layer: Optional[str] = None):
    gdf = gpd.read_file(input_path, layer=layer) if layer else gpd.read_file(input_path)

    if gdf.empty:
        raise ValueError("File contains no features")

    gdf = gdf.to_crs(4326) if gdf.crs is None or gdf.crs.to_epsg() != 4326 else gdf

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")
