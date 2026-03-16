from app.environmental_data import EnvironmentalData


def test_merge_keeps_map_as_left_dataframe(sample_download_dir):
    file_map = {
        "annual_forest_change.csv": "dummy-url",
        "ne_110m_admin_0_countries.zip": "dummy-url",
    }

    data = EnvironmentalData(
        download_dir=str(sample_download_dir),
        file_map=file_map,
        auto_download=False,
    )

    merged = data.get_merged_geodataframe("annual_forest_change.csv", year=2020)

    assert len(merged) == 2
    assert "geometry" in merged.columns
    assert "forest_value" in merged.columns
    assert set(merged["ISO_A3"]) == {"PRT", "ESP"}
