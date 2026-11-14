import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_TTL_SEC = 600

CROP_PROFILES = {
    "wheat": {"kc": 0.85, "en": "Durum Wheat", "gr": "Σκληρό Σιτάρι"},
    "cotton": {"kc": 1.15, "en": "Cotton", "gr": "Βαμβάκι"},
    "corn": {"kc": 1.22, "en": "Corn (Maize)", "gr": "Καλαμπόκι"},
    "olives": {"kc": 0.65, "en": "Olive Grove", "gr": "Ελαιώνας"},
    "vineyard": {"kc": 0.72, "en": "Vineyard", "gr": "Αμπελώνας"},
    "alfalfa": {"kc": 1.10, "en": "Alfalfa", "gr": "Μηδική"},
}

IRRIGATION_EFFICIENCY = {
    "flood": {"eff": 0.52, "en": "Flood Irrigation", "gr": "Κατάκλυση (Αυλάκια)"},
    "sprinkler": {"eff": 0.74, "en": "Overhead Sprinkler", "gr": "Καταιονισμός (Μπεκ)"},
    "drip": {"eff": 0.93, "en": "Subsurface Drip", "gr": "Στάγδην Άρδευση"},
}