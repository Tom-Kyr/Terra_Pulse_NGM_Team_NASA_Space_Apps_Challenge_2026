function onSimulatorChange() {
    simState.crop = document.getElementById('sim-crop').value;
    simState.irrigation = document.getElementById('sim-irrigation').value;
    simState.scenario = document.getElementById('sim-scenario').value;
    refreshAllAnalysis();
}

function saveFieldSlot(slot) {
    const w = latestPayloads.water, s = latestPayloads.soil, f = latestPayloads.fire;
    fieldSlots[slot] = {
        name: getActiveLabel(),
        stress: w ? Math.round(w.metrics.average_water_stress * 100) : 55,
        soil: s ? Math.round(s.metrics.health_pct) : 65,
        fire: f ? Math.round(f.metrics.erosion_pct) : 40,
        eur: w ? Math.round(w.metrics.total_saved_eur) : 1200,
    };
    renderComparisonTab();
    showTelemetryToast(currentLang === 'en' ? `Saved as Field ${slot}!` : `Αποθηκεύτηκε ως Αγρός ${slot}!`);
}

function renderComparisonTab() {
    const a = fieldSlots.A, b = fieldSlots.B;
    document.getElementById('cmp-a-name').textContent = a.name;
    document.getElementById('cmp-a-stress').textContent = `${a.stress}%`;
    document.getElementById('cmp-a-soil').textContent = `${a.soil}%`;
    document.getElementById('cmp-a-fire').textContent = `${a.fire}%`;
    document.getElementById('cmp-a-eur').textContent = `${a.eur} €`;

    document.getElementById('cmp-b-name').textContent = b.name;
    document.getElementById('cmp-b-stress').textContent = `${b.stress}%`;
    document.getElementById('cmp-b-soil').textContent = `${b.soil}%`;
    document.getElementById('cmp-b-fire').textContent = `${b.fire}%`;
    document.getElementById('cmp-b-eur').textContent = `${b.eur} €`;

    renderOrUpdateChart('chart-compare-fields', () => ({
        type: 'bar',
        data: {
            labels: currentLang === 'en'
                ? ['Water Stress (%)', 'Soil Health (%)', 'Erosion Risk (%)', 'Savings (€ / 10)']
                : ['Υδατικό Στρες (%)', 'Υγεία Εδάφους (%)', 'Κίνδυνος Διάβρωσης (%)', 'Ετήσιο Όφελος (€ / 10)'],
            datasets: [
                { label: `${currentLang === 'en' ? 'Field A' : 'Αγρός Α'}: ${a.name}`, data: [a.stress, a.soil, a.fire, Math.round(a.eur / 10)], backgroundColor: '#06B6D4', borderRadius: 8 },
                { label: `${currentLang === 'en' ? 'Field B' : 'Αγρός Β'}: ${b.name}`, data: [b.stress, b.soil, b.fire, Math.round(b.eur / 10)], backgroundColor: '#A855F7', borderRadius: 8 }
            ]
        },
        options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 11 } } } }, scales: getBaseScales() }
    }));
}

async function fetchWaterAnalysis(qs) {
    try {
        const res = await fetch(`${API_BASE}/api/water-analysis?${qs}`);
        const data = await res.json();
        if (!data.metrics) return;
        latestPayloads.water = data;
        const m = data.metrics, c = data.charts;

        document.getElementById('stat-moisture').textContent = `${(m.min_root_moisture * 100).toFixed(1)}%`;
        document.getElementById('stat-water').textContent = `${m.water_need_m3_stremma} m³ / ${currentLang === 'en' ? 'str' : 'στρ'}`;
        document.getElementById('stat-action').textContent = m.prescription;
        document.getElementById('sidebar-data-source').textContent = data.data_source || 'LIVE HUD';
        document.getElementById('map-live-badge').textContent = `${data.data_source} • 4x AI`;
        document.getElementById('strip-source').textContent = data.data_source || 'LIVE';

        if (data.vra_grid) drawVraGridOnMap(data.vra_grid);

        animateValue(document.getElementById('strip-area'), data.location.stremmata, currentLang === 'en' ? ' str' : ' στρ', 1);
        document.getElementById('strip-soil-type').textContent = data.location.soil_type;
        animateValue(document.getElementById('strip-canopy'), m.canopy_temp_c, '°C', 1);
        animateValue(document.getElementById('strip-et0'), m.et0_avg, ' mm', 1);
        animateValue(document.getElementById('strip-elev'), data.location.elevation_m, ' m', 0);
        animateValue(document.getElementById('strip-eur'), m.total_saved_eur, ' €', 0);

        setGauge('gauge-water-circle', 'gauge-water-val', m.average_water_stress * 100);
        document.getElementById('water-headline').textContent = data.farmer_headline || '';
        document.getElementById('water-reasoning').textContent = data.reasoning || '';
        renderStepsList('water-steps', data.action_steps);

        animateValue(document.getElementById('ui-min-moisture'), m.min_root_moisture * 100, '%', 1);
        animateValue(document.getElementById('ui-avg-stress'), m.average_water_stress * 100, '%', 1);
        animateValue(document.getElementById('ui-water-pct-saved'), m.water_saved_pct, '%', 1);
        document.getElementById('ui-deficit-mm').textContent = currentLang === 'en' ? `6-mo deficit: ${m.water_deficit_mm} mm` : `Έλλειμμα 6μήνου: ${m.water_deficit_mm} mm`;
        animateValue(document.getElementById('ui-water-saved'), m.total_water_m3, ' m³', 0);
        document.getElementById('ui-water-per-stremma').textContent = `${m.water_need_m3_stremma} m³ / ${currentLang === 'en' ? 'str' : 'στρ'} (${m.water_saved_pct}% ${currentLang === 'en' ? 'saved' : 'εξοικ.'})`;
        document.getElementById('ui-risk-badge').textContent = m.risk_label;
        document.getElementById('ui-model-mode').textContent = m.model_mode;
        document.getElementById('ai-conclusion-box').textContent = data.conclusions || '';

        const schedEl = document.getElementById('weekly-schedule-list');
        if (schedEl && data.weekly_schedule) {
            schedEl.innerHTML = data.weekly_schedule.map(item => `
                <div class="flex items-center justify-between px-3 py-1.5 rounded-xl inner-box ${item.active ? 'border-[#22C55E]/40' : ''}">
                    <div class="flex items-center space-x-2.5">
                        <span class="w-2 h-2 rounded-full ${item.active ? 'bg-[#22C55E]' : (item.rain_mm >= 4 ? 'bg-cyan-400' : 'bg-slate-500')}"></span>
                        <span class="font-bold w-11">${item.day}</span>
                        <span class="${item.active ? '' : 'text-slate-400'}">${item.action}</span>
                    </div>
                    <span class="font-bold ${item.active ? 'text-cyan-400' : 'text-slate-400'}">${item.mm} mm</span>
                </div>
            `).join('');
        }

        renderOrUpdateChart('chart-drought-timeseries', (ctx) => ({
            type: 'line',
            data: {
                labels: c.months,
                datasets: [
                    { label: currentLang === 'en' ? 'Water Stress (%)' : 'Υδατικό Στρες (%)', data: c.stress_series, borderColor: '#F59E0B', backgroundColor: makeGrad(ctx, 'rgba(245,158,11,0.34)', 'rgba(245,158,11,0.0)'), fill: true, tension: 0.4, pointRadius: 4 },
                    { label: currentLang === 'en' ? 'Soil Moisture (%)' : 'Υγρασία Εδάφους (%)', data: c.moisture_series, borderColor: '#22C55E', backgroundColor: makeGrad(ctx, 'rgba(34,197,94,0.32)', 'rgba(34,197,94,0.0)'), fill: true, tension: 0.4, pointRadius: 4 },
                    { label: currentLang === 'en' ? 'Rainfall (mm)' : 'Βροχόπτωση (mm)', data: c.precip_series, borderColor: '#06B6D4', borderDash: [5, 5], tension: 0.4, pointRadius: 3 }
                ]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } } } }, scales: getBaseScales() }
        }));

        renderOrUpdateChart('chart-water-benchmark', () => ({
            type: 'bar',
            data: {
                labels: c.benchmark.labels,
                datasets: [
                    { label: currentLang === 'en' ? 'Your Field' : 'Το Χωράφι σας', data: c.benchmark.field, backgroundColor: '#22C55E', borderRadius: 6 },
                    { label: currentLang === 'en' ? 'Regional Avg' : 'Μ.Ο. Περιφέρειας', data: c.benchmark.regional_avg, backgroundColor: '#64748B', borderRadius: 6 },
                    { label: currentLang === 'en' ? 'Optimal' : 'Βέλτιστο', data: c.benchmark.optimal, backgroundColor: 'rgba(6,182,212,0.55)', borderRadius: 6 }
                ]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 9 } } } }, scales: getBaseScales() }
        }));

        renderOrUpdateChart('chart-cost-comparison', () => ({
            type: 'bar',
            data: {
                labels: c.cost_comparison.labels,
                datasets: [
                    { label: currentLang === 'en' ? 'Current Setup' : 'Τρέχων Τρόπος', data: c.cost_comparison.traditional, backgroundColor: '#EF4444', borderRadius: 6 },
                    { label: 'TerraPulse AI', data: c.cost_comparison.terrapulse, backgroundColor: '#22C55E', borderRadius: 6 }
                ]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } } } }, scales: getBaseScales() }
        }));
    } catch (err) { console.error("Water API error:", err); }
}

async function fetchSoilAnalysis(qs) {
    try {
        const res = await fetch(`${API_BASE}/api/soil-analysis?${qs}`);
        const data = await res.json();
        if (!data.metrics) return;
        latestPayloads.soil = data;
        const m = data.metrics, c = data.charts;

        document.getElementById('stat-soil-health').textContent = `${m.health_pct}% (${m.health_proxy})`;
        setGauge('gauge-soil-circle', 'gauge-soil-val', m.health_pct);
        document.getElementById('soil-headline').textContent = data.farmer_headline || '';
        document.getElementById('soil-reasoning').textContent = data.reasoning || '';
        renderStepsList('soil-steps', data.action_steps);

        animateValue(document.getElementById('ui-soil-health-proxy'), m.health_pct, '%', 1);
        document.getElementById('ui-soil-health-raw').textContent = `health_proxy = ${m.health_proxy} (0–1)`;
        animateValue(document.getElementById('ui-soil-erosion-proxy'), m.erosion_pct, '%', 1);
        document.getElementById('ui-soil-erosion-raw').textContent = `erosion_proxy = ${m.erosion_proxy} (0–1)`;
        document.getElementById('ui-soil-om').textContent = `${m.soil_om_pct}%`;
        document.getElementById('ui-soil-ndvi').textContent = m.ndvi_avg;
        animateValue(document.getElementById('ui-soil-fert-eur'), m.fert_saved_eur, ' €', 0);
        document.getElementById('ui-soil-mode').textContent = m.model_mode;
        document.getElementById('ui-soil-summary-gr').textContent = data.conclusions || '';

        renderOrUpdateChart('chart-soil-radar', () => ({
            type: 'radar',
            data: {
                labels: currentLang === 'en' ? ['NDVI', 'Organic C', 'Water Retention', 'Anti-Erosion', 'health_proxy'] : ['NDVI', 'Οργανικός Άνθρακας', 'Συγκράτηση Νερού', 'Αντοχή Διάβρωσης', 'health_proxy'],
                datasets: [{ label: getActiveLabel(), data: c.soil_radar, borderColor: '#22C55E', backgroundColor: 'rgba(34,197,94,0.22)', pointBackgroundColor: '#22C55E' }]
            },
            options: {
                animation: chartAnim, responsive: true, maintainAspectRatio: false,
                scales: { r: { min: 0, max: 100, ticks: { display: false }, grid: { color: chartGridColor() }, angleLines: { color: chartGridColor() }, pointLabels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } } } },
                plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor() } } }
            }
        }));

        renderOrUpdateChart('chart-soil-npk', () => ({
            type: 'bar',
            data: {
                labels: c.npk_labels,
                datasets: [
                    { label: currentLang === 'en' ? 'Current (%)' : 'Τρέχον (%)', data: c.npk_current, backgroundColor: '#06B6D4', borderRadius: 6 },
                    { label: currentLang === 'en' ? 'Target (%)' : 'Στόχος (%)', data: c.npk_target, backgroundColor: 'rgba(34,197,94,0.45)', borderRadius: 6 }
                ]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } } } }, scales: getBaseScales() }
        }));

        renderOrUpdateChart('chart-soil-trend', (ctx) => ({
            type: 'line',
            data: {
                labels: c.months,
                datasets: [
                    { label: 'health_proxy (%)', data: c.health_trend, borderColor: '#22C55E', backgroundColor: makeGrad(ctx, 'rgba(34,197,94,0.28)', 'rgba(34,197,94,0.0)'), fill: true, tension: 0.35 },
                    { label: 'erosion_proxy (%)', data: c.erosion_trend, borderColor: '#F59E0B', backgroundColor: makeGrad(ctx, 'rgba(245,158,11,0.24)', 'rgba(245,158,11,0.0)'), fill: true, tension: 0.35 }
                ]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 11 } } } }, scales: getBaseScales() }
        }));
    } catch (err) { console.error("Soil API error:", err); }
}

async function fetchRotationAnalysis(qs) {
    try {
        const res = await fetch(`${API_BASE}/api/rotation-analysis?${qs}`);
        const data = await res.json();
        if (!data.metrics) return;
        latestPayloads.rotation = data;
        const m = data.metrics;

        setGauge('gauge-rotation-circle', 'gauge-rotation-val', m.average_suitability * 100);
        document.getElementById('rotation-headline').textContent = data.farmer_headline || '';
        document.getElementById('rotation-reasoning').textContent = data.reasoning || '';
        renderStepsList('rotation-steps', data.action_steps);

        animateValue(document.getElementById('ui-rotation-suitability'), m.average_suitability, '', 2);
        document.getElementById('ui-rotation-best-crop').textContent = m.best_crop;
        animateValue(document.getElementById('ui-rotation-nfix'), m.n_fixation_kg_ha, ' kg/ha', 1);
        document.getElementById('ai-rotation-conclusion-box').textContent = data.conclusions || '';

        renderOrUpdateChart('chart-rotation-crops', () => ({
            type: 'bar',
            data: {
                labels: Object.keys(m.crop_scores),
                datasets: [{ label: currentLang === 'en' ? 'Suitability (%)' : 'Καταλληλότητα (%)', data: Object.values(m.crop_scores), backgroundColor: ['#22C55E', '#06B6D4', '#A855F7', '#F59E0B'], borderRadius: 8 }]
            },
            options: { animation: chartAnim, indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { display: false } }, scales: getBaseScales() }
        }));

        renderOrUpdateChart('chart-rotation-timeline', (ctx) => ({
            type: 'line',
            data: {
                labels: m.timeline_labels,
                datasets: [{ label: currentLang === 'en' ? 'Available Soil N (kg/ha)' : 'Διαθέσιμο Άζωτο (kg/ha)', data: m.nitrogen_timeline, borderColor: '#06B6D4', backgroundColor: makeGrad(ctx, 'rgba(6,182,212,0.3)', 'rgba(6,182,212,0.0)'), fill: true, tension: 0.35 }]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } } } }, scales: getBaseScales() }
        }));

        renderOrUpdateChart('chart-rotation-roi', () => ({
            type: 'bar',
            data: {
                labels: m.roi_comparison.labels,
                datasets: [
                    { label: currentLang === 'en' ? 'Monoculture' : 'Μονοκαλλιέργεια', data: m.roi_comparison.monoculture, backgroundColor: '#64748B', borderRadius: 6 },
                    { label: currentLang === 'en' ? 'AI Rotation' : 'Αμειψισπορά AI', data: m.roi_comparison.ai_rotation, backgroundColor: '#22C55E', borderRadius: 6 }
                ]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } } } }, scales: getBaseScales() }
        }));
    } catch (err) { console.error("Rotation API error:", err); }
}

async function fetchFireAnalysis(qs) {
    try {
        const res = await fetch(`${API_BASE}/api/fire-analysis?${qs}`);
        const data = await res.json();
        if (!data.metrics) return;
        latestPayloads.fire = data;
        const m = data.metrics, c = data.charts;

        setGauge('gauge-fire-circle', 'gauge-fire-val', m.erosion_pct);
        document.getElementById('fire-headline').textContent = data.farmer_headline || '';
        document.getElementById('fire-reasoning').textContent = data.reasoning || '';
        document.getElementById('fire-sms-preview').textContent = data.sms_alert || '';
        renderStepsList('fire-steps', data.action_steps);

        animateValue(document.getElementById('ui-fire-erosion'), m.erosion_pct, '%', 1);
        document.getElementById('ui-fire-erosion-raw').textContent = `erosion_risk = ${m.erosion_risk} (0–1)`;
        animateValue(document.getElementById('ui-fire-recovery'), m.recovery_pct, '%', 1);
        document.getElementById('ui-fire-recovery-raw').textContent = `recovery_score = ${m.recovery_score} (0–1)`;
        animateValue(document.getElementById('ui-disaster-slope'), m.slope_deg, '°', 1);
        document.getElementById('ui-fire-mode').textContent = m.model_mode;
        document.getElementById('ui-fire-summary-gr').textContent = data.conclusions || '';

        renderOrUpdateChart('chart-disaster-runoff', () => ({
            type: 'bar',
            data: {
                labels: c.runoff_labels,
                datasets: [{ label: currentLang === 'en' ? 'Topsoil Loss (%)' : 'Απώλεια Εδάφους (%)', data: c.runoff_values, backgroundColor: ['#EF4444', '#F59E0B', '#22C55E'], borderRadius: 8 }]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { display: false } }, scales: getBaseScales() }
        }));

        renderOrUpdateChart('chart-fire-rebound', (ctx) => ({
            type: 'line',
            data: {
                labels: c.rebound_months,
                datasets: [
                    { label: currentLang === 'en' ? 'Natural Rebound (%)' : 'Φυσική Αναβλάστηση (%)', data: c.rebound_natural, borderColor: '#F59E0B', borderDash: [5, 5], tension: 0.35 },
                    { label: currentLang === 'en' ? 'With 72h Seeding (%)' : 'Με Ταχεία Σπορά 72h (%)', data: c.rebound_seeded, borderColor: '#22C55E', backgroundColor: makeGrad(ctx, 'rgba(34,197,94,0.28)', 'rgba(34,197,94,0.0)'), fill: true, tension: 0.35 }
                ]
            },
            options: { animation: chartAnim, responsive: true, maintainAspectRatio: false, plugins: { tooltip: darkTooltip, legend: { labels: { color: chartTickColor(), font: { family: 'JetBrains Mono', size: 10 } } } }, scales: getBaseScales() }
        }));
    } catch (err) { console.error("Fire API error:", err); }
}

async function refreshAllAnalysis() {
    const loadingBar = document.getElementById('analysis-loading-bar');
    if (loadingBar) loadingBar.classList.remove('hidden');

    const qs = new URLSearchParams({
        lat: activeState.lat,
        lon: activeState.lon,
        area_ha: activeState.areaHa,
        name: getActiveLabel(),
        lang: currentLang,
        crop: simState.crop,
        irrigation: simState.irrigation,
        scenario: simState.scenario
    }).toString();

    await Promise.all([
        fetchWaterAnalysis(qs),
        fetchSoilAnalysis(qs),
        fetchRotationAnalysis(qs),
        fetchFireAnalysis(qs)
    ]);

    if (activeAnalysisTab === 'compare') renderComparisonTab();
    syncMiniMaps();
    if (loadingBar) setTimeout(() => loadingBar.classList.add('hidden'), 300);
}