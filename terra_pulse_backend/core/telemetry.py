import math
import torch
from core.config import CROP_PROFILES, IRRIGATION_EFFICIENCY
from core.geo_live import get_live_env_data
from core.model_loader import water_model, water_loaded


def compute_location_profile(
    lat: float,
    lon: float,
    area_ha: float,
    name: str,
    lang: str = "gr",
    crop: str = "wheat",
    irrigation: str = "sprinkler",
    scenario: str = "normal",
):
    live = get_live_env_data(lat, lon)
    crop_cfg = CROP_PROFILES.get(crop, CROP_PROFILES["wheat"])
    irr_cfg = IRRIGATION_EFFICIENCY.get(irrigation, IRRIGATION_EFFICIENCY["sprinkler"])

    if live["source"] == "OPEN-METEO LIVE":
        base_temp = live["avg_temp"]
        slope_deg = live["slope_deg"]
        elevation_m = live["elevation_m"]
        et0_live = live["et0_avg"]
        sm_live = live["live_soil_moisture"]
        aridity_factor = max(0.15, min(0.95, 0.35 + (et0_live / 10.0) * 0.45 - min(0.25, live["recent_precip_30d"] / 180.0)))
    else:
        aridity_factor = max(0.15, min(0.95, 0.52 + 0.25 * math.sin(lat * 0.45) - 0.18 * math.cos(lon * 0.35)))
        slope_deg = round(max(1.2, min(28.0, 4.5 + 11.5 * abs(math.sin(lat * 1.7 + lon * 1.1)))), 1)
        elevation_m = round(45 + slope_deg * 24 + 80 * abs(math.cos(lat * 1.3)), 0)
        base_temp = round(16.0 + (42.0 - abs(lat)) * 0.45 + 2.2 * math.sin(lon * 0.5), 1)
        et0_live = round(3.8 + aridity_factor * 3.1, 1)
        sm_live = round(max(0.09, 0.31 - aridity_factor * 0.16), 3)

    if scenario == "heatwave":
        base_temp = round(base_temp + 5.5, 1)
        aridity_factor = min(0.96, round(aridity_factor + 0.22, 2))
        sm_live = max(0.07, round(sm_live * 0.72, 3))
        et0_live = round(et0_live * 1.35, 1)
    elif scenario == "postfire_storm":
        aridity_factor = min(0.92, round(aridity_factor + 0.12, 2))

    ndvi_avg = round(max(0.18, min(0.86, 0.74 - aridity_factor * 0.34 + 0.08 * math.cos(lat * 2.1))), 2)
    if scenario == "postfire_storm":
        ndvi_avg = round(max(0.15, ndvi_avg * 0.52), 2)
    soil_om = round(max(1.1, min(4.8, 3.6 - aridity_factor * 1.8)), 2)

    if aridity_factor > 0.65:
        soil_type = "Sandy Loam (Calcareous)" if lang == "en" else "Αμμοπηλώδες (Ασβεστούχο)"
    elif slope_deg > 11.0:
        soil_type = "Gravelly Clay Loam" if lang == "en" else "Χαλικώδες Αργιλοπηλώδες"
    else:
        soil_type = "Deep Silty Clay Loam" if lang == "en" else "Βαθύ Ιλυοαργιλοπηλώδες"

    months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct"] if lang == "en" else ["Μάιος", "Ιούν", "Ιούλ", "Αύγ", "Σεπ", "Οκτ"]
    moisture_series, stress_series, precip_series, ndvi_series, et0_series = [], [], [], [], []
    feature_rows = []

    for i in range(6):
        seasonal = math.sin((i + 1) * math.pi / 6.0)
        temp_norm = min(1.0, max(0.1, (base_temp + seasonal * 10.0) / 45.0))
        precip_mm = max(2.0, round((1.0 - aridity_factor) * 65.0 * (1.15 - seasonal * 0.85), 1))
        if scenario == "postfire_storm" and i == 5:
            precip_mm = round(precip_mm + 68.0, 1)
        precip_norm = min(1.0, precip_mm / 90.0)
        moisture = max(0.06, min(0.45, sm_live + 0.04 - seasonal * 0.06 + precip_norm * 0.04))
        ndvi_m = max(0.15, min(0.88, ndvi_avg - seasonal * 0.10 + precip_norm * 0.05))
        slope_norm = min(1.0, slope_deg / 30.0)
        et_proxy = min(1.0, temp_norm * 0.75 + (1.0 - moisture) * 0.25)

        feature_rows.append([temp_norm, precip_norm, moisture, ndvi_m, slope_norm, et_proxy])
        moisture_series.append(round(moisture * 100.0, 1))
        precip_series.append(precip_mm)
        ndvi_series.append(round(ndvi_m, 2))
        et0_series.append(round(max(2.0, et0_live * (0.75 + seasonal * 0.45) * crop_cfg["kc"]), 1))

    if water_loaded:
        with torch.no_grad():
            preds = water_model(torch.tensor(feature_rows, dtype=torch.float32)).squeeze(-1).tolist()
            if isinstance(preds, float):
                preds = [preds]
        stress_series = [
            round(min(98.0, max(12.0, (p * 0.50 + (1.0 - moisture_series[idx] / 40.0) * 0.35 + (crop_cfg["kc"] - 0.7) * 0.25) * 100.0)), 1)
            for idx, p in enumerate(preds)
        ]
    else:
        stress_series = [
            round(min(96.0, max(15.0, (aridity_factor * 0.52 + (1.0 - m / 42.0) * 0.38 + (crop_cfg["kc"] - 0.7) * 0.20) * 100.0)), 1)
            for m in moisture_series
        ]

    if scenario == "heatwave":
        stress_series = [min(98.0, round(s + 14.0, 1)) for s in stress_series]

    min_moisture = round(min(moisture_series) / 100.0, 3)
    avg_stress = round(sum(stress_series) / len(stress_series) / 100.0, 3)

    base_crop_need = (18.0 + avg_stress * 24.0) * crop_cfg["kc"]
    current_water_m3_stremma = round(base_crop_need / irr_cfg["eff"], 1)
    ai_drip_m3_stremma = round((base_crop_need * 0.78) / 0.93, 1)
    stremmata = round(area_ha * 10.0, 1)

    total_current_water_m3 = round(current_water_m3_stremma * stremmata, 1)
    total_ai_water_m3 = round(ai_drip_m3_stremma * stremmata, 1)
    water_saved_m3 = round(max(5.0, total_current_water_m3 - total_ai_water_m3), 1)
    water_saved_pct = round(max(8.0, min(58.0, (water_saved_m3 / max(1.0, total_current_water_m3)) * 100.0)), 1)

    erosion_base = min(0.95, max(0.12, (slope_deg / 30.0) * 0.65 + (1.0 - ndvi_avg) * 0.35))
    if scenario == "postfire_storm":
        erosion_base = min(0.97, erosion_base + 0.25)

    canopy_temp_c = round(base_temp + 3.4 + avg_stress * 6.5, 1)
    et0_avg = round(sum(et0_series) / len(et0_series), 1)
    water_deficit_mm = round(max(12.0, sum(et0_series) * 30 - sum(precip_series)), 0)
    water_cost_saved_eur = round(water_saved_m3 * 0.42, 0)
    energy_saved_eur = round(water_saved_m3 * 0.18, 0)
    fert_saved_eur = round(stremmata * (14.5 + (1.0 - soil_om / 5.0) * 11.0), 0)
    co2_seq_tons = round(area_ha * (1.8 + ndvi_avg * 1.4), 2)

    days_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days_gr = ["Δευ", "Τρί", "Τετ", "Πέμ", "Παρ", "Σάβ", "Κυρ"]
    weekly_schedule = []
    fc_precip = live.get("fc_precip", [0, 0, 2, 0, 0, 0, 0])

    for idx in range(7):
        d_label = days_en[idx] if lang == "en" else days_gr[idx]
        if idx < len(live.get("fc_dates", [])) and live["fc_dates"][idx]:
            d_label = live["fc_dates"][idx][5:]
        rain_mm = fc_precip[idx] if idx < len(fc_precip) else 0.0
        if scenario == "postfire_storm" and idx in [1, 2]:
            rain_mm = 42.0 if idx == 1 else 26.0

        if rain_mm >= 4.0:
            irrigate, mm = False, 0.0
            act = f"Skip: Rain ({rain_mm}mm)" if lang == "en" else f"Παράλειψη: Βροχή ({rain_mm}mm)"
        else:
            irrigate = (idx % 2 == 0) if avg_stress >= 0.5 else (idx in [0, 3, 5])
            mm = round((ai_drip_m3_stremma / 10.0) * (0.45 if irrigate else 0.0), 1)
            act = (
                ("Subsurface Drip (05:30)" if irrigate else "Rest / Sensor Check")
                if lang == "en"
                else ("Υπόγεια Στάγδην (05:30)" if irrigate else "Ανάπαυση / Έλεγχος")
            )
        weekly_schedule.append({"day": d_label, "action": act, "mm": mm, "rain_mm": rain_mm, "active": irrigate})

    vra_grid = []
    for r in range(-1, 2):
        for c_idx in range(-1, 2):
            zone_id = f"{['N','C','S'][r+1]}{['W','C','E'][c_idx+1]}"
            var = 0.14 * math.sin((lat + r * 0.002) * 45 + (lon + c_idx * 0.002) * 35)
            zone_moist = round(max(6.0, min(42.0, min_moisture * 100 + var * 35)), 1)
            zone_stress = round(max(10.0, min(96.0, avg_stress * 100 - var * 40)), 1)
            adj = "+15%" if zone_stress > 65 else ("-15%" if zone_stress < 40 else "0%")
            vra_grid.append({"zone": zone_id, "dr": r, "dc": c_idx, "moisture": zone_moist, "stress": zone_stress, "dose_adj": adj})

    return {
        "data_source": live["source"],
        "crop_label": crop_cfg["en"] if lang == "en" else crop_cfg["gr"],
        "irrigation_label": irr_cfg["en"] if lang == "en" else irr_cfg["gr"],
        "scenario": scenario,
        "location": {"name": name, "lat": round(lat, 4), "lon": round(lon, 4), "area_ha": round(area_ha, 2), "stremmata": stremmata, "elevation_m": int(elevation_m), "soil_type": soil_type},
        "aridity_factor": round(aridity_factor, 2), "slope_deg": slope_deg, "base_temp_c": base_temp,
        "canopy_temp_c": canopy_temp_c, "et0_avg": et0_avg, "water_deficit_mm": int(water_deficit_mm),
        "ndvi_avg": ndvi_avg, "soil_om_pct": soil_om, "min_root_moisture": min_moisture,
        "average_water_stress": avg_stress,
        "water_need_m3_stremma": ai_drip_m3_stremma,
        "current_water_m3_stremma": current_water_m3_stremma,
        "total_water_m3": total_ai_water_m3,
        "total_current_water_m3": total_current_water_m3,
        "water_saved_m3": water_saved_m3, "water_saved_pct": water_saved_pct,
        "water_cost_saved_eur": water_cost_saved_eur, "energy_saved_eur": energy_saved_eur,
        "fert_saved_eur": fert_saved_eur, "co2_seq_tons": co2_seq_tons, "erosion_base": round(erosion_base, 3),
        "months": months, "moisture_series": moisture_series, "stress_series": stress_series,
        "precip_series": precip_series, "ndvi_series": ndvi_series, "et0_series": et0_series,
        "weekly_schedule": weekly_schedule, "vra_grid": vra_grid,
    }