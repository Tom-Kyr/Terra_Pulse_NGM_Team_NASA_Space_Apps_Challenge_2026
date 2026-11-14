/* ==================== PREVENT BROWSER PAGE ZOOM BUG ==================== */
window.addEventListener('wheel', (e) => {
    if (e.ctrlKey) {
        e.preventDefault();
        const mapEl = document.getElementById('map');
        if (window.mapInstance && mapEl && mapEl.contains(e.target)) {
            if (e.deltaY < 0) window.mapInstance.zoomIn(0.5);
            else if (e.deltaY > 0) window.mapInstance.zoomOut(0.5);
        }
    }
}, { passive: false });

window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && ['+', '-', '=', '0'].includes(e.key)) e.preventDefault();
});
window.addEventListener('gesturestart', (e) => e.preventDefault());

/* ==================== GLOBAL APPLICATION STATE ==================== */
const API_BASE = 'http://localhost:8000';
let currentLang = 'gr';
let activeAnalysisTab = 'drought';
let isDrawingOrEditing = false;
let isSpeaking = false;

let activeState = {
    lat: 39.3642,
    lon: 22.9211,
    areaHa: 4.5,
    nameEn: 'Larissa (Thessaly Basin)',
    nameGr: 'Λάρισα (Θεσσαλικός Κάμπος)',
    isCustom: false,
    polygonLatLngs: null
};

let simState = {
    crop: 'wheat',
    irrigation: 'sprinkler',
    scenario: 'normal'
};

let latestPayloads = { water: null, soil: null, rotation: null, fire: null };

let fieldSlots = {
    A: { name: 'Λάρισα (Θεσσαλικός Κάμπος)', stress: 58, soil: 66, fire: 38, eur: 1420 },
    B: { name: 'Ηράκλειο (Μεσσαρά)', stress: 79, soil: 48, fire: 64, eur: 1680 }
};

/* ==================== UI, THEME & LANGUAGE HELPERS ==================== */
function getActiveLabel() {
    if (!activeState.isCustom) return currentLang === 'en' ? activeState.nameEn : activeState.nameGr;
    if (activeState.polygonLatLngs) {
        const str = (activeState.areaHa * 10).toFixed(1);
        return currentLang === 'en' ? `Field Polygon (${str} str)` : `Αγροτεμάχιο (${str} στρ.)`;
    }
    return currentLang === 'en'
        ? `Point (${activeState.lat.toFixed(3)}, ${activeState.lon.toFixed(3)})`
        : `Σημείο (${activeState.lat.toFixed(3)}, ${activeState.lon.toFixed(3)})`;
}

function scrollToSection(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function setGauge(circleId, valId, pct) {
    const c = document.getElementById(circleId);
    const v = document.getElementById(valId);
    const clamped = Math.max(0, Math.min(100, pct));
    if (c) c.style.strokeDashoffset = 213.6 - (clamped / 100) * 213.6;
    if (v) v.textContent = `${Math.round(clamped)}%`;
}

function animateValue(el, endVal, suffix = '', decimals = 1) {
    if (!el) return;
    const startVal = parseFloat(el.dataset.val || 0);
    el.dataset.val = endVal;
    const duration = 500, startTime = performance.now();
    function step(now) {
        const p = Math.min(1, (now - startTime) / duration);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = `${(startVal + (endVal - startVal) * eased).toFixed(decimals)}${suffix}`;
        if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function renderStepsList(elId, steps) {
    const el = document.getElementById(elId);
    if (!el || !Array.isArray(steps)) return;
    el.innerHTML = steps.map(s => `<li>${s}</li>`).join('');
}

function showTelemetryToast(msg) {
    const toast = document.getElementById('telemetry-toast');
    const text = document.getElementById('telemetry-toast-text');
    if (!toast || !text) return;
    text.textContent = msg;
    toast.classList.remove('hidden');
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => toast.classList.add('hidden'), 2200);
}

function toggleTheme() {
    document.getElementById('html-root').classList.toggle('dark');
    if (typeof refreshAllAnalysis === 'function') refreshAllAnalysis();
}

function applyStaticTranslations() {
    document.documentElement.lang = currentLang;
    document.querySelectorAll('[data-en][data-gr]').forEach(el => {
        el.textContent = el.getAttribute(`data-${currentLang}`);
    });
    document.querySelectorAll('[data-placeholder-en][data-placeholder-gr]').forEach(el => {
        el.placeholder = el.getAttribute(`data-placeholder-${currentLang}`);
    });
    document.title = currentLang === 'en'
        ? 'TerraPulse | The GPS for Agriculture'
        : 'TerraPulse | Το GPS της Γεωργίας';

    const langBtn = document.getElementById('lang-btn');
    if (langBtn) langBtn.textContent = currentLang === 'en' ? 'Ελληνικά' : 'English';
    const appBtn = document.getElementById('lang-btn-app');
    if (appBtn) appBtn.textContent = currentLang === 'en' ? 'GR' : 'EN';
    const suiteBtn = document.getElementById('lang-btn-suite');
    if (suiteBtn) suiteBtn.textContent = currentLang === 'en' ? 'ΕΛΛΗΝΙΚΑ' : 'ENGLISH';
}

function updateLocationHeaders() {
    const label = getActiveLabel();
    const str = (activeState.areaHa * 10).toFixed(1);
    const areaUnit = currentLang === 'en' ? 'str' : 'στρ';
    const targetWord = currentLang === 'en' ? 'Target' : 'Στόχος';
    const stremmaWord = currentLang === 'en' ? 'stremmata' : 'στρέμματα';

    document.getElementById('header-active-zone').textContent = label;
    document.getElementById('stat-zone').textContent = label;
    document.getElementById('stat-area').textContent = `${str} ${areaUnit}`;
    document.getElementById('suite-location-banner').textContent =
        `${targetWord}: ${label} • ${activeState.lat.toFixed(4)}, ${activeState.lon.toFixed(4)} • ${str} ${stremmaWord} (${activeState.areaHa.toFixed(2)} ha)`;
}

function toggleLang() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    currentLang = currentLang === 'en' ? 'gr' : 'en';
    applyStaticTranslations();
    updateLocationHeaders();
    if (typeof refreshAllAnalysis === 'function') refreshAllAnalysis();
}

/* ==================== WEB SPEECH API VOICE BRIEFING ==================== */
function speakCurrentBriefing() {
    if (!('speechSynthesis' in window)) return;
    if (isSpeaking) {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        return;
    }
    const tabMap = {
        drought: latestPayloads.water,
        soil: latestPayloads.soil,
        rotation: latestPayloads.rotation,
        disaster: latestPayloads.fire
    };
    const payload = tabMap[activeAnalysisTab] || latestPayloads.water;
    if (!payload) return;

    const text = `${payload.farmer_headline || ''}. ${payload.reasoning || ''}. ${(payload.action_steps || []).join('. ')}`;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = currentLang === 'en' ? 'en-US' : 'el-GR';
    utter.rate = 0.98;
    utter.onend = () => { isSpeaking = false; };
    isSpeaking = true;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
}