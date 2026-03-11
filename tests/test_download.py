from pathlib import Path
from unittest.mock import Mock, patch

from app.environmental_data import EnvironmentalData


def test_download_file_saves_content(tmp_path: Path):
    destination = tmp_path / "test_file.csv"

    mock_response = Mock()
    mock_response.content = b"col1,col2\n1,2\n"
    mock_response.raise_for_status = Mock()

    data = EnvironmentalData.__new__(EnvironmentalData)

    with patch("requests.get", return_value=mock_response) as mock_get:
        data._download_file("https://example.com/test.csv", destination)

    mock_get.assert_called_once()
    assert destination.exists()
    assert destination.read_bytes() == b"col1,col2\n1,2\n"
