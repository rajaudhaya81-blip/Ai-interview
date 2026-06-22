// Global animated 3D/Particles Background - InterviewAI
// Hardware-accelerated canvas background utilizing Three.js

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('bg-canvas-container');
    if (!container) return;

    // Detect mobile/tablet to optimize performance
    const isMobile = window.innerWidth < 768;

    let scene, camera, renderer, particles, gridLines;
    let width = window.innerWidth;
    let height = window.innerHeight;

    function init() {
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x030712, 0.0015);

        camera = new THREE.PerspectiveCamera(60, width / height, 1, 1000);
        camera.position.z = 150;

        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: !isMobile });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // --- 1. Glowing Floating Particles (Starfield) ---
        const particleCount = isMobile ? 60 : 150;
        const particleGeometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 400; // X
            positions[i + 1] = (Math.random() - 0.5) * 400; // Y
            positions[i + 2] = (Math.random() - 0.5) * 400; // Z
        }

        particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        // Create canvas particle texture (soft glowing circle)
        const canvas = document.createElement('canvas');
        canvas.width = 16;
        canvas.height = 16;
        const ctx = canvas.getContext('2d');
        const grad = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
        grad.addColorStop(0, 'rgba(139, 92, 246, 1)'); // Violet center
        grad.addColorStop(0.5, 'rgba(59, 130, 246, 0.4)'); // Blue aura
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 16, 16);
        const texture = new THREE.CanvasTexture(canvas);

        const particleMaterial = new THREE.PointsMaterial({
            size: 3,
            map: texture,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        particles = new THREE.Points(particleGeometry, particleMaterial);
        scene.add(particles);

        // --- 2. Rotating Cybernetic Grid Mesh ---
        if (!isMobile) {
            const gridSize = 400;
            const gridDivisions = 20;
            const gridHelper = new THREE.GridHelper(gridSize, gridDivisions, 0x8b5cf6, 0x1f2937);
            gridHelper.position.y = -80;
            gridHelper.rotation.x = Math.PI / 6;
            
            // Adjust materials to be transparent and glowing
            gridHelper.material.transparent = true;
            gridHelper.material.opacity = 0.12;
            scene.add(gridHelper);
            gridLines = gridHelper;
        }

        animate();
    }

    let lastTime = 0;
    function animate(time) {
        requestAnimationFrame(animate);

        // Slow rotations
        if (particles) {
            particles.rotation.y += 0.0004;
            particles.rotation.x += 0.0002;
        }

        if (gridLines) {
            gridLines.rotation.z += 0.0003;
        }

        renderer.render(scene, camera);
    }

    // Window resizing handler
    window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    });

    init();
});
