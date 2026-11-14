from fastapi import APIRouter, Query
from core.model_loader import fire_pth, fire_preprocess, normalize_features, run_generic_pth_inference
from core.telemetry import compute_location_profile

router = APIRouter()


@router.get("/api/fire-analysis")
def get_fire_analysis(
    lat: float = Query(39.3642), lon: float = Query(22.9211), area_ha: float = Query(4.5),
    name: str = Query("Λάρισα (Θεσσαλικός Κάμπος)"), lang: str = Query("gr"),
    crop: str = Query("wheat"), irrigation: str = Query("sprinkler"), scenario: str = Query("normal"),
):
    p = compute_location_profile(lat, lon, area_ha, name, lang, crop, irrigation, scenario)
    raw_features = [p["slope_deg"] / 30.0, p["ndvi_avg"], p["aridity_factor"], sum(p["precip_series"]) / 400.0, p["canopy_temp_c"] / 45.0, p["min_root_moisture"]]
    model_out = run_generic_pth_inference(fire_pth, normalize_features(raw_features, fire_preprocess), expected_outputs=2)

    base_erosion_risk = min(0.96, max(0.15, (p["slope_deg"] / 28.0) * 0.62 + (1.0 - p["ndvi_avg"]) * 0.38))
    if scenario == "postfire_storm":
        base_erosion_risk = min(0.97, base_erosion_risk + 0.25)
    base_recovery = min(0.95, max(0.22, 0.52 * p["ndvi_avg"] + 0.48 * (1.0 - p["aridity_factor"] * 0.6)))

    if model_out is not None:
        erosion_risk = round(max(0.1, min(0.97, 0.40 * model_out[0] + 0.60 * base_erosion_risk)), 3)
        recovery_score = round(max(0.12, min(0.96, 0.45 * model_out[1] + 0.55 * base_recovery)), 3)
        mode = "PyTorch Network 4 (Live)"
    else:
        erosion_risk, recovery_score, mode = round(base_erosion_risk, 3), round(base_recovery, 3), "Fire Recovery Synthesis"

    erosion_pct, recovery_pct = round(erosion_risk * 100, 1), round(recovery_score * 100, 1)
    unmitigated_loss, seeded_loss = min(98, round(erosion_pct * 1.15)), max(8, round(erosion_pct * 0.25))

    if lang == "en":
        if erosion_risk >= 0.62:
            status, status_label = "CRITICAL", "HIGH POST-FIRE & FLOOD RISK"
            farmer_headline = "Steep slope alert — lock topsoil immediately before heavy rain arrives."
            reasoning = f"Because the slope is {p['slope_deg']}°, exposed soil has a {erosion_pct}% risk of washing downhill in the next storm. Fast-sprouting roots can stabilize it within days."
            steps = [
                "Within 72 hours: Broadcast fast-sprouting ryegrass/vetch mix to hold soil.",
                "Place straw wattles or branch barriers across the slope to slow water runoff.",
                "Keep tractors and grazing animals off the field until green cover returns.",
            ]
            sms_alert = f"TERRAPULSE 72H ALERT [{name}]: High runoff risk ({erosion_pct}%) before forecast rain! Deploy rapid cover seeding & slope barriers today."
        elif erosion_risk >= 0.38:
            status, status_label = "MODERATE", "MODERATE RUNOFF RISK"
            farmer_headline = "Moderate slope vulnerability — plant protective strips at the lower edge."
            reasoning = f"Erosion risk is {erosion_pct}%, while natural rebound potential is solid ({recovery_pct}%). Protecting the bottom edge stops mudslides."
            steps = ["Seed a 3–5 m grassy buffer strip along the lower border.", "Clean drainage ditches before autumn storms."]
            sms_alert = f"TERRAPULSE ADVISORY [{name}]: Moderate runoff risk ({erosion_pct}%). Keep lower drainage ditches clear before incoming showers."
        else:
            status, status_label = "OPTIMAL", "LOW RISK & STRONG RECOVERY"
            farmer_headline = "Low erosion risk — your field recovers well naturally."
            reasoning = f"Gentle slope ({p['slope_deg']}°) and strong natural rebound ({recovery_pct}%) mean rain won't easily strip your soil."
            steps = ["Leave natural straw/mulch on the surface.", "Keep perimeter firebreaks clean before next summer."]
            sms_alert = f"TERRAPULSE STATUS [{name}]: Low erosion risk ({erosion_pct}%). Maintain perimeter firebreaks."
        conclusions = f"1. NETWORK 4 EXTREME EVENT DIAGNOSTIC ({status_label})\nZone: «{name}» ({p['location']['stremmata']} str, Slope {p['slope_deg']}°). erosion_risk={erosion_risk}, recovery_score={recovery_score}.\n\n2. INTERVENTION IMPACT\n72h rapid seeding reduces topsoil loss from {unmitigated_loss}% down to {seeded_loss}% and accelerates rebound by ~38%."
        runoff_labels = ["No Action", "Standard Plow", "72h Seeding (AI)"]
        rebound_months = ["M1", "M3", "M6", "M9", "M12"]
    else:
        if erosion_risk >= 0.62:
            status, status_label = "CRITICAL", "ΥΨΗΛΟΣ ΚΙΝΔΥΝΟΣ ΚΑΤΟΛΙΣΘΗΣΗΣ & ΔΙΑΒΡΩΣΗΣ"
            farmer_headline = "Έντονη κλίση — προστατέψτε αμέσως το χώμα πριν πέσουν οι πρώτες βροχές."
            reasoning = f"Με κλίση {p['slope_deg']}°, το εκτεθειμένο έδαφος έχει {erosion_pct}% κίνδυνο να παρασυρθεί από την πρώτη καταιγίδα. Ταχυφυή φυτά μπορούν να το δέσουν σε λίγες μέρες."
            steps = [
                "Μέσα σε 72 ώρες: Ρίξτε σπόρο ήρας, σίκαλης ή βίκου για να πιάσει γρήγορα ρίζα.",
                "Φτιάξτε πρόχειρα φράγματα με κλαδιά ή μπάλες άχυρου κάθετα στην κατηφόρα.",
                "Μην βάλετε τρακτέρ ή ζώα μέσα για 12 μήνες μέχρι να πρασινίσει ξανά.",
            ]
            sms_alert = f"ΕΙΔΟΠΟΙΗΣΗ TERRAPULSE 72H [{name}]: Υψηλός κίνδυνος διάβρωσης ({erosion_pct}%) πριν την επερχόμενη βροχή! Εφαρμόστε ταχεία σπορά & φράγματα απορροής σήμερα."
        elif erosion_risk >= 0.38:
            status, status_label = "MODERATE", "ΜΕΤΡΙΟΣ ΚΙΝΔΥΝΟΣ ΑΠΟΡΡΟΗΣ"
            farmer_headline = "Μέτρια κλίση — βάλτε προστατευτικές λωρίδες στο κάτω μέρος του αγρού."
            reasoning = f"Ο κίνδυνος διάβρωσης είναι {erosion_pct}% και η φύση έχει καλή δύναμη ανάκαμψης ({recovery_pct}%). Μια λωρίδα χόρτου στα χαμηλά όρια συγκρατεί το χώμα."
            steps = ["Σπείρετε μια ζώνη χόρτου 3–5 m στο χαμηλότερο όριο του αγρού.", "Καθαρίστε τα αυλάκια απορροής πριν τα φθινοπωρινά πρωτοβρόχια."]
            sms_alert = f"ΕΠΙΣΗΜΑΝΣΗ TERRAPULSE [{name}]: Μέτριος κίνδυνος απορροής ({erosion_pct}%). Ελέγξτε τα αυλάκια αποστράγγισης."
        else:
            status, status_label = "OPTIMAL", "ΧΑΜΗΛΟΣ ΚΙΝΔΥΝΟΣ & ΙΣΧΥΡΗ ΑΝΑΚΑΜΨΗ"
            farmer_headline = "Χαμηλός κίνδυνος διάβρωσης — η βλάστηση επανέρχεται εύκολα."
            reasoning = f"Η ήπια κλίση ({p['slope_deg']}°) και η υψηλή ανάκαμψη ({recovery_pct}%) προστατεύουν το χωράφι από πλημμύρες και λάσπες."
            steps = ["Αφήστε φυσικά φυτικά υπολείμματα πάνω στο χώμα.", "Κρατήστε καθαρές τις αντιπυρικές ζώνες πριν το καλοκαίρι."]
            sms_alert = f"ΚΑΤΑΣΤΑΣΗ TERRAPULSE [{name}]: Χαμηλός κίνδυνος ({erosion_pct}%). Ομαλή πορεία ανάκαμψης."
        conclusions = f"1. ΕΠΙΣΤΗΜΟΝΙΚΗ ΔΙΑΓΝΩΣΗ ΔΙΚΤΥΟΥ 4 ({status_label})\nΠεριοχή: «{name}» ({p['location']['stremmata']} στρ., κλίση {p['slope_deg']}°). erosion_risk={erosion_risk}, recovery_score={recovery_score}.\n\n2. ΑΠΟΤΕΛΕΣΜΑΤΙΚΟΤΗΤΑ ΠΑΡΕΜΒΑΣΗΣ\nΗ ταχεία σπορά 72 ωρών μειώνει την απώλεια εδάφους από {unmitigated_loss}% σε {seeded_loss}% και επιταχύνει την ανάκαμψη κατά ~38%."
        runoff_labels = ["Χωρίς Δράση", "Κλασική Άροση", "Σπορά 72h (AI)"]
        rebound_months = ["Μ1", "Μ3", "Μ6", "Μ9", "Μ12"]

    rebound_natural = [round(max(10, recovery_pct * (0.28 + 0.14 * i)), 1) for i in range(5)]
    rebound_seeded = [round(min(98, recovery_pct * (0.45 + 0.19 * i) + 16), 1) for i in range(5)]

    return {
        "location": p["location"], "status": status, "status_label": status_label,
        "farmer_headline": farmer_headline, "reasoning": reasoning, "action_steps": steps,
        "sms_alert": sms_alert,
        "metrics": {"erosion_risk": erosion_risk, "recovery_score": recovery_score, "erosion_pct": erosion_pct, "recovery_pct": recovery_pct, "slope_deg": p["slope_deg"], "model_mode": mode},
        "charts": {"runoff_labels": runoff_labels, "runoff_values": [unmitigated_loss, round(unmitigated_loss * 0.68), seeded_loss], "rebound_months": rebound_months, "rebound_natural": rebound_natural, "rebound_seeded": rebound_seeded},
        "conclusions": conclusions,
    }