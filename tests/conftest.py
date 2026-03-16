import sys
import zipfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point


@pytest.fixture
def sample_download_dir(tmp_path: Path) -> Path:
    """Create a temporary folder with a zipped shapefile and a fake CSV dataset."""
    map_gdf = gpd.GeoDataFrame(
        {
            "ADMIN": ["Portugal", "Spain"],
            "ISO_A3": ["PRT", "ESP"],
            "geometry": [Point(-8, 39), Point(-3, 40)],
        },
        crs="EPSG:4326",
    )

    shapefile_dir = tmp_path / "map_files"
    shapefile_dir.mkdir()

    shapefile_path = shapefile_dir / "ne_110m_admin_0_countries.shp"
    map_gdf.to_file(shapefile_path, driver="ESRI Shapefile")

    zip_path = tmp_path / "ne_110m_admin_0_countries.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        for file_path in shapefile_dir.iterdir():
            zip_file.write(file_path, arcname=file_path.name)

    df = pd.DataFrame(
        {
            "entity": ["Portugal", "Spain"],
            "code": ["PRT", "ESP"],
            "year": [2020, 2020],
            "forest_value": [12.5, 18.2],
        }
    )
    df.to_csv(tmp_path / "annual_forest_change.csv", index=False)

    return tmp_path
