from fastapi import APIRouter, Query
from core.model_loader import load_json_file, water_loaded
from core.telemetry import compute_location_profile

router = APIRouter()


@router.get("/api/water-analysis")
def get_water_analysis(
    lat: float = Query(39.3642), lon: float = Query(22.9211), area_ha: float = Query(4.5),
    name: str = Query("Λάρισα (Θεσσαλικός Κάμπος)"), lang: str = Query("gr"),
    crop: str = Query("wheat"), irrigation: str = Query("sprinkler"), scenario: str = Query("normal"),
):
    base_report = load_json_file("terrapulse_network1_report.json")
    p = compute_location_profile(lat, lon, area_ha, name, lang, crop, irrigation, scenario)
    stress_pct = round(p["average_water_stress"] * 100, 1)
    min_moist_pct = round(p["min_root_moisture"] * 100, 1)
    total_eur = int(p["water_cost_saved_eur"] + p["energy_saved_eur"] + p["fert_saved_eur"])

    if lang == "en":
        if p["average_water_stress"] >= 0.65:
            status, risk_label = "CRITICAL", "CRITICAL WATER STRESS"
            farmer_headline = f"{p['crop_label']} is drying fast — switch {p['irrigation_label']} to morning drip."
            farmer_simple = f"Root moisture drops to {min_moist_pct}% while leaf heat reaches {p['canopy_temp_c']}°C. With {p['irrigation_label']}, you currently use {p['current_water_m3_stremma']} m³/str, wasting {p['water_saved_pct']}% compared to AI-timed subsurface drip ({p['water_need_m3_stremma']} m³/str)."
            prescription = "Pre-dawn drip + Soil mulching"
            steps = [
                f"Water strictly 05:00–07:00 AM using {p['water_need_m3_stremma']} m³/str ({p['total_water_m3']} m³ total).",
                "Avoid midday watering — heat causes >35% evaporation loss.",
                "Watch the 7-day forecast table below to skip watering on rainy days.",
            ]
        elif p["average_water_stress"] >= 0.42:
            status, risk_label = "MODERATE", "MODERATE WATER DEFICIT"
            farmer_headline = f"{p['crop_label']} needs scheduled watering every 48h to protect yield."
            farmer_simple = f"Soil moisture ({min_moist_pct}%) in «{name}» shows moderate thirst ({stress_pct}%). Adjusting from {p['irrigation_label']} ({p['current_water_m3_stremma']} m³/str) to AI-timed drip ({p['water_need_m3_stremma']} m³/str) saves {p['water_saved_m3']} m³ and ~{int(p['water_cost_saved_eur'] + p['energy_saved_eur'])} €."
            prescription = "48h pulsed AI irrigation"
            steps = [
                f"Irrigate every 2 days with {p['water_need_m3_stremma']} m³/str following the 7-day forecast below.",
                "Check emitters across the orange/red VRA grid zones shown on the map.",
                f"Capture ~{int(p['water_cost_saved_eur'] + p['energy_saved_eur'])} €/yr savings in water & pump electricity.",
            ]
        else:
            status, risk_label = "OPTIMAL", "OPTIMAL HYDRATION"
            farmer_headline = f"{p['crop_label']} hydration is balanced — cut back pump hours and save."
            farmer_simple = f"Moisture ({min_moist_pct}%) comfortably supports {p['crop_label']}. You can reduce watering frequency by 25% without hurting harvest."
            prescription = "Light maintenance watering"
            steps = [
                "Trim irrigation runtime by 25% to avoid washing nutrients past the roots.",
                "Let natural rainfall in the 7-day schedule cover light moisture needs.",
            ]
        conclusions = f"1. HYDROLOGICAL SUMMARY ({risk_label} | {p['data_source']})\nZone: «{name}» ({p['location']['stremmata']} str, Elev. {p['location']['elevation_m']} m, {p['location']['soil_type']}). Crop: {p['crop_label']} under {p['irrigation_label']}.\n\n2. SAVINGS IMPACT\nSwitching to TerraPulse AI saves {p['water_saved_m3']} m³ ({p['water_saved_pct']}%) = ~{total_eur} €/yr combined savings & {p['co2_seq_tons']} t CO₂e stored."
        cost_labels = ["Water (€)", "Pump Power (€)", "Fertilizer (€)"]
        bench_labels = ["Root Moisture (%)", "Crop Vigor (%)", "Efficiency (%)"]
    else:
        if p["average_water_stress"] >= 0.65:
            status, risk_label = "CRITICAL", "ΚΡΙΣΙΜΟ ΥΔΑΤΙΚΟ ΣΤΡΕΣ"
            farmer_headline = f"Το {p['crop_label']} διψάει έντονα — χρειάζεται πρωινή στάγδην άρδευση."
            farmer_simple = f"Η υγρασία ρίζας πέφτει στο {min_moist_pct}% και η ζέστη φύλλων φτάνει τους {p['canopy_temp_c']}°C. Με {p['irrigation_label']} καταναλώνετε {p['current_water_m3_stremma']} m³/στρ, ενώ με έξυπνη στάγδην ({p['water_need_m3_stremma']} m³/στρ) γλιτώνετε {p['water_saved_pct']}% νερό."
            prescription = "Πρωινή στάγδην + Εδαφοκάλυψη"
            steps = [
                f"Ποτίστε αυστηρά 05:00–07:00 με {p['water_need_m3_stremma']} m³/στρ (σύνολο {p['total_water_m3']} m³).",
                "Μην ποτίζετε μεσημέρι — πάνω από 35% του νερού χάνεται στον αέρα.",
                "Ακολουθήστε τον 7ήμερο πίνακα καιρού παρακάτω ώστε να μην ποτίσετε πριν από βροχή.",
            ]
        elif p["average_water_stress"] >= 0.42:
            status, risk_label = "MODERATE", "ΜΕΤΡΙΟ ΥΔΑΤΙΚΟ ΕΛΛΕΙΜΜΑ"
            farmer_headline = f"Το {p['crop_label']} θέλει τακτικό πότισμα ανά 48 ώρες για μέγιστη απόδοση."
            farmer_simple = f"Στην περιοχή «{name}» η υγρασία ({min_moist_pct}%) προκαλεί μέτρια δίψα ({stress_pct}%). Περνώντας από {p['irrigation_label']} ({p['current_water_m3_stremma']} m³/στρ) σε έξυπνη στάγδην ({p['water_need_m3_stremma']} m³/στρ) γλιτώνετε {p['water_saved_m3']} m³ και ~{int(p['water_cost_saved_eur'] + p['energy_saved_eur'])} €."
            prescription = "Παλμική άρδευση 48 ωρών"
            steps = [
                f"Ποτίστε ανά 2 ημέρες με {p['water_need_m3_stremma']} m³/στρ βάσει της 7ήμερης πρόγνωσης.",
                "Ελέγξτε τα πορτοκαλί/κόκκινα τετράγωνα του πλέγματος (VRA) στον χάρτη για τυχόν βουλωμένους σταλάκτες.",
                f"Εξοικονομήστε ~{int(p['water_cost_saved_eur'] + p['energy_saved_eur'])} €/έτος σε νερό & ρεύμα αντλίας.",
            ]
        else:
            status, risk_label = "OPTIMAL", "ΒΕΛΤΙΣΤΗ ΥΔΑΤΙΚΗ ΙΣΟΡΡΟΠΙΑ"
            farmer_headline = f"Το {p['crop_label']} έχει άριστη υγρασία — μειώστε τις ώρες αντλίας."
            farmer_simple = f"Η υγρασία ({min_moist_pct}%) καλύπτει άνετα το {p['crop_label']}. Μειώνοντας τα ποτίσματα κατά 25% εξοικονομείτε ρεύμα χωρίς απώλεια παραγωγής."
            prescription = "Ελαφριά συντήρηση υγρασίας"
            steps = [
                "Μειώστε τα ποτίσματα κατά 25% για να μην ξεπλένονται τα θρεπτικά στοιχεία.",
                "Αφήστε τις βροχοπτώσεις του 7ήμερου προγράμματος να καλύψουν τη ριζόσφαιρα.",
            ]
        conclusions = f"1. ΕΠΙΣΤΗΜΟΝΙΚΗ ΥΔΡΟΛΟΓΙΚΗ ΔΙΑΓΝΩΣΗ ({risk_label} | {p['data_source']})\nΠεριοχή: «{name}» ({p['location']['stremmata']} στρ., Υψόμ. {p['location']['elevation_m']} m, {p['location']['soil_type']}). Καλλιέργεια: {p['crop_label']} με {p['irrigation_label']}.\n\n2. ΟΙΚΟΝΟΜΙΚΟ & ΕΝΕΡΓΕΙΑΚΟ ΟΦΕΛΟΣ\nΗ μετάβαση στο TerraPulse AI γλιτώνει {p['water_saved_m3']} m³ ({p['water_saved_pct']}%) = ~{total_eur} €/έτος συνολικό όφελος και {p['co2_seq_tons']} τόνους CO₂e."
        cost_labels = ["Νερό (€)", "Ρεύμα Αντλίας (€)", "Λιπάσματα (€)"]
        bench_labels = ["Υγρασία Ρίζας (%)", "Υγεία Φύλλων (%)", "Αποδοτικότητα (%)"]

    trad_water_eur = round(p["total_current_water_m3"] * 0.42)
    trad_energy_eur = round(p["total_current_water_m3"] * 0.18)
    trad_fert_eur = round(p["location"]["stremmata"] * 38)
    ai_water_eur = max(20, round(trad_water_eur - p["water_cost_saved_eur"]))
    ai_energy_eur = max(10, round(trad_energy_eur - p["energy_saved_eur"]))
    ai_fert_eur = max(30, round(trad_fert_eur - p["fert_saved_eur"]))

    return {
        **base_report,
        "location": p["location"], "status": status, "data_source": p["data_source"],
        "farmer_headline": farmer_headline, "reasoning": farmer_simple, "action_steps": steps,
        "vra_grid": p["vra_grid"],
        "metrics": {
            "min_root_moisture": p["min_root_moisture"], "average_water_stress": p["average_water_stress"],
            "water_need_m3_stremma": p["water_need_m3_stremma"], "current_water_m3_stremma": p["current_water_m3_stremma"],
            "total_water_m3": p["total_water_m3"], "water_saved_m3": p["water_saved_m3"], "water_saved_pct": p["water_saved_pct"],
            "water_cost_saved_eur": p["water_cost_saved_eur"], "energy_saved_eur": p["energy_saved_eur"],
            "fert_saved_eur": p["fert_saved_eur"], "total_saved_eur": total_eur, "co2_seq_tons": p["co2_seq_tons"],
            "ndvi_avg": p["ndvi_avg"], "soil_om_pct": p["soil_om_pct"], "slope_deg": p["slope_deg"],
            "base_temp_c": p["base_temp_c"], "canopy_temp_c": p["canopy_temp_c"], "et0_avg": p["et0_avg"],
            "water_deficit_mm": p["water_deficit_mm"], "prescription": prescription, "risk_label": risk_label,
            "model_mode": ("PyTorch Network 1 (Live)" if water_loaded else "Telemetry Synthesis"),
        },
        "weekly_schedule": p["weekly_schedule"],
        "charts": {
            "months": p["months"], "moisture_series": p["moisture_series"], "stress_series": p["stress_series"],
            "precip_series": p["precip_series"], "ndvi_series": p["ndvi_series"], "et0_series": p["et0_series"],
            "cost_comparison": {"labels": cost_labels, "traditional": [trad_water_eur, trad_energy_eur, trad_fert_eur], "terrapulse": [ai_water_eur, ai_energy_eur, ai_fert_eur]},
            "benchmark": {"labels": bench_labels, "field": [round(min_moist_pct * 2.1, 1), round(p["ndvi_avg"] * 100, 1), round(55 + p["water_saved_pct"] * 0.65, 1)], "regional_avg": [48.0, 56.0, 52.0], "optimal": [82.0, 84.0, 92.0]},
        },
        "conclusions": conclusions,
    }