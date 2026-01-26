/**
 * Hero Animation - Vanilla JS port of the Remotion video
 * Handles the "Scenes" and background effects.
 */

class HeroAnimation {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.ctx = null;
        this.canvas = null;
        this.width = 0;
        this.height = 0;

        this.startTime = Date.now();
        this.scenes = {
            hero: { start: 0, duration: 4.5 },
            hook: { start: 4.5, duration: 5 },
            philosophy: { start: 9.5, duration: 5.5 },
            arsenal: { start: 15, duration: 7 },
            cta: { start: 22, duration: 6 },
            tagline: { start: 28, duration: 4.5 },
        };
        this.totalDuration = 32.5; // Seconds

        // Background elements state
        this.candles = Array.from({ length: 15 }).map((_, i) => ({
            delay: Math.random() * 200,
            x: (i * 7), // percent
            speed: Math.random() * 0.5 + 0.5,
            height: Math.random() * 60 + 20,
            isGreen: Math.random() > 0.5,
            offset: Math.random() * 1000
        }));

        this.particles = Array.from({ length: 20 }).map((_, i) => ({
            x: Math.random() * 100,
            y: Math.random() * 100,
            speed: Math.random() * 0.2 + 0.1
        }));

        this.init();
    }

    init() {
        // Create Canvas for background
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.zIndex = '0';
        this.canvas.style.opacity = '0.4';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        // Create DOM containers for text scenes
        this.sceneContainer = document.createElement('div');
        this.sceneContainer.className = 'scene-container';
        this.container.appendChild(this.sceneContainer);

        this.resize();
        window.addEventListener('resize', () => this.resize());

        requestAnimationFrame(() => this.loop());
    }

    resize() {
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        this.canvas.width = this.width;
        this.canvas.height = this.height;
    }

    getSceneProgress(time, scene) {
        if (time < scene.start || time > scene.start + scene.duration) return -1;
        return (time - scene.start) / scene.duration;
    }

    getOpacity(progress) {
        if (progress < 0) return 0;
        // Fade in 0-15%, fade out 85-100%
        if (progress < 0.15) return progress / 0.15;
        if (progress > 0.85) return (1 - progress) / 0.15;
        return 1;
    }

    loop() {
        const now = Date.now();
        const elapsed = (now - this.startTime) / 1000;
        const loopTime = elapsed % this.totalDuration;

        this.drawBackground(loopTime);
        this.drawScenes(loopTime);

        requestAnimationFrame(() => this.loop());
    }

    drawBackground(time) {
        this.ctx.clearRect(0, 0, this.width, this.height);

        // Grid Effect (Simple lines)
        this.ctx.strokeStyle = 'rgba(128, 0, 128, 0.1)';
        this.ctx.lineWidth = 1;
        const gridSize = 80;
        const offset = (time * 10) % gridSize;

        for (let x = 0; x < this.width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.height);
            this.ctx.stroke();
        }

        for (let y = offset; y < this.height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.width, y);
            this.ctx.stroke();
        }

        // Floating Candles
        this.candles.forEach(c => {
            const yProgress = ((time * 20 + c.offset) % (this.height + 200)) - 100;
            const y = this.height - yProgress; // Move up

            const x = (c.x / 100) * this.width;

            this.ctx.fillStyle = c.isGreen ? '#22c55e' : '#a855f7';
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = c.isGreen ? 'rgba(34,197,94,0.5)' : 'rgba(168,85,247,0.5)';

            // Wick
            this.ctx.fillRect(x - 0.5, y - 10, 1, c.height + 20);
            // Body
            this.ctx.fillRect(x - 3, y, 6, c.height);

            this.ctx.shadowBlur = 0;
        });

        // Particles
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        this.particles.forEach((p, i) => {
            const x = (p.x + Math.sin(time * 0.5 + i) * 10) % 100;
            const y = (p.y + time * 2) % 100;

            const px = (x / 100) * this.width;
            const py = (y / 100) * this.height;

            this.ctx.beginPath();
            this.ctx.arc(px, py, 1.5, 0, Math.PI * 2);
            this.ctx.fill();
        });
    }

    drawScenes(time) {
        // Clear previous scene content if scene changed (simple check)
        // Ideally we should diff, but for now we'll just update opacity/content

        let activeScene = null;
        let activeKey = null;

        for (const [key, scene] of Object.entries(this.scenes)) {
            const progress = this.getSceneProgress(time, scene);
            if (progress >= 0 && progress <= 1) {
                activeScene = scene;
                activeKey = key;
                break;
            }
        }

        if (!activeKey) {
            this.sceneContainer.innerHTML = '';
            return;
        }

        const progress = this.getSceneProgress(time, activeScene);
        const opacity = this.getOpacity(progress);

        // Render Scene Content
        let html = '';

        if (activeKey === 'hero') {
            const scale = 0.9 + (Math.sin(progress * Math.PI) * 0.1);
            html = `
                <div class="text-center" style="opacity: ${opacity}; transform: scale(${scale})">
                    <h1 class="title-large">
                        <span class="text-purple glow-purple">SNIPERS</span>
                        <span class="text-green glow-green">-R-US</span>
                    </h1>
                    <div class="divider-gradient"></div>
                    <p class="subtitle">PRECISION TRADING ACADEMY</p>
                </div>
            `;
        } else if (activeKey === 'hook') {
            html = `
                <div class="text-center" style="opacity: ${opacity}; transform: translateY(${(1 - progress) * 20}px)">
                    <h2 class="title-medium">
                        STOP <span class="text-purple underline">GAMBLING</span>.<br>
                        START <span class="text-green">SNIPING</span>.
                    </h2>
                    <p class="text-desc">
                        Tired of chasing price? We don't guess — <span class="italic text-white">we calculate</span>.
                        Wait for the perfect strike.
                    </p>
                </div>
            `;
        } else if (activeKey === 'philosophy') {
            html = `
                <div class="text-center" style="opacity: ${opacity}">
                    <h2 class="title-small text-muted">THE SNIPER PHILOSOPHY</h2>
                    <div class="quote-box">
                        <p class="title-medium italic">"ONE SHOT, ONE KILL"</p>
                        <p class="text-desc">One perfect entry. One risk-managed trade. Pure efficiency.</p>
                    </div>
                </div>
            `;
        } else if (activeKey === 'arsenal') {
            // Static list for simplicity in vanilla JS, could animate items individually
            html = `
                <div class="text-center" style="opacity: ${opacity}">
                    <h2 class="title-medium mb-4">THE ARSENAL</h2>
                    <div class="grid-2x2">
                        <div class="arsenal-card border-purple">
                            <h3 class="text-purple">VWAP Precision</h3>
                            <p>Targeting with surgical accuracy.</p>
                        </div>
                        <div class="arsenal-card border-green">
                            <h3 class="text-green">Golden Pocket Zones</h3>
                            <p>Identifying institutional liquidity.</p>
                        </div>
                         <div class="arsenal-card border-purple">
                            <h3 class="text-purple">Confluence Sniping</h3>
                            <p>Bulletproof entries via data sync.</p>
                        </div>
                         <div class="arsenal-card border-green">
                            <h3 class="text-green">Patience Discipline</h3>
                            <p>Wait for the trade to come to you.</p>
                        </div>
                    </div>
                </div>
            `;
        } else if (activeKey === 'cta') {
            html = `
                <div class="text-center" style="opacity: ${opacity}">
                    <h2 class="title-large" style="font-size: 3rem;">JOIN THE <br><span class="gradient-text">SNIPERS</span></h2>
                    <button class="btn-primary-large mt-4">JOIN THE SNIPERS</button>
                    <div class="flex-row gap-4 mt-4 text-muted text-sm uppercase">
                        <span>• Consistency</span>
                        <span>• Mastery</span>
                        <span>• Freedom</span>
                    </div>
                </div>
            `;
        } else if (activeKey === 'tagline') {
            html = `
                <div class="text-center" style="opacity: ${opacity}">
                     <p class="title-medium font-light">
                        AMATEURS <span class="text-purple font-bold">CHASE</span>.<br>
                        PROFESSIONALS <span class="text-green font-bold">AIM</span>.
                    </p>
                </div>
            `;
        }

        // Only update innerHTML if scene changed or complex update
        // For performance, we'll just set it every frame for this demo as content is light
        this.sceneContainer.innerHTML = html;
    }
}

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    new HeroAnimation('hero-animation');
});
