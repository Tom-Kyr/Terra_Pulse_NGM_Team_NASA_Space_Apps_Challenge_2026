let isSidebarOpen = false;

function launchAppOS() {
    isGlobeActive = false;
    document.getElementById('globe-container').style.display = 'none';
    switchView('app');
}

function switchView(viewName) {
    document.getElementById('view-landing').classList.add('hidden');
    document.getElementById('view-app').classList.add('hidden');
    if (viewName === 'landing') {
        isGlobeActive = true;
        document.getElementById('globe-container').style.display = 'block';
        document.getElementById('view-landing').classList.remove('hidden');
        animateGlobe();
    } else {
        document.getElementById('view-app').classList.remove('hidden');
        setTimeout(() => {
            if (!window.mapInstance) initMap();
            else window.mapInstance.invalidateSize();
        }, 100);
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    isSidebarOpen = !isSidebarOpen;
    sidebar.style.transform = isSidebarOpen ? 'translateX(0)' : 'translateX(-100%)';
    sidebar.style.width = isSidebarOpen ? '410px' : '0px';
    sidebar.style.opacity = isSidebarOpen ? '1' : '0';
    setTimeout(() => {
        if (window.mapInstance) window.mapInstance.invalidateSize();
    }, 450);
}

function openDedicatedAnalysisTab() {
    document.getElementById('view-analysis-tab').classList.remove('hidden');
    setTimeout(() => syncMiniMaps(), 80);
}

function closeDedicatedAnalysisTab() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    isSpeaking = false;
    document.getElementById('view-analysis-tab').classList.add('hidden');
}

function switchAnalysisTab(tabName) {
    activeAnalysisTab = tabName;
    ['drought', 'soil', 'rotation', 'disaster', 'compare'].forEach(t => {
        const panel = document.getElementById(`analysis-tab-${t}`);
        const btn = document.getElementById(`btn-tab-${t}`);
        if (panel) panel.classList.add('hidden');
        if (btn) btn.className = 'px-4 py-2.5 rounded-xl inner-box font-semibold text-xs font-mono uppercase transition cursor-pointer';
    });

    const activePanel = document.getElementById(`analysis-tab-${tabName}`);
    if (activePanel) {
        activePanel.classList.remove('hidden');
        activePanel.classList.remove('animate-fade-in');
        void activePanel.offsetWidth;
        activePanel.classList.add('animate-fade-in');
    }

    const activeBtn = document.getElementById(`btn-tab-${tabName}`);
    if (activeBtn) {
        activeBtn.className = 'px-4 py-2.5 rounded-xl bg-[#22C55E] text-[#050811] font-bold text-xs font-mono uppercase transition cursor-pointer shadow-lg glow-green-sm';
    }

    if (tabName === 'compare') renderComparisonTab();
    setTimeout(() => syncMiniMaps(), 80);
}

window.addEventListener('DOMContentLoaded', () => {
    applyStaticTranslations();
    updateLocationHeaders();
    initGlobe();
    refreshAllAnalysis();
});