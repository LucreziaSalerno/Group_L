from pathlib import Path

import folium
import streamlit as st
import yaml
from streamlit_folium import st_folium

from app.ai_pipeline import (
    assess_environmental_risk,
    describe_image,
    extract_danger_label,
)
from app.image_utils import build_image_filename, download_esri_image
from app.storage import append_result, find_existing_result, load_database


st.set_page_config(page_title="AI Workflow", layout="wide")


@st.cache_data
def load_models_config() -> dict:
    """Load configuration from models.yaml."""
    with open("models.yaml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_preset_values(preset_name: str) -> tuple[float, float, int]:
    """Return default coordinates for known example locations."""
    presets = {
        "Custom": (38.7223, -9.1393, 12),
        "Amazon deforestation": (-3.4653, -62.2159, 10),
        "Lisbon urban area": (38.7223, -9.1393, 12),
        "Sahara desert": (23.4162, 25.6628, 10),
        "California wildfire area": (38.9395, -120.9856, 11),
    }
    return presets.get(preset_name, presets["Custom"])


def initialize_session_state() -> None:
    """Initialize session state values once."""
    if "preset" not in st.session_state:
        st.session_state.preset = "Custom"

    if "latitude_input" not in st.session_state:
        st.session_state.latitude_input = 38.7223

    if "longitude_input" not in st.session_state:
        st.session_state.longitude_input = -9.1393

    if "zoom_input" not in st.session_state:
        st.session_state.zoom_input = 12

    if "clicked_latitude" not in st.session_state:
        st.session_state.clicked_latitude = None

    if "clicked_longitude" not in st.session_state:
        st.session_state.clicked_longitude = None


def apply_preset() -> None:
    """Update lat/lon/zoom from selected preset."""
    lat, lon, zoom = get_preset_values(st.session_state.preset)
    st.session_state.latitude_input = lat
    st.session_state.longitude_input = lon
    st.session_state.zoom_input = zoom


def apply_clicked_coordinates() -> None:
    """Copy clicked map coordinates into the sidebar input widgets."""
    if (
        st.session_state.clicked_latitude is not None
        and st.session_state.clicked_longitude is not None
    ):
        st.session_state.latitude_input = st.session_state.clicked_latitude
        st.session_state.longitude_input = st.session_state.clicked_longitude
        st.session_state.preset = "Custom"


def build_click_map(latitude: float, longitude: float, zoom: int) -> folium.Map:
    """Create an interactive folium map for coordinate picking."""
    fmap = folium.Map(
        location=[latitude, longitude],
        zoom_start=zoom,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    folium.Marker(
        [latitude, longitude],
        tooltip="Current selected point",
        popup=f"Lat: {latitude:.4f}, Lon: {longitude:.4f}",
    ).add_to(fmap)

    folium.LatLngPopup().add_to(fmap)

    return fmap


initialize_session_state()
config = load_models_config()
images_dir = Path("images")
images_dir.mkdir(exist_ok=True)

st.title("AI Workflow")
st.markdown(
    """
    This page downloads a satellite image from **ESRI World Imagery**,
    describes it using an **Ollama vision model**, and assesses whether the
    area may be at **environmental risk**.
    """
)

with st.sidebar:
    st.header("Settings")

    st.selectbox(
        "Choose an example location",
        [
            "Custom",
            "Amazon deforestation",
            "Lisbon urban area",
            "Sahara desert",
            "California wildfire area",
        ],
        key="preset",
        on_change=apply_preset,
    )

    st.number_input(
        "Latitude",
        min_value=-90.0,
        max_value=90.0,
        step=0.0001,
        format="%.4f",
        key="latitude_input",
    )

    st.number_input(
        "Longitude",
        min_value=-180.0,
        max_value=180.0,
        step=0.0001,
        format="%.4f",
        key="longitude_input",
    )

    st.slider(
        "Zoom",
        min_value=1,
        max_value=18,
        key="zoom_input",
    )

    run_button = st.button("Run analysis", use_container_width=True)

latitude = float(st.session_state.latitude_input)
longitude = float(st.session_state.longitude_input)
zoom = int(st.session_state.zoom_input)

st.subheader("Selected Coordinates")
col1, col2, col3 = st.columns(3)
col1.metric("Latitude", f"{latitude:.4f}")
col2.metric("Longitude", f"{longitude:.4f}")
col3.metric("Zoom", zoom)

st.subheader("Pick coordinates from the map")
st.caption("Click on the map, then use the button below to update the inputs.")

map_data = st_folium(
    build_click_map(latitude, longitude, zoom),
    width=None,
    height=420,
    returned_objects=["last_clicked"],
    key="coordinate_picker_map",
)

last_clicked = map_data.get("last_clicked") if map_data else None

if last_clicked:
    clicked_lat = round(last_clicked["lat"], 4)
    clicked_lon = round(last_clicked["lng"], 4)

    st.session_state.clicked_latitude = clicked_lat
    st.session_state.clicked_longitude = clicked_lon

    st.info(
        f"Map click detected — Latitude: {clicked_lat}, Longitude: {clicked_lon}"
    )

    st.button(
        "Use clicked coordinates",
        on_click=apply_clicked_coordinates,
    )

image_filename = build_image_filename(latitude, longitude, zoom)
image_path = images_dir / image_filename

if run_button:
    db = load_database()
    existing = find_existing_result(db, latitude, longitude, zoom)

    if existing is not None:
        st.info(
            "Loaded from a previous saved analysis. The pipeline was not re-run."
        )

        result_col1, result_col2 = st.columns([1.1, 1])

        with result_col1:
            st.subheader("Satellite image")
            stored_image_path = Path(existing["image_path"])
            if stored_image_path.exists():
                st.image(str(stored_image_path), use_container_width=True)
            else:
                st.warning("Stored image file was not found locally.")

        with result_col2:
            st.subheader("Image description")
            st.write(existing["image_description"])

        st.subheader("Risk assessment")
        st.write(existing["text_description"])

        if str(existing["danger"]).upper() == "Y":
            st.error("⚠️ Potential environmental risk detected.")
        else:
            st.success("✅ No clear environmental risk detected.")

        with st.expander("Technical details"):
            st.write(
                {
                    "image_model": existing["image_model"],
                    "risk_model": existing["text_model"],
                    "image_path": existing["image_path"],
                    "loaded_from_database": True,
                }
            )

    else:
        imagery_cfg = config["imagery"]
        image_cfg = config["image_analysis"]
        risk_cfg = config["risk_analysis"]

        with st.spinner("Downloading satellite image from ESRI World Imagery..."):
            download_esri_image(
                latitude=latitude,
                longitude=longitude,
                zoom=zoom,
                output_path=image_path,
                width=imagery_cfg["width"],
                height=imagery_cfg["height"],
                base_half_size_degrees=imagery_cfg.get(
                    "bbox_half_size_degrees_base", 0.8
                ),
            )

        st.success("New image downloaded successfully.")

        try:
            with st.spinner("Analyzing image with vision model..."):
                image_description = describe_image(
                    image_path=image_path,
                    model_name=image_cfg["model"],
                    prompt=image_cfg["prompt"],
                    temperature=image_cfg.get("temperature", 0.2),
                )
        except Exception as exc:
            st.error(f"Image description failed: {exc}")
            st.stop()

        try:
            with st.spinner("Assessing environmental risk..."):
                risk_response = assess_environmental_risk(
                    description=image_description,
                    model_name=risk_cfg["model"],
                    prompt=risk_cfg["prompt"],
                    temperature=risk_cfg.get("temperature", 0.2),
                )
        except Exception as exc:
            st.error(f"Risk assessment failed: {exc}")
            st.stop()

        danger = extract_danger_label(risk_response)

        result_col1, result_col2 = st.columns([1.1, 1])

        with result_col1:
            st.subheader("Satellite image")
            st.image(str(image_path), use_container_width=True)

        with result_col2:
            st.subheader("Image description")
            st.write(image_description)

        st.subheader("Risk assessment")
        st.write(risk_response)

        if danger == "Y":
            st.error("⚠️ Potential environmental risk detected.")
        else:
            st.success("✅ No clear environmental risk detected.")

        append_result(
            latitude=latitude,
            longitude=longitude,
            zoom=zoom,
            image_path=str(image_path),
            image_description=image_description,
            image_prompt=image_cfg["prompt"],
            image_model=image_cfg["model"],
            text_description=risk_response,
            text_prompt=risk_cfg["prompt"],
            text_model=risk_cfg["model"],
            danger=danger,
        )

        st.success("New analysis completed and saved to database/images.csv")

        with st.expander("Technical details"):
            st.write(
                {
                    "image_model": image_cfg["model"],
                    "risk_model": risk_cfg["model"],
                    "image_path": str(image_path),
                    "loaded_from_database": False,
                }
            )

st.divider()

st.subheader("Previous analyses")
db_preview = load_database()

if not db_preview.empty:
    preview_columns = [
        "timestamp",
        "latitude",
        "longitude",
        "zoom",
        "danger",
        "image_model",
        "text_model",
    ]
    available_columns = [col for col in preview_columns if col in db_preview.columns]
    st.dataframe(
        db_preview[available_columns].tail(10),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.write("No previous analyses stored yet.")
