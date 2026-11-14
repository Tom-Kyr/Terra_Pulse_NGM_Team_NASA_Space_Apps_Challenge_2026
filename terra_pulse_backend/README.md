# TerraPulse Backend (FastAPI + PyTorch)

The REST API server that combines live weather/topography feeds with four PyTorch neural networks to generate bilingual (`GR` / `EN`) agricultural advisories.

## Architecture

- **`main.py`** — FastAPI app entry point, CORS configuration, and router registration.
- **`core/config.py`** — Crop water coefficients (`Kc`), irrigation efficiency profiles (`flood`, `sprinkler`, `drip`), and cache settings.
- **`core/model_loader.py`** — Loads all `.pth` PyTorch model weights and `*_preprocess.json` normalizers, and runs `torch.no_grad()` inference.
- **`core/geo_live.py`** — Fetches real 7-day forecasts, `ET₀`, volumetric soil moisture (`0–28 cm`), and 5-point elevation slope from **Open-Meteo** with a 10-minute in-memory cache and offline fallback.
- **`core/telemetry.py`** — Combines live weather, crop/irrigation choices, and Network 1 water-stress inference to build the 180-day profile, 7-day rain-aware schedule, and 3×3 VRA sub-grid.
- **`routes/`** — Modular endpoint handlers:
  - `GET /api/water-analysis` (`routes/water.py`)
  - `GET /api/soil-analysis` (`routes/soil.py`)
  - `GET /api/rotation-analysis` (`routes/rotation.py`)
  - `GET /api/fire-analysis` (`routes/fire.py`)

## Common Query Parameters
All four endpoints accept:
- `lat` & `lon`: Field coordinates (default: Larissa `39.3642, 22.9211`)
- `area_ha`: Field size in hectares (e.g., `4.5` = 45 stremmata)
- `name`: Display name of the region or drawn polygon
- `lang`: `"gr"` or `"en"`
- `crop`: `"wheat"`, `"cotton"`, `"corn"`, `"olives"`, `"vineyard"`, or `"alfalfa"`
- `irrigation`: `"flood"`, `"sprinkler"`, or `"drip"`
- `scenario`: `"normal"`, `"heatwave"`, or `"postfire_storm"`

## Running the Backend
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Interactive Swagger docs are available at `http://localhost:8000/docs`.
