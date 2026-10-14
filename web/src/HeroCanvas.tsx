import { useEffect, useRef } from 'react';

export type OrbState = 'idle' | 'recording' | 'analyzing' | 'results' | 'error';

export interface HeroCanvasProps {
  state?: OrbState;
  audioLevel?: number; // 0.0 to 1.0 real-time microphone volume
  score?: number | null;
  onOrbClick?: () => void;
  frequencyData?: Uint8Array | null;
  scrollProgress?: number; // 0.0 (top) to 1.0 (scrolled)
}

interface Particle {
  x: number;
  y: number;
  angle: number;
  dist: number;
  speed: number;
  radius: number;
  opacity: number;
  color: string;
}

export function HeroCanvas({
  state = 'idle',
  audioLevel = 0,
  score,
  onOrbClick,
  frequencyData,
  scrollProgress = 0
}: HeroCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rafRef = useRef<number>(0);
  const timeRef = useRef<number>(0);
  const smoothedLevelRef = useRef<number>(0);

  // Mouse tilt tracking for 3D parallax depth
  const mouseRef = useRef<{ x: number; y: number; tx: number; ty: number }>({
    x: 0,
    y: 0,
    tx: 0,
    ty: 0
  });

  // Keep latest props in refs for RAF loop
  const stateRef = useRef<OrbState>(state);
  const audioLevelRef = useRef<number>(audioLevel);
  const scoreRef = useRef<number | null | undefined>(score);
  const freqDataRef = useRef<Uint8Array | null | undefined>(frequencyData);
  const scrollRef = useRef<number>(scrollProgress);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    audioLevelRef.current = audioLevel;
  }, [audioLevel]);

  useEffect(() => {
    scoreRef.current = score;
  }, [score]);

  useEffect(() => {
    freqDataRef.current = frequencyData;
  }, [frequencyData]);

  useEffect(() => {
    scrollRef.current = scrollProgress;
  }, [scrollProgress]);

  useEffect(() => {
    const handlePointerMove = (e: PointerEvent) => {
      const nx = (e.clientX / window.innerWidth - 0.5) * 2;
      const ny = (e.clientY / window.innerHeight - 0.5) * 2;
      mouseRef.current.tx = Math.max(-1, Math.min(1, nx));
      mouseRef.current.ty = Math.max(-1, Math.min(1, ny));
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dpr = 1;

    const setSize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.offsetWidth;
      height = canvas.offsetHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    setSize();

    // Ambient floating particles with luminous palette
    const particleColors = [
      'rgba(121, 107, 250, ',  // electric violet
      'rgba(54, 226, 180, ',   // mint
      'rgba(84, 167, 255, ',   // cyan
      'rgba(244, 114, 182, '   // rose quartz highlight
    ];

    const particles: Particle[] = Array.from({ length: 48 }, () => ({
      x: 0,
      y: 0,
      angle: Math.random() * Math.PI * 2,
      dist: Math.random() * 180 + 35,
      speed: (Math.random() * 0.012 + 0.004) * (Math.random() > 0.5 ? 1 : -1),
      radius: Math.random() * 2.2 + 0.8,
      opacity: Math.random() * 0.5 + 0.2,
      color: particleColors[Math.floor(Math.random() * particleColors.length)]
    }));

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const render = () => {
      timeRef.current += prefersReducedMotion ? 0.2 : 1.0;
      const t = timeRef.current;
      const currentState = stateRef.current;
      const targetLevel = audioLevelRef.current || 0;
      const scroll = Math.min(1.0, Math.max(0, scrollRef.current || 0));

      // Mouse smooth interpolation
      mouseRef.current.x += (mouseRef.current.tx - mouseRef.current.x) * 0.06;
      mouseRef.current.y += (mouseRef.current.ty - mouseRef.current.y) * 0.06;
      const mx = prefersReducedMotion ? 0 : mouseRef.current.x;
      const my = prefersReducedMotion ? 0 : mouseRef.current.y;

      // Smooth audio level (actual mic data)
      smoothedLevelRef.current += (targetLevel - smoothedLevelRef.current) * 0.28;
      const level = smoothedLevelRef.current;

      ctx.clearRect(0, 0, width, height);

      // Scroll-driven position and scale modulation
      const scrollScale = Math.max(0.5, 1.0 - scroll * 0.45);
      const scrollOpacity = Math.max(0.15, 1.0 - scroll * 0.7);
      const scrollOffsetY = -scroll * 60;

      const centerX = width * 0.5 + mx * 14;
      const centerY = height * 0.44 + my * 14 + scrollOffsetY;
      const minDim = Math.min(width, height);

      // Base radius adapted to screen size and scroll
      const baseRadius = Math.max(65, Math.min(130, minDim * 0.18)) * scrollScale;

      // Dynamic radius modulation by state & audio
      let breath = Math.sin(t * 0.035) * 4;
      let energyScale = 1.0;

      if (currentState === 'recording') {
        energyScale = 1.0 + level * 0.42;
        breath = Math.sin(t * 0.12) * (6 + level * 22);
      } else if (currentState === 'analyzing') {
        energyScale = 1.0 + Math.sin(t * 0.08) * 0.08;
        breath = Math.sin(t * 0.06) * 3;
      } else if (currentState === 'results') {
        breath = Math.sin(t * 0.02) * 2.5;
      } else if (currentState === 'error') {
        breath = Math.sin(t * 0.08) * 3.5;
      }

      const orbRadius = (baseRadius + breath) * energyScale;

      ctx.save();
      ctx.globalAlpha = scrollOpacity;

      // ----------------------------------------------------
      // 1. BACKGROUND HORIZON HARMONIC WAVES
      // ----------------------------------------------------
      const waveConfigs = [
        { yOffset: 0.35, amp: 18, freq: 0.005, speed: 0.015, color: '121, 107, 250', alpha: 0.14 },
        { yOffset: 0.45, amp: 24, freq: 0.007, speed: 0.02, color: '84, 167, 255', alpha: 0.12 },
        { yOffset: 0.55, amp: 20, freq: 0.004, speed: 0.012, color: '54, 226, 180', alpha: 0.11 },
        { yOffset: 0.65, amp: 16, freq: 0.008, speed: 0.025, color: '159, 149, 252', alpha: 0.09 }
      ];

      waveConfigs.forEach((w) => {
        const baseY = height * w.yOffset + scrollOffsetY * 0.5;
        ctx.beginPath();
        ctx.moveTo(0, baseY);
        for (let x = 0; x <= width; x += 6) {
          const micPerturbation = currentState === 'recording'
            ? Math.sin(x * 0.04 + t * 0.2) * (level * 24)
            : 0;
          const y = baseY +
            Math.sin(x * w.freq + t * w.speed) * w.amp +
            Math.cos(x * (w.freq * 1.6) + t * (w.speed * 0.8)) * (w.amp * 0.4) +
            micPerturbation;
          ctx.lineTo(x, y);
        }
        ctx.strokeStyle = `rgba(${w.color}, ${w.alpha})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      });

      // ----------------------------------------------------
      // 2. VOLUMETRIC CORONA & OUTER GLOW
      // ----------------------------------------------------
      const coronaGrad = ctx.createRadialGradient(
        centerX, centerY, orbRadius * 0.25,
        centerX, centerY, orbRadius * 2.5
      );

      if (currentState === 'recording') {
        coronaGrad.addColorStop(0, `rgba(54, 226, 180, ${0.45 + level * 0.45})`);
        coronaGrad.addColorStop(0.35, `rgba(121, 107, 250, ${0.3 + level * 0.35})`);
        coronaGrad.addColorStop(0.75, 'rgba(84, 167, 255, 0.1)');
        coronaGrad.addColorStop(1, 'rgba(10, 14, 39, 0)');
      } else if (currentState === 'analyzing') {
        coronaGrad.addColorStop(0, 'rgba(121, 107, 250, 0.48)');
        coronaGrad.addColorStop(0.45, 'rgba(84, 167, 255, 0.28)');
        coronaGrad.addColorStop(0.8, 'rgba(121, 107, 250, 0.08)');
        coronaGrad.addColorStop(1, 'rgba(10, 14, 39, 0)');
      } else if (currentState === 'error') {
        coronaGrad.addColorStop(0, 'rgba(255, 146, 126, 0.45)');
        coronaGrad.addColorStop(0.5, 'rgba(248, 113, 113, 0.2)');
        coronaGrad.addColorStop(1, 'rgba(10, 14, 39, 0)');
      } else if (currentState === 'results') {
        coronaGrad.addColorStop(0, 'rgba(54, 226, 180, 0.38)');
        coronaGrad.addColorStop(0.5, 'rgba(121, 107, 250, 0.2)');
        coronaGrad.addColorStop(1, 'rgba(10, 14, 39, 0)');
      } else {
        // Idle
        coronaGrad.addColorStop(0, 'rgba(121, 107, 250, 0.32)');
        coronaGrad.addColorStop(0.4, 'rgba(84, 167, 255, 0.16)');
        coronaGrad.addColorStop(0.75, 'rgba(54, 226, 180, 0.06)');
        coronaGrad.addColorStop(1, 'rgba(10, 14, 39, 0)');
      }

      ctx.fillStyle = coronaGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, orbRadius * 2.5, 0, Math.PI * 2);
      ctx.fill();

      // ----------------------------------------------------
      // 3. CONCENTRIC 3D CONTOUR RINGS (SIRI DEPTH)
      // ----------------------------------------------------
      const ringCount = currentState === 'analyzing' ? 6 : 4;
      for (let i = 0; i < ringCount; i++) {
        const ringProgress = (i + 1) / (ringCount + 1);
        const ringRadius = orbRadius * (0.8 + ringProgress * 0.6);
        const rotationSpeed = (currentState === 'analyzing' ? 0.045 : 0.015) * (i % 2 === 0 ? 1 : -1);
        const ringAngle = t * rotationSpeed + (i * Math.PI) / 3 + mx * 0.3;

        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(ringAngle);
        ctx.scale(1.0, 0.35 + Math.sin(t * 0.02 + i) * 0.15 + my * 0.1);

        ctx.beginPath();
        ctx.arc(0, 0, ringRadius, 0, Math.PI * 2);

        let ringAlpha = 0.26 - i * 0.04;
        if (currentState === 'recording') ringAlpha += level * 0.4;
        if (currentState === 'analyzing') ringAlpha = 0.38;

        const ringColor = i % 2 === 0
          ? `rgba(121, 107, 250, ${ringAlpha})`
          : `rgba(54, 226, 180, ${ringAlpha})`;
        ctx.strokeStyle = ringColor;
        ctx.lineWidth = currentState === 'recording' ? 1.8 + level * 2.5 : 1.3;
        ctx.stroke();

        ctx.restore();
      }

      // ----------------------------------------------------
      // 4. MAIN 3D VOLUMETRIC GLASS ORB SPHERE
      // ----------------------------------------------------
      // Light source moves with cursor for genuine 3D perspective
      const lightOffsetX = centerX - orbRadius * 0.32 + mx * (orbRadius * 0.18);
      const lightOffsetY = centerY - orbRadius * 0.32 + my * (orbRadius * 0.18);

      const sphereGrad = ctx.createRadialGradient(
        lightOffsetX, lightOffsetY, orbRadius * 0.05,
        centerX, centerY, orbRadius
      );

      if (currentState === 'recording') {
        sphereGrad.addColorStop(0, '#FFFFFF');
        sphereGrad.addColorStop(0.18, '#A7F3D0'); // soft mint
        sphereGrad.addColorStop(0.42, '#36E2B4'); // electric mint
        sphereGrad.addColorStop(0.72, '#54A7FF'); // cyan
        sphereGrad.addColorStop(0.9, '#796BFA');  // violet
        sphereGrad.addColorStop(1, '#1A1B4B');    // deep midnight
      } else if (currentState === 'analyzing') {
        sphereGrad.addColorStop(0, '#FFFFFF');
        sphereGrad.addColorStop(0.2, '#DDD6FE'); // lavender
        sphereGrad.addColorStop(0.48, '#796BFA'); // electric violet
        sphereGrad.addColorStop(0.8, '#3B82F6');  // blue
        sphereGrad.addColorStop(1, '#0F172A');
      } else if (currentState === 'error') {
        sphereGrad.addColorStop(0, '#FFF1F2');
        sphereGrad.addColorStop(0.25, '#FDA4AF');
        sphereGrad.addColorStop(0.6, '#F43F5E');
        sphereGrad.addColorStop(0.9, '#881337');
        sphereGrad.addColorStop(1, '#180309');
      } else if (currentState === 'results') {
        sphereGrad.addColorStop(0, '#FFFFFF');
        sphereGrad.addColorStop(0.2, '#BAE6FD');
        sphereGrad.addColorStop(0.5, '#36E2B4');
        sphereGrad.addColorStop(0.8, '#6366F1');
        sphereGrad.addColorStop(1, '#0C1033');
      } else {
        // Idle
        sphereGrad.addColorStop(0, '#F5F3FF');
        sphereGrad.addColorStop(0.15, '#C4B5FD');
        sphereGrad.addColorStop(0.42, '#796BFA');
        sphereGrad.addColorStop(0.72, '#54A7FF');
        sphereGrad.addColorStop(0.92, '#36E2B4');
        sphereGrad.addColorStop(1, '#0B0F2A');
      }

      ctx.save();
      ctx.beginPath();

      // Fluid perimeter harmonic ripple (reacts to real frequency bins / audio level)
      const perimeterPoints = 54;
      const angleStep = (Math.PI * 2) / perimeterPoints;
      const freqBins = freqDataRef.current;

      for (let i = 0; i <= perimeterPoints; i++) {
        const a = i * angleStep;
        let rMod = 0;

        if (currentState === 'recording') {
          // If real frequency bins are available, modulate perimeter dynamically
          const binVal = freqBins && freqBins.length > 0
            ? (freqBins[i % freqBins.length] / 255.0)
            : level;

          rMod = Math.sin(a * 4 + t * 0.15) * (4 + level * 14) +
                 Math.cos(a * 6 - t * 0.2) * (2 + binVal * 12);
        } else if (currentState === 'analyzing') {
          rMod = Math.sin(a * 8 + t * 0.1) * 3.5;
        } else {
          rMod = Math.sin(a * 3 + t * 0.04) * 2;
        }

        const r = orbRadius + rMod;
        const px = centerX + Math.cos(a) * r;
        const py = centerY + Math.sin(a) * r;

        if (i === 0) {
          ctx.moveTo(px, py);
        } else {
          ctx.lineTo(px, py);
        }
      }
      ctx.closePath();

      ctx.fillStyle = sphereGrad;
      ctx.fill();

      // Glass rim highlight / Iridescent Fresnel edge
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
      ctx.lineWidth = 1.6;
      ctx.stroke();
      ctx.restore();

      // ----------------------------------------------------
      // 5. INTERNAL ACOUSTIC LIGHT RIBBON (GLASS REFRACTION)
      // ----------------------------------------------------
      ctx.save();
      ctx.beginPath();
      ctx.arc(centerX, centerY, orbRadius * 0.92, 0, Math.PI * 2);
      ctx.clip();

      // Inner flowing acoustic light ribbon
      ctx.beginPath();
      const ribbonY = centerY + Math.sin(t * 0.05) * 8 + my * 8;
      ctx.moveTo(centerX - orbRadius, ribbonY);
      for (let x = -orbRadius; x <= orbRadius; x += 4) {
        const curve = Math.sin((x * 0.04) + t * (currentState === 'recording' ? 0.2 : 0.05)) *
                      (currentState === 'recording' ? 12 + level * 22 : 8);
        ctx.lineTo(centerX + x, ribbonY + curve);
      }
      ctx.strokeStyle = currentState === 'recording'
        ? `rgba(255, 255, 255, ${0.4 + level * 0.5})`
        : 'rgba(255, 255, 255, 0.25)';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      ctx.restore();

      // ----------------------------------------------------
      // 6. SWARMING PARTICLES / ORBITING QUANTUM HALO
      // ----------------------------------------------------
      particles.forEach((p) => {
        let currentDist = p.dist;
        if (currentState === 'analyzing') {
          // Particles converge into tight quantum ring
          currentDist = orbRadius * 1.15 + Math.sin(t * 0.05 + p.angle) * 8;
          p.angle += p.speed * 2.5;
        } else if (currentState === 'recording') {
          currentDist = orbRadius * (1.1 + level * 0.6) + Math.sin(t * 0.1 + p.angle) * 12;
          p.angle += p.speed * (1.5 + level * 3);
        } else {
          p.angle += p.speed;
        }

        p.x = centerX + Math.cos(p.angle) * currentDist;
        p.y = centerY + Math.sin(p.angle) * currentDist;

        ctx.beginPath();
        const pulse = Math.sin(t * 0.05 + p.angle * 2) * 0.5 + 0.5;
        ctx.arc(p.x, p.y, p.radius * (0.8 + pulse * 0.4), 0, Math.PI * 2);
        ctx.fillStyle = `${p.color}${p.opacity * (0.6 + pulse * 0.4)})`;
        ctx.fill();
      });

      // ----------------------------------------------------
      // 7. ANALYZING RADIAL SCANNER OR RESULTS BADGE
      // ----------------------------------------------------
      if (currentState === 'analyzing') {
        const scanAngle = t * 0.06;
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(scanAngle);
        const scanLine = ctx.createLinearGradient(0, 0, orbRadius * 1.4, 0);
        scanLine.addColorStop(0, 'rgba(54, 226, 180, 0.85)');
        scanLine.addColorStop(0.5, 'rgba(121, 107, 250, 0.45)');
        scanLine.addColorStop(1, 'rgba(84, 167, 255, 0)');
        ctx.strokeStyle = scanLine;
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(orbRadius * 1.4, 0);
        ctx.stroke();
        ctx.restore();
      }

      ctx.restore();

      rafRef.current = requestAnimationFrame(render);
    };

    rafRef.current = requestAnimationFrame(render);

    const handleResize = () => {
      setSize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div
      className="hero-orb-wrapper"
      onClick={onOrbClick}
      role={onOrbClick ? 'button' : undefined}
      tabIndex={onOrbClick ? 0 : undefined}
      aria-label="Interactive Siri-inspired Living Audio Orb"
    >
      <canvas
        ref={canvasRef}
        className="hero-canvas-bg"
        aria-label={`Living Audio Orb state: ${state}`}
      />
    </div>
  );
}