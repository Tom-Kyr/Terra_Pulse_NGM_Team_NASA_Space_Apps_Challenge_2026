import json
import math
import time
import urllib.request
from core.config import CACHE_TTL_SEC

_GEO_CACHE = {}


def fetch_json_url(url: str, timeout: float = 2.4):
    req = urllib.request.Request(url, headers={"User-Agent": "TerraPulse-SpaceApps/2026"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_live_env_data(lat: float, lon: float):
    key = (round(lat, 3), round(lon, 3))
    now = time.time()
    if key in _GEO_CACHE and (now - _GEO_CACHE[key]["ts"]) < CACHE_TTL_SEC:
        return _GEO_CACHE[key]["data"]

    result = {"source": "SYNTHESIS"}
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&daily=temperature_2m_max,precipitation_sum,et0_fao_evapotranspiration"
            "&hourly=soil_moisture_0_to_7cm,soil_moisture_7_to_28cm"
            "&forecast_days=7&past_days=30&timezone=auto"
        )
        w = fetch_json_url(weather_url, timeout=2.5)
        daily = w.get("daily", {})
        hourly = w.get("hourly", {})

        temps = [t for t in daily.get("temperature_2m_max", []) if t is not None]
        precips = [p for p in daily.get("precipitation_sum", []) if p is not None]
        et0s = [e for e in daily.get("et0_fao_evapotranspiration", []) if e is not None]
        sm_vals = [s for s in hourly.get("soil_moisture_7_to_28cm", []) if s is not None]
        if not sm_vals:
            sm_vals = [s for s in hourly.get("soil_moisture_0_to_7cm", []) if s is not None]

        fc_precip = daily.get("precipitation_sum", [])[-7:]
        fc_et0 = daily.get("et0_fao_evapotranspiration", [])[-7:]
        fc_temps = daily.get("temperature_2m_max", [])[-7:]
        fc_dates = daily.get("time", [])[-7:]

        # 5-point elevation slope query
        delta = 0.0012
        elev_lats = f"{lat},{lat+delta},{lat-delta},{lat},{lat}"
        elev_lons = f"{lon},{lon},{lon},{lon+delta},{lon-delta}"
        elev_url = f"https://api.open-meteo.com/v1/elevation?latitude={elev_lats}&longitude={elev_lons}"
        elev_data = fetch_json_url(elev_url, timeout=2.0)
        elevs = elev_data.get("elevation", [120, 120, 120, 120, 120])
        center_elev = round(elevs[0])

        horiz_dist_m = 2.0 * delta * 111320.0
        dz_ns = abs(elevs[1] - elevs[2])
        dz_ew = abs(elevs[3] - elevs[4]) * max(0.3, math.cos(math.radians(lat)))
        slope_deg = round(max(0.8, min(32.0, math.degrees(math.atan(math.hypot(dz_ns, dz_ew) / horiz_dist_m)))), 1)

        result = {
            "source": "OPEN-METEO LIVE",
            "avg_temp": round(sum(temps) / len(temps), 1) if temps else 24.0,
            "recent_precip_30d": round(sum(precips[:-7]) if len(precips) > 7 else sum(precips), 1),
            "et0_avg": round(sum(et0s) / len(et0s), 1) if et0s else 4.5,
            "live_soil_moisture": round(sum(sm_vals[-24:]) / len(sm_vals[-24:]), 3) if sm_vals else 0.22,
            "min_soil_moisture": round(min(sm_vals), 3) if sm_vals else 0.14,
            "fc_precip": [round(x or 0.0, 1) for x in fc_precip],
            "fc_et0": [round(x or 4.0, 1) for x in fc_et0],
            "fc_temps": [round(x or 25.0, 1) for x in fc_temps],
            "fc_dates": fc_dates,
            "elevation_m": center_elev,
            "slope_deg": slope_deg,
        }
    except Exception as e:
        print(f"Live Open-Meteo fallback for ({lat},{lon}): {e}")

    _GEO_CACHE[key] = {"ts": now, "data": result}
    return result