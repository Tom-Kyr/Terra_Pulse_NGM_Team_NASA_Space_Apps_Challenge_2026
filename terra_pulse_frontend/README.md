# TerraPulse Frontend

The browser interface for **TerraPulse**, built with clean modular Vanilla JavaScript, Tailwind CSS, Three.js, Leaflet, and Chart.js. No build step or `npm install` is required.

## Folder Breakdown

- **`index.html`** — Contains the 3 views:
  1. **Landing View:** Interactive 3D Earth globe.
  2. **Map OS:** Full-screen Leaflet workspace with layer switching, search, polygon drawing, and sidebar telemetry.
  3. **Analysis Suite:** 5-tab decision dashboard with a simple farmer summary at the top and deep satellite graphs underneath.
- **`logo.png`** — Brand icon used in the headers and browser favicon.
- **`css/styles.css`** — Light/Dark theme CSS variables, glassmorphism panels, HUD corner brackets, radar sweep animations, and a clean white `@media print` sheet for PDF exports.
- **`js/state.js`** — Holds app state (`activeState`, `simState`, `fieldSlots`), blocks accidental browser pinch-zoom on trackpads, manages `EN ↔ GR` translations, theme toggling, and **Web Speech API** voice readouts.
- **`js/globe.js`** — Renders the Three.js 3D Earth, starfield, dual orbital rings, and moving satellite indicator.
- **`js/charts.js`** — Builds all gradient Chart.js graphs and synchronizes the Leaflet mini-maps inside the analysis tabs.
- **`js/map.js`** — Initializes Leaflet, Leaflet.Draw polygon measurement (hectares & stremmata), OpenStreetMap Nominatim region search, and the **3×3 Variable Rate (VRA)** moisture grid.
- **`js/api.js`** — Fetches live predictions from the FastAPI backend (`http://localhost:8000`), runs the What-If Simulator, and updates the Field A vs. Field B comparison tab.
- **`js/main.js`** — Handles view/sidebar/tab switching and startup initialization.

## Running the Frontend
Serve this folder via **VS Code Live Server** or:
```bash
python -m http.server 5500
```
Then open `http://localhost:5500`.
