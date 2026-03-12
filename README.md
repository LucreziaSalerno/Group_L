# Environmental Data Explorer & AI Environmental Risk Assessment - Group_L

Advanced Programming for Data Science — Group Project

## Authors
- Artur Bastos — [52011] — [52011@novasbe.pt]
- Beatriz Boal — [56556] — [56556@novasbe.pt]
- Lucrezia Salerno — [70098] — [70098@novasbe.pt]
- Rita Borges Coelho — [75754] — [75754@novasbe.pt]

---

## Project Structure
   ```bash
   Group_L/
   ├── app/
   │   ├── __init__.py
   │   ├── environmental_data.py
   │   ├── ai_pipeline.py
   │   ├── image_utils.py
   │   └── storage.py
   ├── pages/
   │   └── 2_AI_Workflow.py
   ├── database/
   │   └── images.csv
   ├── images/
   ├── tests/
   ├── models.yaml
   ├── main.py
   ├── requirements.txt
   └── README.md
```

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/LucreziaSalerno/Group_L.git
   cd Group_L

2. **Install the dependencies**
   ```bash
   pip install -r requirements.txt

3. **Ollama Setup**

   This project uses **Ollama** to run local AI models for image analysis.

   Install Ollama from: https://ollama.com

   Then download the models used in this project:
   ```bash
   ollama pull llava
   ollama pull llama3.2:3b
   ```

4. **Run the application**
   ```bash
   streamlit run main.py

The application will open in your browser and contains two pages:
- **Environmental Data Explorer**
- **AI Workflow**

---

## About the App

**Environmental Data Explorer** is an interactive dashboard built with [Streamlit](https://streamlit.io) that visualises key environmental indicators from [Our World in Data](https://ourworldindata.org). It allows users to explore global trends in forest change, deforestation, protected land, degraded land, and the Red List Index – all with the most recent data available.

**AI Workflow** analyzes satellite imagery to detect potential environmental risks.

## Features

### Environmental Data Explorer

- **Automatic data download** – On first run, the app fetches the latest CSV datasets and a high‑resolution world map from Natural Earth. Everything is stored locally.
- **Interactive choropleth map** – Choose a dataset and a year; the map colours countries according to their value, with hover details.
- **Top / bottom countries** – A bar chart automatically displays the five countries with the highest and the five with the lowest values for the selected indicator.

### AI Workflow

- **Satellite image download** – The app retrieves satellite imagery from **ESRI World Imagery**.
- **AI image description** – A vision model generates a detailed description of the satellite image.
- **Environmental risk analysis** – A second AI model evaluates whether the area may be environmentally at risk.
- **Interactive coordinate selection** – Users can manually enter coordinates, choose preset locations, or click directly on a map.
- **Result caching** – Previously analyzed coordinates are stored locally to avoid recomputation.

---

## How it works

The app uses a custom `EnvironmentalData` class (in `app/environmental_data.py`) to handle downloading, caching, and merging the spatial data with the statistical tables. All visualisations are created with [Plotly Express](https://plotly.com/python/plotly-express/), ensuring smooth interactivity.

For the AI workflow, additional modules in the `app/` folder manage the analysis pipeline:

- **image_utils.py**  
  Handles downloading satellite images from ESRI World Imagery.

- **ai_pipeline.py**  
  Communicates with local Ollama models to generate image descriptions and environmental risk assessments.

- **storage.py**  
  Saves results to `database/images.csv` and checks whether the same coordinates have already been analyzed.

The AI models and prompts are configured in **models.yaml**, allowing the workflow to be adjusted without modifying the code.
