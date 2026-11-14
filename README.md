# TerraPulse — *The GPS for Agriculture*

**TerraPulse** is an AI-powered satellite and field intelligence platform built for the **NASA Space Apps Challenge**.  
It turns complex satellite, weather, and terrain data into **simple, practical, everyday advice for farmers**—while still offering deep scientific charts and neural network telemetry underneath.

---

## Why TerraPulse?

Farmers face four growing challenges:
1. **Drought & Water Waste:** Not knowing *when* or *how much* to irrigate wastes water and pumping electricity.
2. **Soil Exhaustion:** Continuous farming drains organic matter and forces farmers to buy more synthetic fertilizer.
3. **Crop Monoculture:** Planting the same crop every year hurts yields and invites pests.
4. **Fires & Extreme Storms:** Bare or sloped land after a wildfire or heatwave can lose its fertile topsoil in the very first heavy rain.

**TerraPulse solves all four in one place.** You click a field on the map (or draw its exact shape), and four neural networks analyze the land, fetch live weather forecasts, and tell you—in plain language—**what is happening and what to do tomorrow morning**.

---

## Key Features

- **Interactive 3D Earth Landing Page:** A Three.js 3D globe with orbital satellite animations introducing the platform.
- **Interactive Field Map OS (Leaflet):**
  - Switch between **Dark OS**, **Satellite**, and **NDVI / Topo** map layers.
  - Search any region in the world (powered by OpenStreetMap Nominatim).
  - **Draw any field polygon** to automatically measure its real area in **hectares & stremmata** without losing your zoom level.
  - **3×3 Variable Rate (VRA) Sub-Grid:** Color-coded zones inside your field showing which corner is drier or needs `+15%` / `-15%` water.
  - **Compare Two Fields (Field A vs Field B):** Save any two plots and compare their stress, soil health, erosion risk, and annual savings side-by-side.
- **Two-Layer Data Analysis Suite:**
  - **Top ("At a Glance"):** Plain-language explanation, circular progress gauge, and a 1-2-3 step-by-step action checklist any farmer can understand immediately.
  - **Bottom ("Further Analytics"):** Gradient Chart.js graphs, regional benchmarks, cost comparisons (€), live 7-day rain-aware irrigation schedule, interactive mini-maps, and full scientific summaries.
- **Interactive "What-If" Farmer Simulator:** Change your **Crop** (*Wheat, Cotton, Corn, Olives, Vineyard, Alfalfa*), **Irrigation Method** (*Flood, Sprinkler, Drip*), or **Weather Scenario** (*Live Forecast, Heatwave, Post-Fire Storm*) to test savings and risks in real time.
- **Voice Briefing ("Listen"):** Built-in Web Speech API reads the active field guidance aloud in **Greek** or **English**.
- **100% Bilingual (`EN ↔ GR`) & Light/Dark Mode:** Switches every label, chart, voice readout, and AI review between Greek and English.
- **Clean 1-Page PDF Export:** Dedicated print layout turns the analysis into a crisp, white agronomist prescription sheet.

---

## How the 4 PyTorch Neural Networks Work

TerraPulse runs **four specialized PyTorch models** fed by live weather, soil moisture, elevation slope, and vegetation indices:

| Network | Focus | What It Outputs | How It Helps the Farmer |
| :--- | :--- | :--- | :--- |
| **Network 1 — Water** | Drought & Irrigation | Root-zone water stress (`0–1`) | Calculates exact `m³/stremma`, best watering hours (`05:00–07:00`), and skips watering when rain is forecast. |
| **Network 2 — Soil** | Degradation & Depletion | `health_proxy` & `erosion_proxy` (`0–1`) | Detects tired soil, checks NPK & organic carbon balance, and recommends no-till or cover crops to cut fertilizer bills. |
| **Network 3 — Rotation** | Crop Matchmaking | Suitability scores & `N₂` fixation | Suggests the best next crop (e.g., drought-resilient legumes) to naturally put free nitrogen back into the soil. |
| **Network 4 — Fire & Floods** | Extreme Events | `erosion_risk` & `recovery_score` (`0–1`) | Calculates post-fire/storm landslide risk from terrain slope, simulates 12-month plant rebound, and previews a **72h SMS alert**. |

---

## Live Data Sources

- **Open-Meteo Forecast & Soil Moisture API:** Live 7-day temperature, rainfall, `ET₀` evapotranspiration, and volumetric root-zone soil moisture (`0–28 cm`).
- **Open-Meteo 5-Point Elevation API:** Real terrain elevation and calculated slope angle (`°`) around your exact coordinates.
- **OpenStreetMap Nominatim:** Worldwide place and region search.
- *(Graceful Offline Fallback: If there is no internet connection, the backend automatically switches to deterministic telemetry synthesis so the app never crashes.)*

---

## Project Structure

```text
terra_pulse/
├── terra_pulse_frontend/
│   ├── index.html                  # Main HTML layout (Landing, Map OS, Analysis Suite)
│   ├── logo.png                    # TerraPulse brand logo & favicon
│   ├── css/
│   │   └── styles.css              # Light/Dark CSS variables, HUD styling, animations & print sheet
│   └── js/
│       ├── state.js                # App state, zoom-lock fix, EN/GR translations, theme & voice readout
│       ├── globe.js                # Three.js 3D Earth, starfield & orbital satellites
│       ├── charts.js               # Chart.js gradient charts & Leaflet mini-maps
│       ├── map.js                  # Leaflet Map OS, polygon drawing, search & 3x3 VRA grid
│       ├── api.js                  # Backend API calls, What-If simulator & Field A/B comparison
│       └── main.js                 # View/sidebar/tab navigation & startup
│
└── terra_pulse_backend/
    ├── main.py                     # FastAPI entry point + CORS + router registration
    ├── core/
    │   ├── config.py               # Crop coefficients (Kc), irrigation efficiencies & paths
    │   ├── model_loader.py         # PyTorch architectures, .pth weights & preprocess.json loaders
    │   ├── geo_live.py             # Live Open-Meteo weather/moisture/elevation fetch + 10-min cache
    │   └── telemetry.py            # Location telemetry builder, 7-day schedule & VRA sub-grid
    ├── routes/
    │   ├── water.py                # GET /api/water-analysis (Network 1)
    │   ├── soil.py                 # GET /api/soil-analysis (Network 2)
    │   ├── rotation.py             # GET /api/rotation-analysis (Network 3)
    │   └── fire.py                 # GET /api/fire-analysis (Network 4)
    ├── training/
    │   ├── train_network1_water.py     # Trains & saves terrapulse_water_model.pth
    │   ├── train_network2_soil.py      # Trains & saves terrapulse_soil_model.pth + preprocess.json
    │   ├── train_network3_rotation.py  # Trains & saves terrapulse_rotation_model.pth
    │   └── train_network4_fire.py      # Trains & saves terrapulse_fire_model.pth + preprocess.json
    └── *.pth / *.json              # Saved PyTorch weights & normalization parameters
```

---

## Quick Start Guide

### 1. Start the Backend (Python + FastAPI)
Make sure Python 3.10+ is installed, then install the backend dependencies:

```bash
pip install fastapi uvicorn torch
```

Move into the backend folder and start the API server:

```bash
cd terra_pulse_backend
uvicorn main:app --reload
```

The API will run at **`http://localhost:8000`**.  
*(Optional: You can inspect interactive API docs anytime at `http://localhost:8000/docs`.)*

### 2. Start the Frontend
Open `terra_pulse_frontend/index.html` using **VS Code Live Server** (recommended, e.g., `http://127.0.0.1:5500/terra_pulse_frontend/index.html`) or Python's built-in HTTP server:

```bash
cd terra_pulse_frontend
python -m http.server 5500
```

Then open **`http://localhost:5500`** in your browser.

### 3. (Optional) Retrain the 4 Neural Networks
If you want to regenerate or retrain the `.pth` weight files and preprocessing `.json` files from scratch:

```bash
cd terra_pulse_backend
python training/train_network1_water.py
python training/train_network2_soil.py
python training/train_network3_rotation.py
python training/train_network4_fire.py
```

---

## Tech Stack

- **Frontend:** HTML5, Tailwind CSS, Vanilla Modular JavaScript, Three.js, Leaflet + Leaflet.Draw, Chart.js, Web Speech API
- **Backend:** Python, FastAPI, Uvicorn, PyTorch
- **Data & Maps:** Open-Meteo (Forecast, Soil Moisture, Elevation), OpenStreetMap / Nominatim, Esri World Imagery, OpenTopoMap
