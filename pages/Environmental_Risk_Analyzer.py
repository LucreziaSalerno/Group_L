from pathlib import Path

import folium
import streamlit as st
import yaml
from streamlit_folium import st_folium

from app.ai_pipeline import (
    assess_environmental_risk,
    classify_environmental_risk,
    clean_risk_response,
    describe_image,
)
from app.image_utils import build_image_filename, download_esri_image
from app.storage import append_result, find_existing_result, load_database

st.set_page_config(
    page_title="Environmental Risk Analyzer",
    layout="wide"
)

@st.cache_data
def load_database_cached():
    return load_database()


from app.models import AppConfig

@st.cache_data
def load_models_config() -> dict:
    with open("models.yaml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
        config = AppConfig(**data)
        return config.model_dump()


def get_preset_values(preset_name: str) -> tuple[float, float, int]:
    presets = {
        "Custom": (38.7223, -9.1393, 12),

        # stronger fishbone-style deforestation region
        "Amazon deforestation": (-8.7490, -63.9080, 11),

        "Lisbon urban area": (38.7223, -9.1393, 12),
        "Sahara desert": (23.4162, 25.6628, 11),

        # optional extra
        "California wildfire area": (39.8756, -120.4350, 12),

        # stronger open-pit mining candidate
        "Mining area": (40.5230, -112.1510, 13),

        "Chuquicamata Copper Mine": (-22.2885, -68.9000, 12),
        "Rondonia Deforestation": (-9.6000, -63.0000, 11),
    }
    return presets.get(preset_name, presets["Custom"])


def initialize_session_state() -> None:
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
    lat, lon, zoom = get_preset_values(st.session_state.preset)
    st.session_state.latitude_input = lat
    st.session_state.longitude_input = lon
    st.session_state.zoom_input = zoom


def apply_clicked_coordinates() -> None:
    if (
        st.session_state.clicked_latitude is not None
        and st.session_state.clicked_longitude is not None
    ):
        st.session_state.latitude_input = st.session_state.clicked_latitude
        st.session_state.longitude_input = st.session_state.clicked_longitude
        st.session_state.preset = "Custom"


def build_click_map(latitude: float, longitude: float, zoom: int) -> folium.Map:
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


def show_result_summary(danger: str, source_label: str) -> None:
    """Show the main result summary block with a proper dashboard layout."""
    st.header("Analysis Dashboard Overview")

    is_danger = (danger == "Y")
    status_text = "High Risk Detected" if is_danger else "Stable / Low Concern"
    
    dash_col1, dash_col2 = st.columns(2)
    with dash_col1:
        st.metric("Classification", danger)
    with dash_col2:
        st.metric("Assessment Status", status_text)

    st.progress(100 if is_danger else 25, text="Risk Assessment Confidence Score")
    st.caption(source_label)

    if is_danger:
        st.error("Potential environmental risk detected in this region based on satellite image analysis. Further investigation is recommended.")
    else:
        st.success("No clear environmental risk detected in the analyzed visible range. Area appears stable.")

st.divider()

initialize_session_state()
config = load_models_config()
images_dir = Path("images")
images_dir.mkdir(exist_ok=True)

st.title("Environmental Risk Analyzer")
st.caption("Analyze satellite images with local AI models to detect potential environmental risks.")
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
            "Mining area",
            "Chuquicamata Copper Mine",
            "Rondonia Deforestation",
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

    st.slider("Zoom", min_value=1, max_value=18, key="zoom_input")

    run_button = st.button("Run analysis", use_container_width=True)

latitude = float(st.session_state.latitude_input)
longitude = float(st.session_state.longitude_input)
zoom = int(st.session_state.zoom_input)

st.subheader("Selected Coordinates")
c1, c2, c3 = st.columns(3)
c1.metric("Latitude", f"{latitude:.4f}")
c2.metric("Longitude", f"{longitude:.4f}")
c3.metric("Zoom", zoom)

st.subheader("Pick coordinates from the map")
st.caption("Click on the map to select coordinates, then press 'Use clicked coordinates'.")

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

    st.success(f"Selected point → Latitude: {clicked_lat}, Longitude: {clicked_lon}")
    st.button("Use clicked coordinates", on_click=apply_clicked_coordinates)

image_filename = build_image_filename(latitude, longitude, zoom)
image_path = images_dir / image_filename

if run_button:
    db = load_database_cached()
    existing = find_existing_result(db, latitude, longitude, zoom)

    if existing is not None:
        danger = str(existing["danger"]).upper()
        image_description = str(existing["image_description"])
        risk_text = clean_risk_response(str(existing["text_description"]))

        show_result_summary(
            danger=danger,
            source_label="Loaded from a previous saved analysis. The pipeline was not re-run.",
        )

        # Image first
        st.subheader("Satellite image")
        stored_image_path = Path(existing["image_path"])
        if stored_image_path.exists():
            st.image(str(stored_image_path), use_container_width=True)
        else:
            st.warning(
                "Stored image file was not found locally. It may have been renamed, moved, or deleted."
            )

        # Risk result second
        st.subheader("Risk assessment")
        st.write(risk_text)

        # Description after
        st.subheader("Image description")
        st.write(image_description)

        with st.expander("Technical details"):
            st.write(
                {
                    "image_model": existing["image_model"],
                    "risk_model": existing["text_model"],
                    "image_path": existing["image_path"],
                    "loaded_from_database": True,
                    "danger_label": danger,
                }
            )

    else:
        imagery_cfg = config["imagery"]
        image_cfg = config["image_analysis"]
        risk_cfg = config["risk_analysis"]

        try:
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
        except Exception as exc:
            st.error(f"Satellite image download failed: {exc}")
            st.stop()

        try:
            with st.spinner("Analyzing image with vision model..."):
                image_description = describe_image(
                    image_path=image_path,
                    model_name=image_cfg["model"],
                    prompt=image_cfg["prompt"],
                    temperature=image_cfg.get("temperature", 0.1),
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
                    temperature=risk_cfg.get("temperature", 0.1),
                )
        except Exception as exc:
            st.error(f"Risk assessment failed: {exc}")
            st.stop()
        
        try:
            danger = classify_environmental_risk(
                description=image_description,
                model_name=risk_cfg["model"],
            )
        except Exception as exc:
            st.error(f"Final risk classification failed: {exc}")
            st.stop()
            
        display_risk_response = clean_risk_response(risk_response)

        show_result_summary(
            danger=danger,
            source_label="New analysis completed and saved to database/images.csv",
        )

        # Image first
        st.subheader("Satellite image")
        st.image(str(image_path), use_container_width=True)

        # Risk result second
        st.subheader("Risk assessment")
        st.write(display_risk_response)

        # Description after
        st.subheader("Image description")
        st.write(image_description)

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

        with st.expander("Technical details"):
            st.write(
                {
                    "image_model": image_cfg["model"],
                    "risk_model": risk_cfg["model"],
                    "image_path": str(image_path),
                    "loaded_from_database": False,
                    "danger_label": danger,
                }
            )

st.divider()

st.subheader("Previous analyses")
db_preview = load_database_cached()

st.metric("Total analyses stored", len(db_preview))

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

    # Make danger column easier to read
    db_preview["danger"] = db_preview["danger"].map(
        {"Y": "Risk", "N": "Safe"}
    )
    available_columns = [col for col in preview_columns if col in db_preview.columns]
    st.dataframe(
        db_preview[available_columns].tail(10),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.write("No previous analyses stored yet.")
