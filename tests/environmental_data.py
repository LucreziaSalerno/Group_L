# app/environmental_data.py
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, Optional, Union
import requests
import time

class EnvironmentalData:
    """
    Handles downloading, loading and merging of environmental datasets
    with the world map.
    """

    # Default download URLs (you can override via constructor)
    DEFAULT_FILE_MAP = {
        "annual_forest_change.csv": "https://ourworldindata.org/grapher/annual-change-forest-area.csv?v=1&csvType=full&useColumnShortNames=true",
        "annual_deforestation.csv": "https://ourworldindata.org/grapher/annual-deforestation.csv?v=1&csvType=full&useColumnShortNames=true",
        "protected_land.csv": "https://ourworldindata.org/grapher/terrestrial-protected-areas.csv?v=1&csvType=full&useColumnShortNames=true",
        "degraded_land.csv": "https://ourworldindata.org/grapher/share-degraded-land.csv?v=1&csvType=full&useColumnShortNames=true",
        "red_list_index.csv": "https://ourworldindata.org/grapher/red-list-index.csv?v=1&csvType=full&useColumnShortNames=true",
        "ne_110m_admin_0_countries.zip": "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    }

    def __init__(
        self,
        download_dir: str = "downloads",
        file_map: Optional[Dict[str, str]] = None,
        auto_download: bool = True
    ):
        self.download_dir = Path(download_dir)
        self.file_map = file_map or self.DEFAULT_FILE_MAP.copy()
        self.dataframes: Dict[str, Union[pd.DataFrame, gpd.GeoDataFrame]] = {}

        if auto_download:
            self._download_all()

        self._load_all()

    def _download_all(self, max_retries: int = 3) -> None:
        """Download all files that are not already present."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for filename, url in self.file_map.items():
            dest = self.download_dir / filename
            if dest.exists():
                print(f"{filename} already exists, skipping download.")
                continue

            print(f"Downloading {filename} ...")
            for attempt in range(1, max_retries + 1):
                try:
                    resp = requests.get(url, timeout=30, headers=headers)
                    resp.raise_for_status()
                    with open(dest, "wb") as f:
                        f.write(resp.content)
                    print(f"  Saved to {dest}")
                    break
                except Exception as e:
                    print(f"  Attempt {attempt} failed: {e}")
                    if attempt == max_retries:
                        print(f"  Giving up on {filename}")
                    else:
                        time.sleep(2)

    def _load_all(self) -> None:
        """Load all files into DataFrames and store them in self.dataframes."""
        # Load map (geopandas)
        map_file = self.download_dir / "ne_110m_admin_0_countries.zip"
        if not map_file.exists():
            raise FileNotFoundError(f"Map file {map_file} not found. Download first.")
        self.dataframes["map"] = gpd.read_file(map_file)

        # Load CSV files
        for filename in self.file_map:
            if filename == "ne_110m_admin_0_countries.zip":
                continue
            file_path = self.download_dir / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                self.dataframes[filename] = df
            else:
                print(f"Warning: {filename} not found, skipping.")

    def get_available_years(self, dataset_key: str) -> list:
        """
        Return sorted list of years available in a given dataset.
        dataset_key should be one of the CSV filenames (without path).
        """
        df = self.dataframes.get(dataset_key)
        if df is None or "year" not in df.columns:
            return []
        return sorted(df["year"].dropna().unique())

    def get_merged_geodataframe(
        self, dataset_key: str, year: Optional[int] = None
    ) -> gpd.GeoDataFrame:
        """
        Merge the map with the specified dataset.
        If year is given, filter the dataset to that year before merging.
        Returns a GeoDataFrame (map left) with the merged data.
        """
        map_gdf = self.dataframes["map"].copy()
        df = self.dataframes.get(dataset_key)
        if df is None:
            raise ValueError(f"Dataset {dataset_key} not loaded.")

        if year is not None:
            df = df[df["year"] == year].copy()
        else:
            # If no year specified, take the most recent year for each country?
            # For simplicity, we'll keep all years – the user must select.
            # But could implement a default: most recent overall.
            pass

        # Merge on country code (ISO_A3 in map, 'code' in CSV)
        # Use left join to keep all map rows.
        merged = map_gdf.merge(
            df,
            left_on="ISO_A3",
            right_on="code",
            how="left"
        )
        return merged

    def get_value_column_name(self, dataset_key: str) -> str:
        """
        Heuristically find the main value column in a dataset (the one that is not 'entity', 'code', 'year').
        """
        df = self.dataframes.get(dataset_key)
        if df is None:
            return ""
        # Common OWID column names: _1d_deforestation, net_change_forest_area, etc.
        # We'll take the first column that is not entity, code, year.
        for col in df.columns:
            if col not in ["entity", "code", "year"]:
                return col
        return ""