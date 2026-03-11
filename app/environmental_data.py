# app/environmental_data.py
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, Optional, Union
import requests
import time


class EnvironmentalData:
    """Download, load, and merge environmental datasets with a world map."""

    DEFAULT_FILE_MAP = {
        "annual_forest_change.csv": (
            "https://ourworldindata.org/grapher/"
            "annual-change-forest-area.csv?v=1&csvType=full&useColumnShortNames=true"
        ),
        "annual_deforestation.csv": (
            "https://ourworldindata.org/grapher/"
            "annual-deforestation.csv?v=1&csvType=full&useColumnShortNames=true"
        ),
        "protected_land.csv": (
            "https://ourworldindata.org/grapher/"
            "terrestrial-protected-areas.csv?v=1&csvType=full&useColumnShortNames=true"
        ),
        "degraded_land.csv": (
            "https://ourworldindata.org/grapher/"
            "share-degraded-land.csv?v=1&csvType=full&useColumnShortNames=true"
        ),
        "red_list_index.csv": (
            "https://ourworldindata.org/grapher/"
            "red-list-index.csv?v=1&csvType=full&useColumnShortNames=true"
        ),
        "ne_110m_admin_0_countries.zip": (
            "https://naciscdn.org/naturalearth/110m/cultural/"
            "ne_110m_admin_0_countries.zip"
        ),
    }

    def __init__(
        self,
        download_dir: str = "downloads",
        file_map: Optional[Dict[str, str]] = None,
        auto_download: bool = True,
    ) -> None:
        self.download_dir = Path(download_dir)
        self.file_map = file_map or self.DEFAULT_FILE_MAP.copy()
        self.dataframes: Dict[str, Union[pd.DataFrame, gpd.GeoDataFrame]] = {}

        if auto_download:
            self._download_all()

        self._load_all()

    def _download_file(self, url: str, destination: Path, timeout: int = 30) -> None:
        """Download one file and save it locally."""
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        destination.write_bytes(response.content)

    def _download_all(self) -> None:
        """Download all required files that do not already exist."""
        self.download_dir.mkdir(parents=True, exist_ok=True)

        failed_files = []

        for filename, url in self.file_map.items():
            destination = self.download_dir / filename

            if destination.exists():
                continue

            try:
                self._download_file(url, destination)
            except requests.RequestException as exc:
                failed_files.append(f"{filename}: {exc}")

        if failed_files:
            raise RuntimeError(
                "Some files could not be downloaded:\n" + "\n".join(failed_files)
            )

    def _load_all(self) -> None:
        """Load the world map and all CSV files into memory."""
        map_file = self.download_dir / "ne_110m_admin_0_countries.zip"
        if not map_file.exists():
            raise FileNotFoundError(f"Map file not found: {map_file}")

        self.dataframes["map"] = gpd.read_file(map_file)

        for filename in self.file_map:
            if filename == "ne_110m_admin_0_countries.zip":
                continue

            file_path = self.download_dir / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Dataset file not found: {file_path}")

            self.dataframes[filename] = pd.read_csv(file_path)

    def get_available_years(self, dataset_key: str) -> list[int]:
        """Return sorted available years for a dataset."""
        df = self.dataframes.get(dataset_key)

        if df is None or "year" not in df.columns:
            return []

        years = sorted(df["year"].dropna().astype(int).unique().tolist())
        return years

    def get_merged_geodataframe(
        self,
        dataset_key: str,
        year: Optional[int] = None,
    ) -> gpd.GeoDataFrame:
        """Merge the map with a selected dataset, optionally filtered by year."""
        if "map" not in self.dataframes:
            raise ValueError("Map data is not loaded.")

        df = self.dataframes.get(dataset_key)
        if df is None:
            raise ValueError(f"Dataset not loaded: {dataset_key}")

        required_columns = {"code", "year"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"Dataset '{dataset_key}' is missing columns: {sorted(missing_columns)}"
            )

        if year is not None:
            df = df[df["year"] == year].copy()

        map_gdf = self.dataframes["map"].copy()
        merged = map_gdf.merge(df, how="left", left_on="ISO_A3", right_on="code")
        return merged

    def get_value_column_name(self, dataset_key: str) -> str:
        """Return the main numeric value column of a dataset."""
        df = self.dataframes.get(dataset_key)

        if df is None:
            raise ValueError(f"Dataset not loaded: {dataset_key}")

        excluded_columns = {"entity", "code", "year"}

        value_columns = [col for col in df.columns if col.lower() not in excluded_columns]

        if not value_columns:
            raise ValueError(f"No value column found in dataset: {dataset_key}")

        return value_columns[0]
