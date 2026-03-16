from datetime import datetime
from pathlib import Path

import pandas as pd


DATABASE_PATH = Path("database/images.csv")

DATABASE_COLUMNS = [
    "timestamp",
    "latitude",
    "longitude",
    "zoom",
    "image_path",
    "image_description",
    "image_prompt",
    "image_model",
    "text_description",
    "text_prompt",
    "text_model",
    "danger",
]


def ensure_database_exists() -> None:
    """Create the CSV database with headers if needed."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not DATABASE_PATH.exists():
        pd.DataFrame(columns=DATABASE_COLUMNS).to_csv(DATABASE_PATH, index=False)


def load_database() -> pd.DataFrame:
    """Load the CSV database."""
    ensure_database_exists()

    if DATABASE_PATH.stat().st_size == 0:
        return pd.DataFrame(columns=DATABASE_COLUMNS)

    return pd.read_csv(DATABASE_PATH)


def find_existing_result(
    df: pd.DataFrame,
    latitude: float,
    longitude: float,
    zoom: int,
):
    """Find a previously computed result for the same settings."""
    if df.empty:
        return None

    result = df[
        (df["latitude"].round(4) == round(latitude, 4))
        & (df["longitude"].round(4) == round(longitude, 4))
        & (df["zoom"] == zoom)
    ]

    if result.empty:
        return None

    return result.iloc[-1]


def append_result(
    latitude: float,
    longitude: float,
    zoom: int,
    image_path: str,
    image_description: str,
    image_prompt: str,
    image_model: str,
    text_description: str,
    text_prompt: str,
    text_model: str,
    danger: str,
) -> None:
    """Append one run to the CSV database."""
    df = load_database()

    new_row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "latitude": latitude,
        "longitude": longitude,
        "zoom": zoom,
        "image_path": image_path,
        "image_description": image_description,
        "image_prompt": image_prompt,
        "image_model": image_model,
        "text_description": text_description,
        "text_prompt": text_prompt,
        "text_model": text_model,
        "danger": danger,
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATABASE_PATH, index=False)
