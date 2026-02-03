import { useEffect, useRef } from 'react';
import { Navigation } from './sections/Navigation';
import { Hero } from './sections/Hero';
import { AgentIdentityModal } from './sections/AgentIdentityModal';
import { Terminal } from './sections/Terminal';
import { PaperTrading } from './sections/PaperTrading';
import { SignalFeed } from './sections/SignalFeed';
import { FuelCluster } from './sections/FuelCluster';
import { Footer } from './sections/Footer';
import { AgentConsole } from './sections/AgentConsole';
import { FreeTrialModal } from './sections/FreeTrialModal';
import { Tiers } from './sections/Tiers';
import { ZOIDToken } from './sections/ZOIDToken';
import { FreeSignals } from './sections/FreeSignals';
import { SniperGuruTracker } from './sections/SniperGuruTracker';
import { SignalBetting } from './sections/SignalBetting';
import { ClawrmaPromo } from './sections/ClawrmaPromo';

import { TerminalProvider } from './TerminalContext';

function App() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // Background Fluid Animation Effect
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;
        let particles: Particle[] = [];

        class Particle {
            x: number;
            y: number;
            vx: number;
            vy: number;
            size: number;
            color: string;

            constructor() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.vx = (Math.random() - 0.5) * 0.5;
                this.vy = (Math.random() - 0.5) * 0.5;
                this.size = Math.random() * 2 + 1;
                this.color = Math.random() > 0.5 ? 'rgba(0, 255, 65, 0.1)' : 'rgba(157, 78, 221, 0.1)';
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;
                if (this.x < 0) this.x = width;
                if (this.x > width) this.x = 0;
                if (this.y < 0) this.y = height;
                if (this.y > height) this.y = 0;
            }

            draw(ctx: CanvasRenderingContext2D) {
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        const init = () => {
            particles = [];
            for (let i = 0; i < 150; i++) {
                particles.push(new Particle());
            }
        };

        const animate = () => {
            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = 'rgba(5, 5, 5, 0)'; // Clear with transparency

            particles.forEach(p => {
                p.update();
                p.draw(ctx);
            });
            requestAnimationFrame(animate);
        };

        const handleResize = () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
            init();
        };

        window.addEventListener('resize', handleResize);
        init();
        animate();

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Scroll to top on page load
    useEffect(() => {
        window.scrollTo(0, 0);
    }, []);

    return (
        <TerminalProvider>
            <div className="bg-black min-h-screen text-white font-sans selection:bg-sniper-green/30">
                {/* Dynamic Background */}
                <canvas
                    ref={canvasRef}
                    className="fixed inset-0 z-0 pointer-events-none"
                />
                <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 z-0 pointer-events-none mix-blend-overlay"></div>

                {/* Content */}
                <div className="relative z-10">
                    <Navigation />
                    <main>
                        <Hero />
                        <ClawrmaPromo />
                        <SignalBetting />
                        <ZOIDToken />
                        <Tiers />
                        <FreeSignals />
                        <SniperGuruTracker />
                        <AgentConsole />
                        <Terminal />
                        <PaperTrading />
                        <SignalFeed />
                        <FuelCluster />
                    </main>
                    <Footer />
                </div>

                <AgentIdentityModal />
                <FreeTrialModal />
            </div>
        </TerminalProvider>
    );
}

export default App;
