import pandas as pd
import plotly.express as px
import streamlit as st

from app.environmental_data import EnvironmentalData


st.set_page_config(page_title="Environmental Data Explorer", layout="wide")


@st.cache_resource
def load_data() -> EnvironmentalData:
    """Initialize and cache the data handler."""
    return EnvironmentalData(download_dir="downloads")


data_handler = load_data()

st.title("Environmental Data Explorer")
st.markdown(
    "Explore global environmental indicators from "
    "[Our World in Data](https://ourworldindata.org)."
)

datasets = {
    "Annual Forest Change": "annual_forest_change.csv",
    "Annual Deforestation": "annual_deforestation.csv",
    "Protected Land (%)": "protected_land.csv",
    "Degraded Land (%)": "degraded_land.csv",
    "Red List Index": "red_list_index.csv",
}

selected_name = st.sidebar.selectbox("Choose a dataset", list(datasets.keys()))
dataset_key = datasets[selected_name]

years = data_handler.get_available_years(dataset_key)
if not years:
    st.error(f"No year data available for {selected_name}.")
    st.stop()

selected_year = st.sidebar.selectbox("Select year", years, index=len(years) - 1)

merged_gdf = data_handler.get_merged_geodataframe(dataset_key, year=selected_year)
value_col = data_handler.get_value_column_name(dataset_key)

if value_col not in merged_gdf.columns:
    st.error(f"Value column '{value_col}' not found in merged data.")
    st.stop()

plot_gdf = merged_gdf.dropna(subset=[value_col, "geometry"]).copy()

if plot_gdf.empty:
    st.warning("No data available for the selected year and dataset.")
    st.stop()

st.subheader(f"{selected_name} in {selected_year}")

fig = px.choropleth(
    plot_gdf,
    geojson=plot_gdf.geometry.__geo_interface__,
    locations=plot_gdf.index,
    color=value_col,
    hover_name="ADMIN",
    hover_data={value_col: ":.2f"},
    color_continuous_scale="Viridis",
    title=f"{selected_name} ({selected_year})",
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})

st.plotly_chart(fig, use_container_width=True)

st.subheader("Top 5 and Bottom 5 Countries")

sorted_df = plot_gdf[["ADMIN", value_col]].dropna().sort_values(
    by=value_col,
    ascending=False,
)

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
    color_continuous_scale="Viridis",
)
fig_bar.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig_bar, use_container_width=True)

with st.expander("ℹ️ About this app"):
    st.markdown(
        """
        This app visualises environmental indicators from **Our World in Data**.

        - The map shows the latest available values per country.
        - The bar chart highlights the five countries with the highest and lowest values.
        - All data is downloaded automatically on first run.
        """
    )
