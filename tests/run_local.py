from pathlib import Path
from api.pipeline.run import setup_logging, run_pipeline


TEST_DATA_DIR = Path(__file__).resolve().parents[0] / "data"

setup_logging()


def main():
    run_pipeline(
        od_clusters_a=TEST_DATA_DIR / "b_klynger.gpkg",
        od_clusters_b=TEST_DATA_DIR / "a_klynger.gpkg",
        od_table=TEST_DATA_DIR / "Data_2023_0099_Tabel_1.csv",
        stops=TEST_DATA_DIR / "dynlayer.gpkg",
        od_clusters_a_id_field="klynge_id",
        od_clusters_a_count_field="Beboere",
        od_clusters_b_id_field="klynge_id",
        od_clusters_b_count_field="Arbejdere",
        od_table_a_id_field="Bopael_klynge_id",
        od_table_b_id_field="Arbejssted_klynge_id",
        od_table_trips_field="Antal",
        stops_id_field="stopnummer",
        netascore_gpkg=TEST_DATA_DIR / "netascore_20251008_200432.gpkg",
        output_format="GPKG",
        seed=None,
    )


if __name__ == "__main__":
    main()
