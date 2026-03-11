from pathlib import Path

import streamlit as st
import yaml

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


config = load_models_config()

st.title("AI Workflow")
st.markdown(
    "Choose coordinates and zoom, download a satellite image, "
    "describe it with a vision model, and assess possible environmental risk."
)

with st.sidebar:
    st.header("Settings")
    latitude = st.number_input(
        "Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=38.7223,
        step=0.0001,
        format="%.4f",
    )
    longitude = st.number_input(
        "Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=-9.1393,
        step=0.0001,
        format="%.4f",
    )
    zoom = st.slider("Zoom", min_value=1, max_value=18, value=12)

    run_button = st.button("Run analysis", use_container_width=True)

images_dir = Path("images")
images_dir.mkdir(exist_ok=True)

image_filename = build_image_filename(latitude, longitude, zoom)
image_path = images_dir / image_filename

if run_button:
    db = load_database()
    existing = find_existing_result(db, latitude, longitude, zoom)

    if existing is not None:
        st.info("Existing result found. Loaded from the local database.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Satellite image")
            st.image(existing["image_path"], use_container_width=True)

        with col2:
            st.subheader("Image description")
            st.write(existing["image_description"])

        st.subheader("Risk assessment")
        st.write(existing["text_description"])

        if str(existing["danger"]).upper() == "Y":
            st.error("Potential environmental risk detected.")
        else:
            st.success("No clear environmental risk detected.")

        with st.expander("Stored record details"):
            st.write(existing.to_dict())

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

        with st.spinner("Generating image description with Ollama..."):
            image_description = describe_image(
                image_path=image_path,
                model_name=image_cfg["model"],
                prompt=image_cfg["prompt"],
                temperature=image_cfg.get("temperature", 0.2),
            )

        with st.spinner("Assessing environmental risk..."):
            risk_response = assess_environmental_risk(
                description=image_description,
                model_name=risk_cfg["model"],
                prompt=risk_cfg["prompt"],
                temperature=risk_cfg.get("temperature", 0.2),
            )

        danger = extract_danger_label(risk_response)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Satellite image")
            st.image(str(image_path), use_container_width=True)

        with col2:
            st.subheader("Image description")
            st.write(image_description)

        st.subheader("Risk assessment")
        st.write(risk_response)

        if danger == "Y":
            st.error("Potential environmental risk detected.")
        else:
            st.success("No clear environmental risk detected.")

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

        st.caption("Result saved to database/images.csv")
