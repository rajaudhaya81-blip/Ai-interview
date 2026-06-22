// Sci-Fi Synthesized UI Sound Effects using Web Audio API
// Morphed, low-volume, non-obtrusive micro-sounds for premium feel.

let audioCtx = null;

function initAudioContext() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

const playSFX = (type) => {
    try {
        initAudioContext();
        if (!audioCtx) return;

        const now = audioCtx.currentTime;
        const masterVolume = audioCtx.createGain();
        masterVolume.gain.setValueAtTime(0.04, now); // Set overall volume low (4%)
        masterVolume.connect(audioCtx.destination);

        switch (type) {
            case 'hover': {
                // High-pitched soft sci-fi tick
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(1200, now);
                osc.frequency.exponentialRampToValueAtTime(1600, now + 0.04);
                
                gain.gain.setValueAtTime(0.3, now);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.04);
                
                osc.connect(gain);
                gain.connect(masterVolume);
                osc.start(now);
                osc.stop(now + 0.05);
                break;
            }
            case 'click': {
                // Futuristic mechanical tap
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(450, now);
                osc.frequency.exponentialRampToValueAtTime(150, now + 0.08);
                
                gain.gain.setValueAtTime(0.8, now);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
                
                osc.connect(gain);
                gain.connect(masterVolume);
                osc.start(now);
                osc.stop(now + 0.09);
                break;
            }
            case 'start': {
                // Futuristic energy sweep swoosh
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(100, now);
                osc.frequency.exponentialRampToValueAtTime(800, now + 0.25);
                
                gain.gain.setValueAtTime(0.6, now);
                gain.gain.linearRampToValueAtTime(0.01, now + 0.25);
                
                osc.connect(gain);
                gain.connect(masterVolume);
                osc.start(now);
                osc.stop(now + 0.26);
                break;
            }
            case 'achievement': {
                // Retro gaming major chord arpeggio
                const notes = [261.63, 329.63, 392.00, 523.25]; // C4, E4, G4, C5 arpeggio
                notes.forEach((freq, idx) => {
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(freq, now + idx * 0.08);
                    
                    gain.gain.setValueAtTime(0.4, now + idx * 0.08);
                    gain.gain.exponentialRampToValueAtTime(0.01, now + idx * 0.08 + 0.15);
                    
                    osc.connect(gain);
                    gain.connect(masterVolume);
                    osc.start(now + idx * 0.08);
                    osc.stop(now + idx * 0.08 + 0.16);
                });
                break;
            }
            case 'type': {
                // Short typing mechanical click
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(800 + Math.random() * 300, now);
                
                gain.gain.setValueAtTime(0.15, now);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.02);
                
                osc.connect(gain);
                gain.connect(masterVolume);
                osc.start(now);
                osc.stop(now + 0.03);
                break;
            }
        }
    } catch (e) {
        console.warn('Audio Context play failed (awaiting user interaction):', e);
    }
};

// Bind audio context initializer to early user interactions
window.addEventListener('click', initAudioContext, { once: true });
window.addEventListener('mouseenter', initAudioContext, { once: true });
window.addEventListener('keydown', initAudioContext, { once: true });
