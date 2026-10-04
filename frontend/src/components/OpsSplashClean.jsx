import React, { useEffect, useState, useRef, useCallback } from "react";

/**
 * O.P.S. — Cybernetic Retro Title Card & Landing Page
 * Over-Engineered Programmed System — Ambient AI Operating System
 * 
 * Perfect Audio Synchronization:
 * - Solves browser autoplay policy by detecting AudioContext state.
 * - If browser permits audio, starts 5s countdown and retro sounds immediately.
 * - If browser suspends audio (default Edge/Chrome behavior on batch launch),
 *   presents a high-voltage arcade prompt: "CLICK ANYWHERE TO BOOT WITH SOUND".
 * - On first click / keypress: Audio context resumes immediately, triggering the full
 *   5-second audiovisual sequence with zero delay.
 * - Zero-leak guarantee: All audio contexts, nodes, and timeouts are destroyed on exit.
 */

const LOGO_SRC = "/ops-logo.png";
const DURATION = 5000;
const FADE = 400;

export default function OpsSplashClean({ onDone }) {
  const [bootState, setBootState] = useState("CHECKING"); // 'CHECKING', 'STANDBY', 'RUNNING', 'EXITING'
  const [gone, setGone] = useState(false);
  const [pct, setPct] = useState(0);
  const [audioMuted, setAudioMuted] = useState(false);
  const [bootLogIndex, setBootLogIndex] = useState(0);

  const audioCtxRef = useRef(null);
  const masterGainRef = useRef(null);
  const isTerminatedRef = useRef(false);
  const timeoutsRef = useRef([]);
  const intervalsRef = useRef([]);

  const bootLogs = [
    "[0.2s] KERNEL INITIALIZED // ARCH: x86_64 LOCAL-FIRST",
    "[0.9s] MOUNTING POSTGRESQL PERSISTENCE ENGINE (ops_db)...",
    "[1.7s] VERIFYING LOCAL TRI-MODEL FLEET (DEEPSEEK / QWEN / LLAMA)...",
    "[2.6s] CALIBRATING DESKTOP OVERLAY DAEMON (CTRL+ALT ARMED)...",
    "[3.5s] SYNCING WEBSOCKET BUS // WS_PORTS: 8000/DEV...",
    "[4.3s] AMBIENT OPERATING SYSTEM COMBAT READY."
  ];

  const safeTimeout = useCallback((fn, delay) => {
    if (isTerminatedRef.current) return null;
    const id = setTimeout(() => {
      if (!isTerminatedRef.current) fn();
    }, delay);
    timeoutsRef.current.push(id);
    return id;
  }, []);

  // -------------------------------------------------------------
  // Clean Audio Subsystem: Master Gain & Zero-Leak Termination
  // -------------------------------------------------------------
  const cleanAudio = useCallback(() => {
    isTerminatedRef.current = true;
    timeoutsRef.current.forEach(clearTimeout);
    intervalsRef.current.forEach(clearInterval);
    timeoutsRef.current = [];
    intervalsRef.current = [];

    if (masterGainRef.current) {
      try {
        masterGainRef.current.gain.cancelScheduledValues(0);
        masterGainRef.current.gain.setValueAtTime(0, 0);
      } catch {}
    }

    if (audioCtxRef.current) {
      try {
        audioCtxRef.current.close().catch(() => {});
      } catch {}
      audioCtxRef.current = null;
    }
  }, []);

  const getAudioContext = useCallback(() => {
    if (isTerminatedRef.current) return null;
    if (!audioCtxRef.current) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      try {
        const ctx = new AudioCtx();
        const master = ctx.createGain();
        master.gain.setValueAtTime(audioMuted ? 0 : 1, 0);
        master.connect(ctx.destination);
        audioCtxRef.current = ctx;
        masterGainRef.current = master;
      } catch {
        return null;
      }
    }
    return audioCtxRef.current;
  }, [audioMuted]);

  const connectToMaster = useCallback((node) => {
    if (masterGainRef.current && node) {
      node.connect(masterGainRef.current);
    }
  }, []);

  // 1. CRT Power-On & Degauss Thump
  const playCrtTurnOn = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const t = ctx.currentTime;

      const subOsc = ctx.createOscillator();
      const subGain = ctx.createGain();
      subOsc.type = "sine";
      subOsc.frequency.setValueAtTime(140, t);
      subOsc.frequency.exponentialRampToValueAtTime(32, t + 0.35);

      subGain.gain.setValueAtTime(0.35, t);
      subGain.gain.exponentialRampToValueAtTime(0.001, t + 0.38);

      subOsc.connect(subGain);
      connectToMaster(subGain);
      subOsc.start(t);
      subOsc.stop(t + 0.38);

      const flyOsc = ctx.createOscillator();
      const flyGain = ctx.createGain();
      flyOsc.type = "sawtooth";
      flyOsc.frequency.setValueAtTime(14000, t + 0.05);
      flyOsc.frequency.exponentialRampToValueAtTime(8000, t + 0.25);

      flyGain.gain.setValueAtTime(0.001, t);
      flyGain.gain.linearRampToValueAtTime(0.035, t + 0.05);
      flyGain.gain.exponentialRampToValueAtTime(0.0001, t + 0.28);

      flyOsc.connect(flyGain);
      connectToMaster(flyGain);
      flyOsc.start(t + 0.05);
      flyOsc.stop(t + 0.28);
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 2. Retro Cyber Boot Chime / Polyphonic FM Arpeggio
  const playBootArpeggio = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const t = ctx.currentTime;

      const notes = [261.63, 311.13, 349.23, 392.0, 466.16, 523.25];
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "square";
        osc.frequency.setValueAtTime(freq, t + idx * 0.08);

        const filter = ctx.createBiquadFilter();
        filter.type = "lowpass";
        filter.frequency.setValueAtTime(2400, t + idx * 0.08);

        gain.gain.setValueAtTime(0.09, t + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, t + idx * 0.08 + 0.16);

        osc.connect(filter);
        filter.connect(gain);
        connectToMaster(gain);

        osc.start(t + idx * 0.08);
        osc.stop(t + idx * 0.08 + 0.16);
      });
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 3. Tactical Reticle Lock-On Sound
  const playLockChirp = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const t = ctx.currentTime;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(1760, t);
      osc.frequency.setValueAtTime(2349.3, t + 0.06);

      gain.gain.setValueAtTime(0.12, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.16);

      osc.connect(gain);
      connectToMaster(gain);
      osc.start(t);
      osc.stop(t + 0.16);
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 4. Data-Stream Seek Tick
  const playDataTick = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const t = ctx.currentTime;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(850 + Math.random() * 450, t);

      gain.gain.setValueAtTime(0.035, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.02);

      osc.connect(gain);
      connectToMaster(gain);
      osc.start(t);
      osc.stop(t + 0.025);
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 5. System Armed Warp Chime (100% Launch)
  const playArmedChime = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const t = ctx.currentTime;

      const chord = [261.63, 392.0, 523.25, 659.25, 1174.66];
      chord.forEach((freq) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, t);

        gain.gain.setValueAtTime(0.14, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.65);

        osc.connect(gain);
        connectToMaster(gain);
        osc.start(t);
        osc.stop(t + 0.65);
      });
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 6. Continuous Ambient Sci-Fi Synth Drone
  const startAmbientSynth = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const t = ctx.currentTime;

      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const droneGain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      osc1.type = "sawtooth";
      osc1.frequency.setValueAtTime(55, t);
      osc2.type = "sawtooth";
      osc2.frequency.setValueAtTime(82.4, t);

      filter.type = "lowpass";
      filter.frequency.setValueAtTime(180, t);
      filter.frequency.exponentialRampToValueAtTime(1400, t + 4.5);
      filter.Q.setValueAtTime(3.5, t);

      droneGain.gain.setValueAtTime(0.001, t);
      droneGain.gain.linearRampToValueAtTime(0.07, t + 0.4);
      droneGain.gain.linearRampToValueAtTime(0.08, t + 4.2);
      droneGain.gain.exponentialRampToValueAtTime(0.0001, t + 4.9);

      osc1.connect(filter);
      osc2.connect(filter);
      filter.connect(droneGain);
      connectToMaster(droneGain);

      osc1.start(t);
      osc2.start(t);
      osc1.stop(t + 5.0);
      osc2.stop(t + 5.0);

      const shimmerOsc = ctx.createOscillator();
      const shimmerGain = ctx.createGain();
      shimmerOsc.type = "sine";
      shimmerOsc.frequency.setValueAtTime(440, t);
      shimmerOsc.frequency.linearRampToValueAtTime(880, t + 4.5);

      shimmerGain.gain.setValueAtTime(0.0001, t);
      shimmerGain.gain.linearRampToValueAtTime(0.03, t + 1.0);
      shimmerGain.gain.exponentialRampToValueAtTime(0.0001, t + 4.8);

      shimmerOsc.connect(shimmerGain);
      connectToMaster(shimmerGain);
      shimmerOsc.start(t);
      shimmerOsc.stop(t + 5.0);
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // Master 5-second presentation runner
  const start5SecondSequence = useCallback(() => {
    if (isTerminatedRef.current) return;
    setBootState("RUNNING");

    // 1. Audio Sequence
    playCrtTurnOn();
    startAmbientSynth();
    safeTimeout(playBootArpeggio, 800);
    safeTimeout(playLockChirp, 1600);

    // 2. Boot log ticker
    const logInterval = setInterval(() => {
      setBootLogIndex((prev) => (prev < bootLogs.length - 1 ? prev + 1 : prev));
    }, 700);
    intervalsRef.current.push(logInterval);

    // 3. Progress bar with synchronized seek ticks
    let progressInterval;
    const progressStart = safeTimeout(() => {
      progressInterval = setInterval(() => {
        setPct((p) => {
          if (p >= 100) return 100;
          if (Math.random() > 0.4) playDataTick();
          return Math.min(100, p + 2);
        });
      }, 30);
      intervalsRef.current.push(progressInterval);
    }, 2000);
    timeoutsRef.current.push(progressStart);

    // 4. Final chord and fade out
    safeTimeout(playArmedChime, DURATION - FADE - 100);
    safeTimeout(() => setBootState("EXITING"), DURATION - FADE);
    safeTimeout(() => {
      setGone(true);
      cleanAudio();
      if (onDone) onDone();
    }, DURATION);
  }, [
    playCrtTurnOn,
    startAmbientSynth,
    playBootArpeggio,
    playLockChirp,
    playDataTick,
    playArmedChime,
    safeTimeout,
    cleanAudio,
    onDone,
    bootLogs.length
  ]);

  // Immediate exit / launch
  const handleLaunchNow = useCallback(() => {
    if (isTerminatedRef.current || gone) return;
    playArmedChime();
    setBootState("EXITING");
    safeTimeout(() => {
      setGone(true);
      cleanAudio();
      if (onDone) onDone();
    }, FADE);
  }, [gone, playArmedChime, safeTimeout, cleanAudio, onDone]);

  // Initial Boot Check
  useEffect(() => {
    isTerminatedRef.current = false;
    const ctx = getAudioContext();

    if (ctx) {
      if (ctx.state === "running") {
        // Autoplay already allowed: start immediately!
        start5SecondSequence();
      } else {
        // Attempt resume: if allowed without gesture, start immediately
        ctx.resume().then(() => {
          if (ctx.state === "running" && !isTerminatedRef.current) {
            start5SecondSequence();
          } else {
            setBootState("STANDBY");
          }
        }).catch(() => {
          setBootState("STANDBY");
        });
      }
    } else {
      setBootState("STANDBY");
    }

    // Engagement handler: Clicking or pressing any key starts the audio sequence
    const handleEngage = () => {
      if (isTerminatedRef.current) return;
      const activeCtx = getAudioContext();
      if (activeCtx) {
        activeCtx.resume().then(() => {
          setBootState((prev) => {
            if (prev === "STANDBY" || prev === "CHECKING") {
              start5SecondSequence();
              return "RUNNING";
            }
            return prev;
          });
        }).catch(() => {
          start5SecondSequence();
        });
      } else {
        start5SecondSequence();
      }
    };

    window.addEventListener("pointerdown", handleEngage);
    window.addEventListener("keydown", handleEngage);

    const handleKeyNav = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        handleLaunchNow();
      } else if (e.key === "m" || e.key === "M") {
        setAudioMuted((m) => {
          const next = !m;
          if (masterGainRef.current) {
            masterGainRef.current.gain.setValueAtTime(next ? 0 : 1, 0);
          }
          return next;
        });
      }
    };
    window.addEventListener("keydown", handleKeyNav);

    return () => {
      cleanAudio();
      window.removeEventListener("pointerdown", handleEngage);
      window.removeEventListener("keydown", handleEngage);
      window.removeEventListener("keydown", handleKeyNav);
    };
  }, [getAudioContext, start5SecondSequence, handleLaunchNow, cleanAudio]);

  if (gone) return null;

  const totalBlocks = 16;
  const filledBlocks = Math.round((pct / 100) * totalBlocks);

  const getStatusStage = () => {
    if (bootState === "STANDBY") return "STANDBY: PRESS ANY KEY OR CLICK TO ENGAGE";
    if (pct < 20) return "INITIALIZING KERNEL BUS...";
    if (pct < 45) return "INDEXING PERSISTENT VECTOR MEMORY...";
    if (pct < 70) return "ARMING LOCAL INFERENCE MODELS...";
    if (pct < 95) return "SYNCHRONIZING DESKTOP DAEMON...";
    return "SYSTEM AUTHORIZED. BOOT COMPLETE.";
  };

  const isExiting = bootState === "EXITING";

  return (
    <div
      className={`ops-c fixed inset-0 z-[100] overflow-hidden bg-black select-none transition-opacity ${
        isExiting ? "opacity-0" : "opacity-100"
      }`}
      style={{ transitionDuration: `${FADE}ms` }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Share+Tech+Mono&display=swap');
        .ops-c { font-family: 'VT323', 'Share Tech Mono', ui-monospace, monospace; font-size: 1.25rem; }
        .px { font-family: 'Press Start 2P', ui-monospace, monospace; }

        .stage { animation: crtPowerOn .75s cubic-bezier(.19,1,.22,1) both; }
        @keyframes crtPowerOn {
          0% { transform: scaleY(.003) scaleX(0); filter: brightness(8) contrast(2); }
          40% { transform: scaleY(.003) scaleX(1); filter: brightness(6) contrast(1.5); }
          75% { transform: scaleY(1.05) scaleX(1); filter: brightness(2); }
          100% { transform: scaleY(1) scaleX(1); filter: brightness(1) contrast(1); }
        }

        .floor {
          background-image:
            linear-gradient(rgba(239,68,68,.35) 1.5px, transparent 1.5px),
            linear-gradient(90deg, rgba(239,68,68,.35) 1.5px, transparent 1.5px);
          background-size: 56px 56px;
          transform: perspective(480px) rotateX(68deg) scale(2.6);
          transform-origin: 50% 100%;
          animation: moveGrid 1.1s linear infinite;
          -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,.8) 40%, transparent 85%);
          mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,.8) 40%, transparent 85%);
        }
        @keyframes moveGrid { to { background-position: 0 56px; } }

        .crt::before {
          content: " ";
          display: block;
          position: absolute;
          inset: 0;
          background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.4) 50%),
                      linear-gradient(90deg, rgba(255, 0, 0, 0.04), rgba(0, 255, 0, 0.01), rgba(0, 255, 0, 0.04));
          z-index: 50;
          background-size: 100% 3px, 6px 100%;
          pointer-events: none;
        }

        .crt::after {
          content: "";
          position: absolute;
          inset: 0;
          pointer-events: none;
          z-index: 51;
          background: radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.85) 100%);
          box-shadow: inset 0 0 120px rgba(0,0,0,0.9);
        }

        .scan-bar {
          position: absolute;
          inset-x: 0;
          height: 12px;
          background: linear-gradient(to bottom, transparent, rgba(239, 68, 68, 0.15), transparent);
          z-index: 45;
          pointer-events: none;
          animation: scanRoll 4.2s linear infinite;
        }
        @keyframes scanRoll {
          0% { top: -20px; opacity: 0; }
          10% { opacity: 0.8; }
          90% { opacity: 0.8; }
          100% { top: 100%; opacity: 0; }
        }

        .reticle-spin { animation: reticleSpin 16s linear infinite; }
        @keyframes reticleSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .reticle-spin-rev { animation: reticleSpinRev 24s linear infinite; }
        @keyframes reticleSpinRev { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }

        .logo-wrap { animation: logoEnter .7s cubic-bezier(0.16, 1, 0.3, 1) .55s forwards; opacity: 0; }
        @keyframes logoEnter {
          from { opacity: 0; transform: scale(.78) translateY(12px); filter: blur(6px); }
          to { opacity: 1; transform: scale(1) translateY(0); filter: blur(0); }
        }

        .holo-pulse { animation: holoPulse 2.8s ease-in-out infinite alternate; }
        @keyframes holoPulse {
          0% { filter: drop-shadow(0 0 15px rgba(220,38,38,0.4)) brightness(1); }
          100% { filter: drop-shadow(0 0 35px rgba(239,68,68,0.85)) brightness(1.2); }
        }

        .glitch-title {
          position: relative;
          display: inline-block;
          animation: titleEnter .5s steps(8) 1.3s forwards;
          opacity: 0;
          text-shadow: 0 0 20px rgba(239, 68, 68, 0.8), 3px 3px 0 #7f1d1d, -2px -2px 0 #0284c7;
        }
        @keyframes titleEnter {
          from { opacity: 0; letter-spacing: .45em; transform: scale(0.9); }
          to { opacity: 1; letter-spacing: .06em; transform: scale(1); }
        }

        .rule-glow { transform: scaleX(0); animation: ruleExpand .5s cubic-bezier(.25,1,.5,1) 1.9s forwards; }
        @keyframes ruleExpand { to { transform: scaleX(1); } }

        .sub-type { clip-path: inset(0 100% 0 0); animation: textWipe .7s steps(28) 2.1s forwards; }
        @keyframes textWipe { to { clip-path: inset(0 0 0 0); } }

        .load-block { opacity: 0; animation: fadeIn .4s ease-out 2.3s forwards; }
        @keyframes fadeIn { to { opacity: 1; } }

        .blink-fast { animation: blinkRate .6s steps(1) infinite; }
        @keyframes blinkRate { 50% { opacity: 0; } }

        .arcade-prompt {
          animation: arcadePulse 1.2s ease-in-out infinite alternate;
        }
        @keyframes arcadePulse {
          0% { transform: scale(0.98); box-shadow: 0 0 15px rgba(239,68,68,0.5); }
          100% { transform: scale(1.02); box-shadow: 0 0 30px rgba(239,68,68,0.9); }
        }

        @media (prefers-reduced-motion: reduce) {
          .ops-c *, .ops-c *::before, .ops-c *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
          }
        }
      `}</style>

      <div className="stage crt relative h-full w-full flex flex-col justify-between p-4 sm:p-8 cursor-pointer">
        <div className="scan-bar" />

        {/* 3D Synthwave Perspective Grid Floor */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[62vh] overflow-hidden">
          <div className="floor absolute inset-0" />
        </div>

        {/* Cyberpunk Sun / Horizon Vanishing Glow */}
        <div className="pointer-events-none absolute left-1/2 top-[52%] -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[radial-gradient(ellipse_at_center,rgba(220,38,38,0.22)_0%,rgba(185,28,28,0.08)_50%,transparent_75%)] blur-2xl" />

        {/* Tactical Corner Brackets */}
        <div className="pointer-events-none absolute inset-3 sm:inset-6">
          <div className="absolute left-0 top-0 w-8 h-8 border-l-2 border-t-2 border-red-500 flex items-start justify-start p-1">
            <span className="text-[10px] text-red-500 font-mono tracking-widest leading-none">01</span>
          </div>
          <div className="absolute right-0 top-0 w-8 h-8 border-r-2 border-t-2 border-red-500 flex items-start justify-end p-1">
            <span className="text-[10px] text-red-500 font-mono tracking-widest leading-none">02</span>
          </div>
          <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-zinc-600 flex items-end justify-start p-1">
            <span className="text-[10px] text-zinc-500 font-mono tracking-widest leading-none">03</span>
          </div>
          <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-zinc-600 flex items-end justify-end p-1">
            <span className="text-[10px] text-zinc-500 font-mono tracking-widest leading-none">04</span>
          </div>

          <div className="absolute left-1/2 top-0 -translate-x-1/2 flex items-center gap-3">
            <span className="h-[2px] w-12 bg-red-600/60" />
            <span className="text-[11px] text-red-400 tracking-[0.3em] font-mono uppercase">O.P.S // AMBIENT BOOT SEQUENCE</span>
            <span className="h-[2px] w-12 bg-red-600/60" />
          </div>
        </div>

        {/* TOP STATUS BAR: HUD Telemetry & Audio Toggle */}
        <header className="relative z-20 flex items-center justify-between text-xs tracking-wider text-neutral-400 pt-1">
          <div className="flex items-center gap-3 font-mono">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-red-600/70 bg-red-950/40 text-red-300 font-bold text-[11px]">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
              {bootState === "STANDBY" ? "STANDBY_WAIT" : "SYSTEM_LIVE"}
            </span>
            <span className="hidden sm:inline text-neutral-500">
              SYS: <strong className="text-neutral-300">TITAN-X</strong> | ARCH: <strong className="text-neutral-300">LOCAL_LLM</strong>
            </span>
          </div>

          <div className="flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => {
                setAudioMuted((m) => {
                  const next = !m;
                  if (masterGainRef.current) {
                    masterGainRef.current.gain.setValueAtTime(next ? 0 : 1, 0);
                  }
                  return next;
                });
              }}
              title="Toggle Audio FX [Press M]"
              className={`px-2.5 py-1 border text-[11px] font-mono tracking-wider transition cursor-pointer flex items-center gap-1.5 ${
                audioMuted
                  ? "border-neutral-700 bg-neutral-900/60 text-neutral-500 hover:text-white"
                  : "border-red-600/80 bg-red-950/60 text-red-200 hover:border-red-400 shadow-[0_0_10px_rgba(220,38,38,0.4)]"
              }`}
            >
              <span>{audioMuted ? "🔇 AUDIO: MUTED [M]" : "🔊 RETRO FX: ON [M]"}</span>
            </button>

            <button
              onClick={handleLaunchNow}
              className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white font-mono text-xs font-bold tracking-widest transition cursor-pointer shadow-[0_0_15px_rgba(220,38,38,0.6)] active:scale-95 border border-red-400"
            >
              SKIP [ESC]
            </button>
          </div>
        </header>

        {/* CENTERSTAGE: Holographic Reticle + Logo + 3D Glitch Title */}
        <main className="relative z-20 flex flex-col items-center justify-center my-auto text-center">
          <div className="relative flex items-center justify-center mb-2">
            <svg
              className="reticle-spin absolute pointer-events-none w-56 h-56 sm:w-72 sm:h-72 text-red-600/40"
              viewBox="0 0 100 100"
            >
              <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" strokeWidth="0.8" strokeDasharray="4 6" />
              <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="16 12" />
              <line x1="50" y1="2" x2="50" y2="10" stroke="currentColor" strokeWidth="1.5" />
              <line x1="50" y1="90" x2="50" y2="98" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2" y1="50" x2="10" y2="50" stroke="currentColor" strokeWidth="1.5" />
              <line x1="90" y1="50" x2="98" y2="50" stroke="currentColor" strokeWidth="1.5" />
            </svg>

            <svg
              className="reticle-spin-rev absolute pointer-events-none w-44 h-44 sm:w-56 sm:h-56 text-cyan-500/25"
              viewBox="0 0 100 100"
            >
              <polygon points="50,15 80,32 80,68 50,85 20,68 20,32" fill="none" stroke="currentColor" strokeWidth="0.8" strokeDasharray="5 3" />
            </svg>

            <div className="pointer-events-none absolute h-36 w-36 sm:h-52 sm:w-52 rounded-full bg-red-600/35 blur-3xl animate-pulse" />

            <div className="logo-wrap relative z-10 p-2">
              <img
                src={LOGO_SRC}
                alt="O.P.S Emblem"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                  const fallback = document.getElementById("ops-fallback-core");
                  if (fallback) fallback.style.display = "block";
                }}
                className="holo-pulse relative block h-[24vh] max-h-[260px] min-h-[140px] w-auto select-none object-contain"
                draggable={false}
              />

              <div id="ops-fallback-core" style={{ display: "none" }} className="w-36 h-36 relative flex items-center justify-center">
                <div className="w-28 h-28 border-2 border-red-500 rotate-45 flex items-center justify-center bg-red-950/40 shadow-[0_0_25px_rgba(239,68,68,0.7)]">
                  <span className="px text-2xl font-bold text-white tracking-widest -rotate-45">OPS</span>
                </div>
              </div>
            </div>
          </div>

          <div className="relative mt-2">
            <h1 className="glitch-title px text-4xl sm:text-6xl md:text-7xl font-extrabold text-white tracking-wider">
              O.P.S
            </h1>
            <span className="block text-[11px] font-mono tracking-[0.45em] text-red-400 mt-1 uppercase">
              VERSION 2.6 // AUTONOMOUS WORKSTATION CORE
            </span>
          </div>

          <div className="flex flex-col items-center gap-2 mt-3 max-w-xl">
            <div className="rule-glow h-[2px] w-64 sm:w-96 bg-gradient-to-r from-transparent via-red-500 to-transparent shadow-[0_0_12px_rgba(239,68,68,0.9)]" />
            <p className="sub-type text-lg sm:text-2xl tracking-[0.22em] text-neutral-200 font-semibold uppercase">
              OVER ENGINEERED PROGRAM SYSTEM
            </p>
            <p className="text-xs sm:text-sm tracking-[0.16em] text-neutral-400 font-mono">
              [ 100% LOCAL-FIRST AMBIENT AI OPERATING SYSTEM ]
            </p>
          </div>

          {/* STANDBY ARCADE PROMPT (Triggers sound & countdown on gesture) */}
          {bootState === "STANDBY" && (
            <div className="arcade-prompt mt-5 inline-flex flex-col items-center gap-1.5 px-6 py-3 border-2 border-red-500 bg-red-950/80 text-white font-mono text-sm tracking-widest">
              <span className="text-red-400 text-xs tracking-[0.3em]">-- AUDIO ENGINE READY --</span>
              <span className="font-bold text-base text-yellow-300">
                ⚡ CLICK ANYWHERE OR PRESS ANY KEY TO INITIALIZE ⚡
              </span>
              <span className="text-neutral-400 text-[11px] tracking-wider">
                [ ENGAGES 5-SECOND RETRO AUDIO-VISUAL SEQUENCE ]
              </span>
            </div>
          )}

          {/* Segmented LED Progress Bar */}
          <div className="load-block mt-6 w-72 sm:w-96 max-w-full">
            <div className="mb-2 flex items-center justify-between text-xs font-mono">
              <span className="text-red-400 flex items-center gap-1.5 font-bold tracking-wider">
                <span className="w-1.5 h-1.5 bg-red-500 inline-block animate-ping" />
                {getStatusStage()}
              </span>
              <span className="text-white px text-[10px] tracking-widest bg-red-950/80 px-2 py-0.5 border border-red-700">
                {String(pct).padStart(3, "0")}%
              </span>
            </div>

            <div className="flex items-center gap-1 p-1 bg-black/90 border border-neutral-700 shadow-inner">
              {Array.from({ length: totalBlocks }).map((_, i) => {
                const isFilled = i < filledBlocks;
                const isHead = i === filledBlocks - 1;
                return (
                  <div
                    key={i}
                    className={`h-3.5 flex-1 transition-all duration-75 ${
                      isFilled
                        ? isHead
                          ? "bg-white shadow-[0_0_10px_#ffffff]"
                          : "bg-red-600 shadow-[0_0_6px_rgba(220,38,38,0.8)]"
                        : "bg-neutral-900 border border-neutral-800"
                    }`}
                  />
                );
              })}
            </div>

            <div className="mt-2 flex justify-between text-[11px] font-mono text-neutral-500">
              <span>BUS: 128-BIT DIRECT</span>
              <span>RATE: {pct > 0 && pct < 100 ? `${(pct * 8.4).toFixed(1)} MB/s` : bootState === "STANDBY" ? "AWAITING START" : "STANDBY"}</span>
              <span>SECURITY: SHA-256</span>
            </div>
          </div>
        </main>

        {/* BOTTOM HUD FOOTER */}
        <footer className="relative z-20 flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-neutral-400 border-t border-neutral-900 pt-3 gap-2">
          <div className="flex items-center gap-2 text-left w-full sm:w-auto">
            <span className="text-red-500 font-bold">[BIOS]</span>
            <span className="text-neutral-300 truncate max-w-sm sm:max-w-md">
              {bootState === "STANDBY" ? "WAITING FOR OPERATOR AUTHORIZATION (KEYPRESS/CLICK)..." : bootLogs[bootLogIndex]}
            </span>
            <span className="text-red-500 blink-fast">_</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-neutral-500 text-[11px] hidden md:inline">
              PRESS <kbd className="text-red-400 bg-neutral-900 px-1 border border-neutral-700">ESC</kbd> TO BYPASS INTRO
            </span>
            <span className="text-red-500/80 font-mono text-[11px] font-bold">
              {bootState === "STANDBY" ? "STANDBY" : `AUTO-LAUNCH IN ${Math.max(0, Math.ceil((DURATION - pct * (DURATION / 100)) / 1000))}s`}
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
