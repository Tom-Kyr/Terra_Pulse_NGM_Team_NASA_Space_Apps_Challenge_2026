# TerraPulse Neural Network Training Scripts

Standalone PyTorch training pipelines for all four TerraPulse networks. Running any script trains the model from scratch, logs epoch loss, and saves the `.pth` weights (and `*_preprocess.json` feature scalers where applicable) into `terra_pulse_backend/`.

## Models Overview

1. **`train_network1_water.py` → `terrapulse_water_model.pth`**
   - **Architecture:** MLP (`6 → 16 → 8 → 1`, ReLU + Sigmoid)
   - **Inputs:** Temperature, precipitation, soil moisture, NDVI, slope, evapotranspiration proxy
   - **Output:** `water_stress` (`0–1`)

2. **`train_network2_soil.py` → `terrapulse_soil_model.pth` + `terrapulse_soil_preprocess.json`**
   - **Architecture:** MLP (`6 → 24 → 12 → 2`, ReLU + Sigmoid)
   - **Inputs (standardized):** NDVI, organic matter, slope, rainfall, aridity, moisture
   - **Outputs:** `health_proxy` (`0–1`) & `erosion_proxy` (`0–1`)

3. **`train_network3_rotation.py` → `terrapulse_rotation_model.pth`**
   - **Architecture:** MLP (`5 → 20 → 12 → 4`, ReLU + Sigmoid)
   - **Inputs:** Aridity, organic matter, slope, moisture, soil nitrogen
   - **Outputs:** Suitability scores (`0–1`) for Legumes, Alfalfa, Wheat, and Sorghum

4. **`train_network4_fire.py` → `terrapulse_fire_model.pth` + `terrapulse_fire_preprocess.json`**
   - **Architecture:** MLP (`6 → 24 → 12 → 2`, ReLU + Sigmoid)
   - **Inputs (standardized):** Slope, NDVI, aridity, rainfall intensity, canopy heat, moisture
   - **Outputs:** `erosion_risk` (`0–1`) & `recovery_score` (`0–1`)

## Retraining
From inside `terra_pulse_backend/`:
```bash
python training/train_network1_water.py
python training/train_network2_soil.py
python training/train_network3_rotation.py
python training/train_network4_fire.py
```
