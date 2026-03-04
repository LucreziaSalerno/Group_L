# main.py
import streamlit as st
import plotly.express as px
import pandas as pd
from app.environmental_data import EnvironmentalData

# ----------------------------------------------------------------------
# Cache the data handler to avoid repeated downloads / loading
# ----------------------------------------------------------------------
@st.cache_resource
def load_data():
    """Initialize and return the EnvironmentalData object."""
    return EnvironmentalData(download_dir="downloads")

data_handler = load_data()

# ----------------------------------------------------------------------
# App title and description
# ----------------------------------------------------------------------
st.set_page_config(page_title="Enironmental Data Explorer", layout="wide")
st.title("Environmental Data Explorer")
st.markdown("Explore global environmental indicators from [Our World in Data](https://ourworldindata.org).")

# ----------------------------------------------------------------------
# Sidebar: dataset selection
# ----------------------------------------------------------------------
datasets = {
    "Annual Forest Change": "annual_forest_change.csv",
    "Annual Deforestation": "annual_deforestation.csv",
    "Protected Land (%)": "protected_land.csv",
    "Degraded Land (%)": "degraded_land.csv",
    "Red List Index": "red_list_index.csv"
}

selected_name = st.sidebar.selectbox("Choose a dataset", list(datasets.keys()))
dataset_key = datasets[selected_name]

# ----------------------------------------------------------------------
# Get available years for the selected dataset
# ----------------------------------------------------------------------
years = data_handler.get_available_years(dataset_key)
if not years:
    st.error(f"No year data available for {selected_name}. Please check the dataset.")
    st.stop()

# Default to most recent year
selected_year = st.sidebar.selectbox("Select year", years, index=len(years)-1)

# ----------------------------------------------------------------------
# Load merged data for the chosen dataset and year
# ----------------------------------------------------------------------
merged_gdf = data_handler.get_merged_geodataframe(dataset_key, year=selected_year)
value_col = data_handler.get_value_column_name(dataset_key)

if value_col not in merged_gdf.columns:
    st.error(f"Value column '{value_col}' not found in merged data.")
    st.stop()

# Drop rows without geometry or without the value
plot_gdf = merged_gdf.dropna(subset=[value_col, "geometry"]).copy()

if plot_gdf.empty:
    st.warning("No data available for the selected year and dataset.")
    st.stop()

# ----------------------------------------------------------------------
# Display main map
# ----------------------------------------------------------------------
st.subheader(f"{selected_name} in {selected_year}")

# Create choropleth map using plotly
fig = px.choropleth(
    plot_gdf,
    geojson=plot_gdf.geometry.__geo_interface__,
    locations=plot_gdf.index,
    color=value_col,
    hover_name="ADMIN",
    hover_data={value_col: ":.2f"},
    color_continuous_scale="Viridis",
    title=f"{selected_name} ({selected_year})"
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0, "t":30, "l":0, "b":0})

# Use width='stretch' instead of deprecated use_container_width
st.plotly_chart(fig, width='stretch')

# ----------------------------------------------------------------------
# Bar chart: top 5 and bottom 5 countries
# ----------------------------------------------------------------------
st.subheader("Top 5 and Bottom 5 Countries")

# Sort values and take top/bottom 5
sorted_df = plot_gdf[["ADMIN", value_col]].dropna().sort_values(value_col, ascending=False)
top5 = sorted_df.head(5)
bottom5 = sorted_df.tail(5)
combined = pd.concat([top5, bottom5], axis=0)

fig_bar = px.bar(
    combined,
    x="ADMIN",
    y=value_col,
    color=value_col,
    title="Highest and Lowest Values",
    labels={"ADMIN": "Country", value_col: selected_name},
    color_continuous_scale="Viridis"
)
fig_bar.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_bar, width='stretch')

# ----------------------------------------------------------------------
# Optional: show data source and info
# ----------------------------------------------------------------------
with st.expander("ℹ️ About this app"):
    st.markdown("""
    This app visualises environmental indicators from **Our World in Data**.
    - The map shows the latest available values per country.
    - The bar chart highlights the five countries with the highest and lowest values.
    - All data is downloaded automatically on first run.
    """)