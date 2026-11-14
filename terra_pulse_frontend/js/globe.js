let scene, camera, renderer, globeMesh, orbitRing, orbitRing2, satDot, starField;
let isGlobeActive = true;
let satAngle = 0;

function initGlobe() {
    const container = document.getElementById('globe-container');
    if (!container || container.childElementCount > 0) return;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 2.8;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 2.0));
    const dl = new THREE.DirectionalLight(0xffffff, 1.8);
    dl.position.set(5, 3, 5);
    scene.add(dl);

    const tl = new THREE.TextureLoader();
    globeMesh = new THREE.Mesh(
        new THREE.SphereGeometry(1, 64, 64),
        new THREE.MeshStandardMaterial({
            map: tl.load('https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_atmos_2048.jpg'),
            bumpMap: tl.load('https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_normal_2048.jpg'),
            bumpScale: 0.05, roughness: 0.7, metalness: 0.1
        })
    );
    scene.add(globeMesh);

    orbitRing = new THREE.Mesh(
        new THREE.RingGeometry(1.22, 1.23, 96),
        new THREE.MeshBasicMaterial({ color: 0x22C55E, side: THREE.DoubleSide, transparent: true, opacity: 0.32 })
    );
    orbitRing.rotation.x = Math.PI / 2.6;
    orbitRing.rotation.y = 0.3;
    scene.add(orbitRing);

    orbitRing2 = new THREE.Mesh(
        new THREE.RingGeometry(1.30, 1.306, 96),
        new THREE.MeshBasicMaterial({ color: 0x06B6D4, side: THREE.DoubleSide, transparent: true, opacity: 0.22 })
    );
    orbitRing2.rotation.x = -Math.PI / 3.1;
    orbitRing2.rotation.y = -0.4;
    scene.add(orbitRing2);

    satDot = new THREE.Mesh(
        new THREE.SphereGeometry(0.025, 12, 12),
        new THREE.MeshBasicMaterial({ color: 0x22C55E })
    );
    scene.add(satDot);

    const starGeo = new THREE.BufferGeometry();
    const starPos = [];
    for (let i = 0; i < 320; i++) {
        starPos.push((Math.random() - 0.5) * 24, (Math.random() - 0.5) * 24, (Math.random() - 0.5) * 24 - 4);
    }
    starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
    starField = new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0x94a3b8, size: 0.03, transparent: true, opacity: 0.55 }));
    scene.add(starField);

    let isDragging = false, prevMouseX = 0;
    container.addEventListener('mousedown', (e) => { isDragging = true; prevMouseX = e.clientX; });
    window.addEventListener('mousemove', (e) => {
        if (isDragging && isGlobeActive) {
            globeMesh.rotation.y += (e.clientX - prevMouseX) * 0.005;
            prevMouseX = e.clientX;
        }
    });
    window.addEventListener('mouseup', () => { isDragging = false; });

    window.addEventListener('resize', () => {
        if (!renderer || !camera) return;
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    animateGlobe();
}

function animateGlobe() {
    if (!isGlobeActive) return;
    requestAnimationFrame(animateGlobe);
    satAngle += 0.012;
    if (globeMesh) globeMesh.rotation.y += 0.0013;
    if (orbitRing) orbitRing.rotation.z += 0.002;
    if (orbitRing2) orbitRing2.rotation.z -= 0.0015;
    if (starField) starField.rotation.y += 0.0003;
    if (satDot) {
        satDot.position.set(Math.cos(satAngle) * 1.225, Math.sin(satAngle) * 0.45, Math.sin(satAngle) * 1.15);
    }
    renderer.render(scene, camera);
}