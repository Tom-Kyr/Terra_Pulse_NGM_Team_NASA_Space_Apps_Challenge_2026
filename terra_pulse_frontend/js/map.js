window.mapInstance = null;
let markerInstance = null, currentTileLayer = null, drawnItems = null, vraLayerGroup = null;

const mapLayers = {
    dark: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png?api_key=995eddc8-a9c9-4d38-b10a-bdd7665c1ffe',
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ndvi: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'
};

const radarIcon = L.divIcon({
    className: 'radar-marker',
    html: '<div class="ring"></div><div class="dot"></div>',
    iconSize: [18, 18],
    iconAnchor: [9, 9]
});

function calcPolygonAreaHa(latlngs) {
    return (L.GeometryUtil && L.GeometryUtil.geodesicArea)
        ? Math.max(0.2, L.GeometryUtil.geodesicArea(latlngs) / 10000)
        : 4.5;
}

function drawVraGridOnMap(gridData) {
    if (!window.mapInstance || !vraLayerGroup || !Array.isArray(gridData)) return;
    vraLayerGroup.clearLayers();
    const cellDeg = Math.max(0.0012, Math.sqrt(activeState.areaHa) * 0.00075);

    gridData.forEach(cell => {
        const cLat = activeState.lat + cell.dr * cellDeg;
        const cLon = activeState.lon + cell.dc * cellDeg;
        const bounds = [[cLat - cellDeg / 2, cLon - cellDeg / 2], [cLat + cellDeg / 2, cLon + cellDeg / 2]];
        const col = cell.stress > 65 ? '#EF4444' : (cell.stress > 45 ? '#F59E0B' : '#22C55E');
        const rect = L.rectangle(bounds, { color: col, weight: 1, fillColor: col, fillOpacity: 0.24 });
        rect.bindPopup(`<b>VRA ${cell.zone}</b><br>Moisture: ${cell.moisture}%<br>Stress: ${cell.stress}%<br>Dose Adj: <b>${cell.dose_adj}</b>`);
        rect.on('click', (ev) => { L.DomEvent.stopPropagation(ev); rect.openPopup(); });
        rect.addTo(vraLayerGroup);
    });
}

function initMap() {
    if (window.mapInstance) { window.mapInstance.invalidateSize(); return; }

    window.mapInstance = L.map('map', {
        zoomControl: false,
        wheelDebounceTime: 60,
        wheelPxPerZoomLevel: 90,
        zoomSnap: 0.5
    }).setView([activeState.lat, activeState.lon], 11);

    currentTileLayer = L.tileLayer(mapLayers.dark, { maxZoom: 20 }).addTo(window.mapInstance);
    L.control.zoom({ position: 'topleft' }).addTo(window.mapInstance);

    vraLayerGroup = new L.LayerGroup().addTo(window.mapInstance);
    drawnItems = new L.FeatureGroup();
    window.mapInstance.addLayer(drawnItems);

    if (L.Control.Draw) {
        window.mapInstance.addControl(new L.Control.Draw({
            position: 'topleft',
            edit: { featureGroup: drawnItems },
            draw: { polygon: true, rectangle: true, circle: false, marker: false, polyline: false, circlemarker: false }
        }));

        window.mapInstance.on('draw:drawstart draw:editstart draw:deletestart', () => { isDrawingOrEditing = true; });
        window.mapInstance.on('draw:drawstop draw:editstop draw:deletestop', () => {
            setTimeout(() => { isDrawingOrEditing = false; }, 120);
        });

        window.mapInstance.on(L.Draw.Event.CREATED, (e) => {
            const layer = e.layer;
            layer.setStyle({ color: '#22C55E', fillColor: '#22C55E', fillOpacity: 0.14, weight: 2.5 });
            drawnItems.addLayer(layer);

            const latlngs = layer.getLatLngs()[0] || [];
            const center = layer.getBounds().getCenter();
            const areaHa = calcPolygonAreaHa(latlngs);

            activeState.polygonLatLngs = latlngs;
            activeState.isCustom = true;
            selectLocation(center.lat, center.lng, areaHa, false);

            layer.bindPopup(`<b>${getActiveLabel()}</b><br>${center.lat.toFixed(4)}, ${center.lng.toFixed(4)}`);
            layer.on('click', (ev) => {
                L.DomEvent.stopPropagation(ev);
                activeState.polygonLatLngs = latlngs;
                activeState.isCustom = true;
                selectLocation(center.lat, center.lng, areaHa, false);
            });
        });
    }

    markerInstance = L.marker([activeState.lat, activeState.lon], { icon: radarIcon })
        .addTo(window.mapInstance)
        .bindPopup(getActiveLabel());

    window.mapInstance.on('click', (e) => {
        if (isDrawingOrEditing) return;
        activeState.polygonLatLngs = null;
        activeState.isCustom = true;
        selectLocation(e.latlng.lat, e.latlng.lng, activeState.areaHa, false);
    });

    setTimeout(() => window.mapInstance.invalidateSize(), 200);
}

function setMapLayer(layerKey) {
    if (!window.mapInstance || !mapLayers[layerKey]) return;
    if (currentTileLayer) window.mapInstance.removeLayer(currentTileLayer);
    currentTileLayer = L.tileLayer(mapLayers[layerKey], { maxZoom: 20 }).addTo(window.mapInstance);

    ['dark', 'satellite', 'ndvi'].forEach(k => {
        const btn = document.getElementById(`layer-btn-${k}`);
        if (btn) {
            btn.className = k === layerKey
                ? 'px-3 py-1.5 rounded-lg bg-[#22C55E] text-[#050811] font-bold transition'
                : 'px-3 py-1.5 rounded-lg bg-transparent transition';
        }
    });
}

function selectPreset(lat, lng, nameEn, nameGr, areaHa) {
    activeState.polygonLatLngs = null;
    activeState.isCustom = false;
    activeState.nameEn = nameEn;
    activeState.nameGr = nameGr;
    selectLocation(lat, lng, areaHa, true);
}

function selectLocation(lat, lng, areaHa = 4.5, shouldZoom = false) {
    activeState.lat = lat;
    activeState.lon = lng;
    activeState.areaHa = areaHa;
    const label = getActiveLabel();

    if (window.mapInstance) {
        if (shouldZoom) window.mapInstance.flyTo([lat, lng], 12, { duration: 0.85 });
        else window.mapInstance.panTo([lat, lng], { animate: true });
        if (markerInstance) markerInstance.setLatLng([lat, lng]).bindPopup(`<b>${label}</b>`).openPopup();
    }

    updateLocationHeaders();
    showTelemetryToast(currentLang === 'en' ? `Syncing live weather & AI for ${label}...` : `Φόρτωση ζωντανού καιρού & AI για ${label}...`);
    refreshAllAnalysis();
}

async function handleMapSearch(event) {
    if (event.key !== 'Enter') return;
    const query = event.target.value.trim();
    if (!query) return;
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const results = await res.json();
        if (results && results.length > 0) {
            const place = results[0].display_name.split(',')[0];
            selectPreset(parseFloat(results[0].lat), parseFloat(results[0].lon), place, place, 4.5);
        }
    } catch (err) {
        console.error("Search error:", err);
    }
}