from app.environmental_data import EnvironmentalData


def test_get_available_years(sample_download_dir):
    file_map = {
        "annual_forest_change.csv": "dummy-url",
        "ne_110m_admin_0_countries.zip": "dummy-url",
    }

    data = EnvironmentalData(
        download_dir=str(sample_download_dir),
        file_map=file_map,
        auto_download=False,
    )

    years = data.get_available_years("annual_forest_change.csv")

    assert years == [2020]


def test_get_value_column_name(sample_download_dir):
    file_map = {
        "annual_forest_change.csv": "dummy-url",
        "ne_110m_admin_0_countries.zip": "dummy-url",
    }

    data = EnvironmentalData(
        download_dir=str(sample_download_dir),
        file_map=file_map,
        auto_download=False,
    )

    assert data.get_value_column_name("annual_forest_change.csv") == "forest_value"
