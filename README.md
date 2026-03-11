# Group_L
Advanced Programming for Data Science Project Repository
Group Members Emails:
- 70098@novasbe.pt 
- 56556@novasbe.pt 
- 52011@novasbe.pt 
- 75754@novasbe.pt 


## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/LucreziaSalerno/Group_L.git
   cd Group_L

2. **Install the dependencies**
   ```bash
   pip install -r requirements.txt
  
3. **Run the application**
   ```bash
   streamlit run main.py


## About the App

**Environmental Data Explorer** is an interactive dashboard built with [Streamlit](https://streamlit.io) that visualises key environmental indicators from [Our World in Data](https://ourworldindata.org). It allows users to explore global trends in forest change, deforestation, protected land, degraded land, and the Red List Index – all with the most recent data available.

### Features

- **Automatic data download** – On first run, the app fetches the latest CSV datasets and a high‑resolution world map from Natural Earth. Everything is stored locally.
- **Interactive choropleth map** – Choose a dataset and a year; the map colours countries according to their value, with hover details.
- **Top / bottom countries** – A bar chart automatically displays the five countries with the highest and the five with the lowest values for the selected indicator.


### How it works

The app uses a custom `EnvironmentalData` class (in `app/environmental_data.py`) to handle downloading, caching, and merging the spatial data with the statistical tables. All visualisations are created with [Plotly Express](https://plotly.com/python/plotly-express/), ensuring smooth interactivity.
