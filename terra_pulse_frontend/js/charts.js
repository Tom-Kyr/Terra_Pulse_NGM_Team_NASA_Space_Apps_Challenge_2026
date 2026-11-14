const charts = {};
const miniMaps = {};

const chartAnim = { duration: 850, easing: 'easeOutQuart' };
const darkTooltip = {
    backgroundColor: 'rgba(5, 8, 17, 0.94)',
    borderColor: '#22C55E',
    borderWidth: 1,
    titleFont: { family: 'JetBrains Mono' },
    bodyFont: { family: 'Bai Jamjuree' }
};

function isDark() { return document.getElementById('html-root').classList.contains('dark'); }
function chartTickColor() { return isDark() ? '#cbd5e1' : '#334155'; }
function chartGridColor() { return isDark() ? 'rgba(148,163,184,0.08)' : 'rgba(15,23,42,0.08)'; }

function getBaseScales() {
    return {
        x: { ticks: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } }, grid: { color: chartGridColor() } },
        y: { ticks: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } }, grid: { color: chartGridColor() } }
    };
}

function makeGrad(ctx, colorTop, colorBottom) {
    const g = ctx.createLinearGradient(0, 0, 0, 240);
    g.addColorStop(0, colorTop);
    g.addColorStop(1, colorBottom);
    return g;
}

function renderOrUpdateChart(id, builderFn) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    if (charts[id]) charts[id].destroy();
    const ctx = canvas.getContext('2d');
    charts[id] = new Chart(ctx, builderFn(ctx));
}

function ensureMiniMap(id, tileUrl, overlayColor, secondaryColor = null) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!miniMaps[id]) {
        const m = L.map(id, { zoomControl: false, attributionControl: false }).setView([activeState.lat, activeState.lon], 13);
        L.tileLayer(tileUrl, { maxZoom: 19 }).addTo(m);
        const outer = L.circle([activeState.lat, activeState.lon], {
            radius: 420, color: overlayColor, fillColor: overlayColor, fillOpacity: 0.18, weight: 1.5, dashArray: '4 4'
        }).addTo(m);
        const inner = L.circle([activeState.lat, activeState.lon], {
            radius: 190, color: secondaryColor || overlayColor, fillColor: secondaryColor || overlayColor, fillOpacity: 0.32, weight: 2
        }).addTo(m);
        const polyLayer = L.layerGroup().addTo(m);
        miniMaps[id] = { map: m, outer, inner, polyLayer };
    }

    const mm = miniMaps[id];
    mm.map.invalidateSize();
    const r = Math.max(220, Math.sqrt(activeState.areaHa * 10000) * 0.9);
    mm.outer.setLatLng([activeState.lat, activeState.lon]).setRadius(r * 1.4);
    mm.inner.setLatLng([activeState.lat, activeState.lon]).setRadius(r * 0.75);
    mm.polyLayer.clearLayers();

    if (activeState.polygonLatLngs && activeState.polygonLatLngs.length > 2) {
        const p = L.polygon(activeState.polygonLatLngs, { color: overlayColor, fillOpacity: 0.35, weight: 2.5 }).addTo(mm.polyLayer);
        mm.map.fitBounds(p.getBounds(), { padding: [20, 20] });
    } else {
        mm.map.setView([activeState.lat, activeState.lon], 13);
    }
}

function syncMiniMaps() {
    if (activeAnalysisTab === 'drought') ensureMiniMap('mini-map-drought', mapLayers.dark, '#06B6D4', '#22C55E');
    else if (activeAnalysisTab === 'soil') ensureMiniMap('mini-map-soil', mapLayers.satellite, '#22C55E', '#10B981');
    else if (activeAnalysisTab === 'rotation') ensureMiniMap('mini-map-rotation', mapLayers.satellite, '#A855F7', '#22C55E');
    else if (activeAnalysisTab === 'disaster') ensureMiniMap('mini-map-disaster', mapLayers.ndvi, '#F59E0B', '#EF4444');
}