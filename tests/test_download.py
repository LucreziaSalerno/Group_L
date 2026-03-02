import requests
from pathlib import Path
from typing import Dict
import time

def download_data(file_map: Dict[str, str], target_dir: str = "downloads", max_retries: int = 3) -> None:
    path = Path(target_dir)
    path.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for filename, url in file_map.items():
        print(f"Downloading {filename} ...")
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=30, headers=headers)
                response.raise_for_status()
                file_path = path / filename
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"  Saved to {file_path}")
                break
            except Exception as e:
                print(f"  Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    print(f"  Giving up on {filename}")
                else:
                    time.sleep(2)  # wait before retry