import math
from fastapi import APIRouter, Query
from core.model_loader import soil_pth, soil_preprocess, normalize_features, run_generic_pth_inference
from core.telemetry import compute_location_profile

router = APIRouter()


@router.get("/api/soil-analysis")
def get_soil_analysis(
    lat: float = Query(39.3642), lon: float = Query(22.9211), area_ha: float = Query(4.5),
    name: str = Query("Λάρισα (Θεσσαλικός Κάμπος)"), lang: str = Query("gr"),
    crop: str = Query("wheat"), irrigation: str = Query("sprinkler"), scenario: str = Query("normal"),
):
    p = compute_location_profile(lat, lon, area_ha, name, lang, crop, irrigation, scenario)
    raw_features = [p["ndvi_avg"], p["soil_om_pct"] / 5.0, p["slope_deg"] / 30.0, sum(p["precip_series"]) / 400.0, p["aridity_factor"], p["min_root_moisture"]]
    model_out = run_generic_pth_inference(soil_pth, normalize_features(raw_features, soil_preprocess), expected_outputs=2)

    base_health = max(0.18, min(0.95, 0.55 * (p["ndvi_avg"] / 0.85) + 0.45 * (p["soil_om_pct"] / 4.5)))
    base_erosion = p["erosion_base"]

    if model_out is not None:
        health_proxy = round(max(0.1, min(0.96, 0.45 * model_out[0] + 0.55 * base_health)), 3)
        erosion_proxy = round(max(0.08, min(0.95, 0.45 * model_out[1] + 0.55 * base_erosion)), 3)
        mode = "PyTorch Network 2 (Live)"
    else:
        health_proxy, erosion_proxy, mode = round(base_health, 3), round(base_erosion, 3), "Soil Telemetry Synthesis"

    health_pct, erosion_pct = round(health_proxy * 100, 1), round(erosion_proxy * 100, 1)

    if lang == "en":
        if health_proxy < 0.50 or erosion_proxy > 0.60:
            status, status_label = "CRITICAL", "TIRED SOIL & EROSION RISK"
            farmer_headline = "Your soil is losing fertility and washes away easily in rain."
            reasoning = f"Soil health is low ({health_pct}%) and erosion risk is {erosion_pct}% because organic matter dropped to {p['soil_om_pct']}% on a {p['slope_deg']}° slope."
            steps = [
                "Skip deep plowing this season (shallow/no-till) to keep topsoil intact.",
                "Sow winter cover plants like vetch or clover for free natural nitrogen.",
                f"Spread compost/residue to lift organic matter from {p['soil_om_pct']}% toward 3.5%+.",
            ]
        elif health_proxy < 0.72:
            status, status_label = "MODERATE", "MODERATE SOIL FATIGUE"
            farmer_headline = "Your soil works well, but needs biological support to cut fertilizer bills."
            reasoning = f"Soil health is {health_pct}% and erosion risk is {erosion_pct}%. Rotating with legumes lets you buy ~42% less synthetic fertilizer."
            steps = [
                "Cut synthetic nitrogen by 35–45% and add legumes next season.",
                "Plow/plant across the slope (contour lines) to keep rainwater inside the field.",
                f"Save ~{int(p['fert_saved_eur'])} €/yr using variable-rate fertilizer zones.",
            ]
        else:
            status, status_label = "OPTIMAL", "HEALTHY & FERTILE SOIL"
            farmer_headline = "Your soil is healthy, alive, and protected against erosion."
            reasoning = f"Strong soil health ({health_pct}%) and low erosion ({erosion_pct}%). Good plant cover protects microbes and holds moisture."
            steps = ["Keep sowing cover strips between main harvests.", "Only apply light maintenance fertilizer doses."]
        conclusions = f"1. NETWORK 2 SOIL DIAGNOSTIC ({status_label})\nZone: «{name}» ({p['location']['stremmata']} str, {p['location']['soil_type']}). health_proxy={health_proxy}, erosion_proxy={erosion_proxy}, OM={p['soil_om_pct']}%.\n\n2. RESTORATION ROI\nCutting synthetic fertilizer by ~42% yields ~{int(p['fert_saved_eur'])} €/yr + {p['co2_seq_tons']} t CO₂e stored."
        npk_labels = ["Nitrogen (N)", "Phosphorus (P)", "Potassium (K)", "Organic Carbon"]
    else:
        if health_proxy < 0.50 or erosion_proxy > 0.60:
            status, status_label = "CRITICAL", "ΚΟΥΡΑΣΜΕΝΟ ΕΔΑΦΟΣ & ΚΙΝΔΥΝΟΣ ΔΙΑΒΡΩΣΗΣ"
            farmer_headline = "Το χώμα έχει εξαντληθεί και κινδυνεύει να παρασυρθεί από τις βροχές."
            reasoning = f"Η υγεία εδάφους είναι χαμηλή ({health_pct}%) και ο κίνδυνος διάβρωσης {erosion_pct}% λόγω οργανικής ουσίας {p['soil_om_pct']}% σε κλίση {p['slope_deg']}°."
            steps = [
                "Μην οργώσετε βαθιά φέτος (επιφανειακός καλλιεργητής / no-till).",
                "Σπείρετε χειμερινό βίκο ή τριφύλλι για ριζική συγκράτηση & δωρεάν άζωτο.",
                f"Αφήστε φυτικά υπολείμματα/κομπόστ για να ανέβει η οργανική ουσία πάνω από 3.5%.",
            ]
        elif health_proxy < 0.72:
            status, status_label = "MODERATE", "ΜΕΤΡΙΑ ΚΟΥΡΑΣΗ ΕΔΑΦΟΥΣ"
            farmer_headline = "Το χώμα αποδίδει, αλλά χρειάζεται φυσική ενίσχυση για μείωση λιπασμάτων."
            reasoning = f"Υγεία εδάφους {health_pct}% και διάβρωση {erosion_pct}%. Η εναλλαγή με ψυχανθή μειώνει το χημικό λίπασμα κατά ~42%."
            steps = [
                "Μειώστε το αζωτούχο λίπασμα κατά 35–45% βάζοντας ψυχανθή στον επόμενο κύκλο.",
                "Καλλιεργείτε κάθετα στην κλίση ώστε το νερό βροχής να μένει στο χωράφι.",
                f"Εξοικονομήστε ~{int(p['fert_saved_eur'])} €/έτος ρίχνοντας λίπασμα στοχευμένα.",
            ]
        else:
            status, status_label = "OPTIMAL", "ΥΓΙΕΣ & ΓΟΝΙΜΟ ΧΩΜΑ"
            farmer_headline = "Το έδαφος είναι πολύ υγιές, ζωντανό και προστατευμένο."
            reasoning = f"Υψηλή υγεία εδάφους ({health_pct}%) και χαμηλή διάβρωση ({erosion_pct}%). Το χώμα κρατάει καλά υγρασία και θρεπτικά στοιχεία."
            steps = ["Συνεχίστε τα φυτά κάλυψης ανάμεσα στις βασικές σπορές.", "Περιοριστείτε σε μικρές δόσεις συντήρησης."]
        conclusions = f"1. ΕΠΙΣΤΗΜΟΝΙΚΗ ΔΙΑΓΝΩΣΗ ΔΙΚΤΥΟΥ 2 ({status_label})\nΠεριοχή: «{name}» ({p['location']['stremmata']} στρ., {p['location']['soil_type']}). health_proxy={health_proxy}, erosion_proxy={erosion_proxy}, Οργανική Ουσία={p['soil_om_pct']}%.\n\n2. ΟΙΚΟΝΟΜΙΚΟ ΟΦΕΛΟΣ\nΗ μείωση χημικών λιπασμάτων κατά ~42% αποδίδει ~{int(p['fert_saved_eur'])} €/έτος + {p['co2_seq_tons']} t CO₂e."
        npk_labels = ["Άζωτο (N)", "Φώσφορος (P)", "Κάλιο (K)", "Οργανικός Άνθρακας"]

    health_trend = [round(max(15, min(98, health_pct + 4 * math.cos(i * 0.8) - i * 1.1)), 1) for i in range(6)]
    erosion_trend = [round(max(8, min(95, erosion_pct + 6 * math.sin(i * 0.9))), 1) for i in range(6)]
    npk_current = [round(min(95, health_pct * 0.85), 1), round(min(95, health_pct * 0.78), 1), round(min(95, health_pct * 0.92), 1), round(min(95, p["soil_om_pct"] * 19.0), 1)]

    return {
        "location": p["location"], "status": status, "status_label": status_label,
        "farmer_headline": farmer_headline, "reasoning": reasoning, "action_steps": steps,
        "metrics": {"health_proxy": health_proxy, "erosion_proxy": erosion_proxy, "health_pct": health_pct, "erosion_pct": erosion_pct, "ndvi_avg": p["ndvi_avg"], "soil_om_pct": p["soil_om_pct"], "fert_saved_eur": p["fert_saved_eur"], "co2_seq_tons": p["co2_seq_tons"], "model_mode": mode},
        "charts": {"months": p["months"], "health_trend": health_trend, "erosion_trend": erosion_trend, "npk_labels": npk_labels, "npk_current": npk_current, "npk_target": [85, 82, 88, 84], "soil_radar": [round(min(95, p["ndvi_avg"] * 100), 1), round(min(95, p["soil_om_pct"] * 20), 1), round(max(20, 88 - p["average_water_stress"] * 45), 1), round(max(20, 100 - erosion_pct), 1), health_pct]},
        "conclusions": conclusions,
    }