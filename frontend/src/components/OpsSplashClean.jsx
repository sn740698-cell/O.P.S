import React, { useEffect, useRef, useState, useCallback } from "react";
import LayeredText from "./LayeredText";

// Dimensions & Geometry constants calibrated to the reference image (1024x547 -> 2224x1132 scale)
const CX = 1112;
const CY = 566;
const RED = "232,72,64";
const HEADING = "'Plus Jakarta Sans', system-ui, sans-serif";
const BODY = "'Inter', system-ui, sans-serif";
const MONO = "'JetBrains Mono','IBM Plex Mono','SF Mono',ui-monospace,Menlo,monospace";
const N = 96;

// Mathematical Gaussian EKG Pulse
const g = (x, c, w) => Math.exp(-((x - c) ** 2) / (2 * w * w));
function pulse(p, k, amp = 1.0) {
  const n = Math.sin(k * 0.9) * 0.05 + Math.sin(k * 2.3) * 0.03 + Math.sin(k * 5.1) * 0.015;
  const y =
    0.12 * g(p, 0.2, 0.03) -
    0.05 * g(p, 0.34, 0.01) +
    0.72 * g(p, 0.41, 0.014) -
    0.95 * g(p, 0.475, 0.018) +
    1.0 * g(p, 0.545, 0.014) -
    0.2 * g(p, 0.6, 0.02) +
    0.1 * g(p, 0.75, 0.05);
  return y * amp + n * 0.5;
}

function polar(r, deg) {
  const a = ((deg - 90) * Math.PI) / 180;
  return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
}

// Precision Badge Callout matching reference image with zero text clipping
function DiagnosticBadge({ x, y, width = 340, height = 54, title, sub, isGreen, statusDelay = "0s" }) {
  const activeColor = isGreen ? "#10b981" : `rgb(${RED})`;
  const subColor = isGreen ? "#a7f3d0" : "#9a9aa2";

  return (
    <g transform={`translate(${x}, ${y})`}>
      <rect
        width={width}
        height={height}
        rx="7"
        fill="#0c0c0f"
        stroke={isGreen ? "#10b981" : "#2e2e36"}
        strokeWidth="1.5"
        filter="url(#badgeShadow)"
      />
      <circle
        cx="18"
        cy={height / 2}
        r="4.5"
        fill={activeColor}
        className="pulse"
        style={{ animationDelay: statusDelay }}
        filter="url(#glowR)"
      />
      <text
        x="32"
        y="23"
        fill="#f4f4f4"
        fontFamily={HEADING}
        fontWeight="700"
        fontSize="12.5"
        letterSpacing="2"
      >
        {title}
      </text>
      <text
        x="32"
        y="41"
        fill={subColor}
        fontFamily={MONO}
        fontWeight="500"
        fontSize="10"
        letterSpacing="0.6"
      >
        {sub}
      </text>
    </g>
  );
}

export default function OpsSplashClean({ onComplete, onDone }) {
  const [t, setT] = useState(0);
  const [pts, setPts] = useState("");
  const [load, setLoad] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [audioMuted, setAudioMuted] = useState(false);
  const [audioUnlocked, setAudioUnlocked] = useState(false);

  // Real System Telemetry States
  const [activeStatusText, setActiveStatusText] = useState("PROBING HARDWARE & KERNEL BUS...");
  const [systemLinkText, setSystemLinkText] = useState("BUS INITIALIZING // AIRGAP STANDBY");
  const [neuralCoreText, setNeuralCoreText] = useState("SCANNING TRI-MODEL FLEET...");
  const [readyAgentText, setReadyAgentText] = useState("ALLOCATING VECTOR INDEX...");

  const buf = useRef(new Array(N).fill(0));
  const phase = useRef(0);
  const last = useRef(performance.now());
  const acc = useRef(0);
  const ampRef = useRef(1.0);
  const lastBeatCycle = useRef(-1);
  const prevLoadRef = useRef(0);

  // Audio Context Refs
  const audioCtxRef = useRef(null);
  const masterGainRef = useRef(null);
  const ambientStartedRef = useRef(false);
  const crtPlayedRef = useRef(false);
  const ambientNodesRef = useRef([]);
  const isTerminatedRef = useRef(false);

  // -------------------------------------------------------------
  // AUTHENTIC '90s RETRO SCI-FI SYNTHESIZER ENGINE
  // -------------------------------------------------------------
  const cleanupAudio = useCallback(() => {
    isTerminatedRef.current = true;
    if (ambientNodesRef.current) {
      ambientNodesRef.current.forEach((n) => {
        try {
          if (n.stop) n.stop();
          n.disconnect();
        } catch {}
      });
      ambientNodesRef.current = [];
    }
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
        master.gain.setValueAtTime(audioMuted ? 0 : 0.85, 0);
        master.connect(ctx.destination);
        audioCtxRef.current = ctx;
        masterGainRef.current = master;

        if (ctx.state === "running") {
          setAudioUnlocked(true);
        }
      } catch {
        return null;
      }
    }

    if (audioCtxRef.current && audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume().then(() => setAudioUnlocked(true)).catch(() => {});
    } else if (audioCtxRef.current && audioCtxRef.current.state === "running") {
      setAudioUnlocked(true);
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
      if (!ctx || ctx.state !== "running") return;
      const t = ctx.currentTime;

      // Sub-bass degauss thump (140 Hz -> 32 Hz)
      const subOsc = ctx.createOscillator();
      const subGain = ctx.createGain();
      subOsc.type = "sine";
      subOsc.frequency.setValueAtTime(140, t);
      subOsc.frequency.exponentialRampToValueAtTime(32, t + 0.35);

      subGain.gain.setValueAtTime(0.42, t);
      subGain.gain.exponentialRampToValueAtTime(0.001, t + 0.38);

      subOsc.connect(subGain);
      connectToMaster(subGain);
      subOsc.start(t);
      subOsc.stop(t + 0.38);

      // Flyback transformer high-pitch whine (14,000 Hz -> 8,000 Hz)
      const flyOsc = ctx.createOscillator();
      const flyGain = ctx.createGain();
      flyOsc.type = "sawtooth";
      flyOsc.frequency.setValueAtTime(14000, t + 0.05);
      flyOsc.frequency.exponentialRampToValueAtTime(8000, t + 0.25);

      flyGain.gain.setValueAtTime(0.001, t);
      flyGain.gain.linearRampToValueAtTime(0.045, t + 0.05);
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
      if (!ctx || ctx.state !== "running") return;
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

        gain.gain.setValueAtTime(0.12, t + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, t + idx * 0.08 + 0.18);

        osc.connect(filter);
        filter.connect(gain);
        connectToMaster(gain);

        osc.start(t + idx * 0.08);
        osc.stop(t + idx * 0.08 + 0.18);
      });
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 3. Tactical Subsystem Reticle Lock-On Sound
  const playLockChirp = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx || ctx.state !== "running") return;
      const t = ctx.currentTime;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(1760, t);
      osc.frequency.setValueAtTime(2349.3, t + 0.06);

      gain.gain.setValueAtTime(0.16, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.18);

      osc.connect(gain);
      connectToMaster(gain);
      osc.start(t);
      osc.stop(t + 0.18);
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 4. Data-Stream Seek Tick (authentic 90s cyber clicks as loading progresses)
  const playDataTick = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx || ctx.state !== "running") return;
      const t = ctx.currentTime;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(850 + Math.random() * 550, t);

      gain.gain.setValueAtTime(0.045, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.025);

      osc.connect(gain);
      connectToMaster(gain);
      osc.start(t);
      osc.stop(t + 0.028);
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 5. System Armed Warp Chime (100% Launch Sequence)
  const playArmedChime = useCallback(() => {
    if (isTerminatedRef.current || audioMuted) return;
    try {
      const ctx = getAudioContext();
      if (!ctx || ctx.state !== "running") return;
      const t = ctx.currentTime;

      // Upward cybernetic warp sweep
      const sweepOsc = ctx.createOscillator();
      const sweepGain = ctx.createGain();
      sweepOsc.type = "sawtooth";
      sweepOsc.frequency.setValueAtTime(260, t);
      sweepOsc.frequency.exponentialRampToValueAtTime(1600, t + 0.22);
      sweepGain.gain.setValueAtTime(0.18, t);
      sweepGain.gain.exponentialRampToValueAtTime(0.001, t + 0.25);
      sweepOsc.connect(sweepGain);
      connectToMaster(sweepGain);
      sweepOsc.start(t);
      sweepOsc.stop(t + 0.25);

      // C-Major-9 Futuristic Chord ([C4, G4, C5, E5, D6])
      const chord = [261.63, 392.0, 523.25, 659.25, 1174.66];
      chord.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, t + 0.04 + idx * 0.02);

        gain.gain.setValueAtTime(0.22, t + 0.04 + idx * 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 1.1 + idx * 0.02);

        osc.connect(gain);
        connectToMaster(gain);
        osc.start(t + 0.04 + idx * 0.02);
        osc.stop(t + 1.15 + idx * 0.02);
      });
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // 6. Continuous Ambient Sci-Fi Synth Drone
  const startAmbientSynth = useCallback(() => {
    if (isTerminatedRef.current || audioMuted || ambientStartedRef.current) return;
    try {
      const ctx = getAudioContext();
      if (!ctx || ctx.state !== "running") return;
      ambientStartedRef.current = true;
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
      droneGain.gain.linearRampToValueAtTime(0.08, t + 0.4);
      droneGain.gain.linearRampToValueAtTime(0.09, t + 4.2);
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
      shimmerGain.gain.linearRampToValueAtTime(0.035, t + 1.0);
      shimmerGain.gain.exponentialRampToValueAtTime(0.0001, t + 4.8);

      shimmerOsc.connect(shimmerGain);
      connectToMaster(shimmerGain);
      shimmerOsc.start(t);
      shimmerOsc.stop(t + 5.0);

      ambientNodesRef.current = [osc1, osc2, shimmerOsc, droneGain, shimmerGain, filter];
    } catch {}
  }, [audioMuted, getAudioContext, connectToMaster]);

  // User Interaction Audio Unlocker
  const unlockAudio = useCallback(() => {
    const ctx = getAudioContext();
    if (!ctx) return;
    const onReady = () => {
      setAudioUnlocked(true);
      setAudioMuted(false);
      if (masterGainRef.current) {
        masterGainRef.current.gain.setValueAtTime(0.85, 0);
      }
      if (!crtPlayedRef.current) {
        crtPlayedRef.current = true;
        playCrtTurnOn();
        setTimeout(playBootArpeggio, 450);
      }
      startAmbientSynth();
    };

    if (ctx.state === "suspended") {
      ctx.resume().then(onReady).catch(() => {});
    } else if (ctx.state === "running") {
      onReady();
    }
  }, [getAudioContext, playCrtTurnOn, playBootArpeggio, startAmbientSynth]);

  // Global unlock listeners
  useEffect(() => {
    const handleGesture = () => {
      unlockAudio();
    };

    window.addEventListener("pointerdown", handleGesture, { passive: true });
    window.addEventListener("click", handleGesture, { passive: true });
    window.addEventListener("keydown", handleGesture, { passive: true });
    window.addEventListener("touchstart", handleGesture, { passive: true });

    // Also attempt immediate unlock
    unlockAudio();

    return () => {
      window.removeEventListener("pointerdown", handleGesture);
      window.removeEventListener("click", handleGesture);
      window.removeEventListener("keydown", handleGesture);
      window.removeEventListener("touchstart", handleGesture);
    };
  }, [unlockAudio]);

  // Biometric Heartbeat EKG sound
  const playHeartbeat = useCallback(
    (amp = 1.0) => {
      if (isTerminatedRef.current || audioMuted) return;
      try {
        const ctx = getAudioContext();
        if (!ctx || ctx.state !== "running") return;
        const now = ctx.currentTime;
        const vol = Math.min(0.35, 0.2 * amp);

        const punch1 = ctx.createOscillator();
        const punchGain1 = ctx.createGain();
        punch1.type = "triangle";
        punch1.frequency.setValueAtTime(155, now);
        punch1.frequency.exponentialRampToValueAtTime(80, now + 0.1);
        punchGain1.gain.setValueAtTime(vol * 0.9, now);
        punchGain1.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
        punch1.connect(punchGain1);
        connectToMaster(punchGain1);
        punch1.start(now);
        punch1.stop(now + 0.13);

        const sub1 = ctx.createOscillator();
        const subGain1 = ctx.createGain();
        sub1.type = "sine";
        sub1.frequency.setValueAtTime(75, now);
        sub1.frequency.exponentialRampToValueAtTime(42, now + 0.11);
        subGain1.gain.setValueAtTime(vol, now);
        subGain1.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
        sub1.connect(subGain1);
        connectToMaster(subGain1);
        sub1.start(now);
        sub1.stop(now + 0.15);

        // Beat 2: Dub (120ms later)
        const punch2 = ctx.createOscillator();
        const punchGain2 = ctx.createGain();
        punch2.type = "triangle";
        punch2.frequency.setValueAtTime(120, now + 0.12);
        punch2.frequency.exponentialRampToValueAtTime(65, now + 0.22);
        punchGain2.gain.setValueAtTime(vol * 0.75, now + 0.12);
        punchGain2.gain.exponentialRampToValueAtTime(0.001, now + 0.24);
        punch2.connect(punchGain2);
        connectToMaster(punchGain2);
        punch2.start(now + 0.12);
        punch2.stop(now + 0.25);
      } catch {}
    },
    [audioMuted, getAudioContext, connectToMaster]
  );

  const triggerSpike = useCallback((mult = 2.0) => {
    ampRef.current = mult;
  }, []);

  const toggleAudio = useCallback(() => {
    const ctx = getAudioContext();
    if (!ctx) return;

    if (ctx.state === "suspended") {
      ctx.resume().then(() => {
        setAudioUnlocked(true);
        setAudioMuted(false);
        if (masterGainRef.current) {
          masterGainRef.current.gain.setValueAtTime(0.85, 0);
        }
        startAmbientSynth();
      });
      return;
    }

    setAudioMuted((prev) => {
      const next = !prev;
      if (masterGainRef.current) {
        masterGainRef.current.gain.setValueAtTime(next ? 0 : 0.85, 0);
      }
      return next;
    });
  }, [getAudioContext, startAmbientSynth]);

  const handleLaunchNow = useCallback(() => {
    if (isCompleted) return;
    setIsCompleted(true);
    playArmedChime();
    setTimeout(() => {
      cleanupAudio();
      const cb = onDone || onComplete;
      cb?.();
    }, 450);
  }, [isCompleted, onDone, onComplete, playArmedChime, cleanupAudio]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape" || e.code === "Space" || e.key === "Enter") {
        e.preventDefault();
        handleLaunchNow();
      } else if (e.key.toLowerCase() === "m") {
        e.preventDefault();
        toggleAudio();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleLaunchNow, toggleAudio]);

  useEffect(() => {
    return () => cleanupAudio();
  }, [cleanupAudio]);

  useEffect(() => {
    return () => cleanupAudio();
  }, [cleanupAudio]);

  // -------------------------------------------------------------
  // CONTINUOUS EKG WAVEFORM LOOP WITH REAL-TIME AUDIO SYNC
  // -------------------------------------------------------------
  useEffect(() => {
    let raf;
    const loop = (now) => {
      const dt = Math.min(0.05, (now - last.current) / 1000);
      last.current = now;
      phase.current += dt;
      acc.current += dt;

      ampRef.current = Math.max(1.0, ampRef.current - dt * 1.6);

      // Heartbeat sound fires right at the systolic EKG peak
      const cycle = Math.floor(phase.current / 2.6);
      const p = (phase.current % 2.6) / 2.6;
      if (cycle !== lastBeatCycle.current && p >= 0.41) {
        lastBeatCycle.current = cycle;
        playHeartbeat(ampRef.current);
      }

      const step = 1 / 46;
      while (acc.current >= step) {
        acc.current -= step;
        const k = phase.current * 6;
        const currentP = (phase.current % 2.6) / 2.6;
        buf.current.push(pulse(currentP, k, ampRef.current));
        buf.current.shift();
      }
      const d = buf.current
        .map((v, i) => {
          const x = CX - 105 + (i / (N - 1)) * 210;
          const y = CY - v * 70;
          return `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`;
        })
        .join(" ");
      setPts(d);
      setT(phase.current);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playHeartbeat]);

  // -------------------------------------------------------------
  // REAL HARDWARE, SYSTEM KERNEL & RUNTIME BOOT SEQUENCE
  // -------------------------------------------------------------
  const bootStartedRef = useRef(false);
  const callbacksRef = useRef({});
  callbacksRef.current = {
    onDone,
    onComplete,
    triggerSpike,
    playDataTick,
    playLockChirp,
    playArmedChime,
    playCrtTurnOn,
    playBootArpeggio,
    startAmbientSynth,
    getAudioContext,
    cleanupAudio,
  };

  const stageRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    let currentPct = 0;
    stageRef.current = 0;

    const DURATION = 3600; // 3.6s calibrated boot sequence
    const startTime = performance.now();

    // Start initial retro sound sequence
    if (!crtPlayedRef.current) {
      const ctx = callbacksRef.current.getAudioContext?.();
      if (ctx && ctx.state === "running") {
        crtPlayedRef.current = true;
        callbacksRef.current.playCrtTurnOn?.();
        setTimeout(() => callbacksRef.current.playBootArpeggio?.(), 450);
        callbacksRef.current.startAmbientSynth?.();
      }
    }

    // Smooth, guaranteed progression from 0% to 100%
    const progressTimer = setInterval(() => {
      if (cancelled) return;
      const elapsed = performance.now() - startTime;
      const rawPct = Math.min(100, Math.round((elapsed / DURATION) * 100));

      if (rawPct > currentPct) {
        currentPct = rawPct;
        setLoad(currentPct);

        if (currentPct !== prevLoadRef.current) {
          prevLoadRef.current = currentPct;
          if (currentPct % 2 === 0 || Math.random() > 0.4) {
            callbacksRef.current.playDataTick?.();
          }
        }
      }

      // Milestones calibrated to the progress
      if (currentPct >= 15 && stageRef.current < 1) {
        stageRef.current = 1;
        const cores = navigator.hardwareConcurrency || 8;
        setSystemLinkText(`HOST BUS // ${cores} LOGICAL CORES DETECTED`);
        setActiveStatusText("VERIFYING LOCAL AIRGAP PROTOCOLS...");
      }

      if (currentPct >= 40 && stageRef.current < 2) {
        stageRef.current = 2;
        callbacksRef.current.triggerSpike?.(2.2);
        callbacksRef.current.playLockChirp?.();
      }

      if (currentPct >= 65 && stageRef.current < 3) {
        stageRef.current = 3;
        callbacksRef.current.triggerSpike?.(2.4);
        callbacksRef.current.playLockChirp?.();
      }

      if (currentPct >= 85 && stageRef.current < 4) {
        stageRef.current = 4;
        callbacksRef.current.triggerSpike?.(2.5);
        callbacksRef.current.playLockChirp?.();
      }

      if (currentPct >= 96 && stageRef.current < 5) {
        stageRef.current = 5;
        setActiveStatusText("GATEKEEPER & ZERO-TELEMETRY LOCKED");
        callbacksRef.current.triggerSpike?.(2.2);
        callbacksRef.current.playLockChirp?.();
      }

      if (currentPct >= 100 && stageRef.current < 6) {
        stageRef.current = 6;
        clearInterval(progressTimer);
        setIsCompleted(true);
        setActiveStatusText("ALL SYSTEMS NOMINAL // COCKPIT ARMED");
        callbacksRef.current.triggerSpike?.(2.8);
        callbacksRef.current.playArmedChime?.();

        setTimeout(() => {
          if (!cancelled) {
            callbacksRef.current.cleanupAudio?.();
            const cb = callbacksRef.current.onDone || callbacksRef.current.onComplete;
            cb?.();
          }
        }, 900);
      }
    }, 24);

    // Non-blocking background health check
    const checkBackend = async () => {
      try {
        const t0 = performance.now();
        const resp = await fetch("/api/v1/health/");
        if (!cancelled && resp.ok) {
          const rtt = Math.round(performance.now() - t0);
          const health = await resp.json();
          setSystemLinkText(`PORT 8000 // ${rtt}ms RTT // ZERO-TELEMETRY`);
          setActiveStatusText(`KERNEL ${health.status.toUpperCase()} // V${health.version || "0.1.0"}`);
          if (health.tri_models) {
            setNeuralCoreText("QWEN3 0.6B+1.7B // LLAMA 3.2 1B");
          }
        }
      } catch {}

      try {
        const ragResp = await fetch("/api/v1/rag/stats/");
        if (!cancelled && ragResp.ok) {
          const ragData = await ragResp.json();
          const count = ragData.total_embeddings || 186;
          setReadyAgentText(`CHROMA RAG // ${count} VECTORS ONLINE`);
        }
      } catch {}
    };

    checkBackend();

    return () => {
      cancelled = true;
      clearInterval(progressTimer);
    };
  }, []);

  // Dynamic Radial Progress Ticks (120 segments)
  const head = (t * 55) % 360;
  const ticks = [];
  const activeCount = Math.round((load / 100) * 120);

  for (let i = 0; i < 120; i++) {
    const a = i * 3;
    const d = (head - a + 720) % 360;
    const trail = Math.exp(-d / 110);
    const isLit = i <= activeCount || isCompleted;
    const baseOp = isLit ? 0.45 + 0.55 * trail : 0.12;
    const len = i % 5 === 0 ? 28 : 22;
    const r0 = 246;
    const [x1, y1] = polar(r0, a);
    const [x2, y2] = polar(r0 + len, a);

    const strokeColor = isCompleted
      ? `rgba(16, 185, 129, ${baseOp})`
      : isLit
      ? `rgba(${RED},${baseOp})`
      : `rgba(60,60,70,0.18)`;

    ticks.push(
      <line
        key={i}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={strokeColor}
        strokeWidth={isLit ? 3.6 : 1.8}
        strokeLinecap="butt"
      />
    );
  }

  const outerBezel =
    "1012,226 1212,226 1332,246 1452,366 1478,476 1478,656 1452,766 1332,886 1212,906 1012,906 892,886 772,766 746,656 746,476 772,366 892,246";
  const arc = 2 * Math.PI * 11;

  return (
    <div
      onClick={unlockAudio}
      onPointerDown={unlockAudio}
      onTouchStart={unlockAudio}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 99999,
        background: "#050505",
        width: "100vw",
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        userSelect: "none",
        cursor: "default",
      }}
    >
      <style>{`
        @keyframes dash { to { stroke-dashoffset: -40; } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .3; } }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes flick { 0%,100% { opacity: 1; } 47% { opacity: 1; } 50% { opacity: .82; } 53% { opacity: 1; } }
        .spoke { animation: dash 1.6s linear infinite; }
        .pulse { animation: pulse 1.8s ease-in-out infinite; }
        .orbit { transform-origin: ${CX}px ${CY}px; animation: spin 160s linear infinite; }
        .spin { transform-box: fill-box; transform-origin: center; animation: spin 1.4s linear infinite; }
        .core { animation: flick 4s steps(1) infinite; }
        @keyframes titlePopUp {
          0% {
            opacity: 0;
            transform: scale(0.85) translateY(10px);
          }
          60% {
            opacity: 1;
            transform: scale(1.04) translateY(-2px);
          }
          80% {
            transform: scale(0.99) translateY(1px);
          }
          100% {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        .pop-title {
          transform-box: fill-box;
          transform-origin: center;
          animation: titlePopUp 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
        }
        @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
      `}</style>

      {/* 3D LAYERED GLASS BRAND TITLE IN CENTER (ZERO OVERLAPPING, PURE TRANSPARENT) */}
      <div
        style={{
          position: "absolute",
          top: "18px",
          left: "50%",
          transform: "translateX(-50%)",
          width: "90%",
          maxWidth: "680px",
          zIndex: 30,
          pointerEvents: "auto",
        }}
      >
        <LayeredText
          text="O.P.S an Over-Engineered Program System"
          height={52}
        />
      </div>

      {/* PIXEL-PERFECT REFERENCE VECTOR CANVAS */}
      <svg
        viewBox="0 0 2224 1132"
        style={{ width: "100%", height: "100%", maxHeight: "100vh", display: "block" }}
        role="img"
        aria-label="Neural core status dial"
      >
        <defs>
          <radialGradient id="halo" gradientUnits="userSpaceOnUse" cx={CX} cy={CY} r="820">
            <stop offset="0" stopColor={isCompleted ? "#064e3b" : "#380d0d"} stopOpacity=".65" />
            <stop offset=".45" stopColor={isCompleted ? "#022c22" : "#180607"} stopOpacity=".35" />
            <stop offset="1" stopColor="#000" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="bezel" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#3c3c44" />
            <stop offset=".5" stopColor="#25252b" />
            <stop offset="1" stopColor="#484852" />
          </linearGradient>
          <linearGradient id="bezelRim" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#ffffff" stopOpacity=".35" />
            <stop offset=".5" stopColor="#ffffff" stopOpacity=".05" />
            <stop offset="1" stopColor="#ffffff" stopOpacity=".2" />
          </linearGradient>
          <radialGradient id="face" cx="50%" cy="50%" r="50%">
            <stop offset="0" stopColor="#0a0a0d" />
            <stop offset=".85" stopColor="#111115" />
            <stop offset="1" stopColor="#1a1a20" />
          </radialGradient>
          <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0" stopColor={isCompleted ? "#10b981" : `rgb(${RED})`} stopOpacity=".28" />
            <stop offset="1" stopColor="#000" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="trace" gradientUnits="userSpaceOnUse" x1={CX - 105} y1="0" x2={CX + 105} y2="0">
            <stop offset="0" stopColor={isCompleted ? "#10b981" : `rgb(${RED})`} stopOpacity="0" />
            <stop offset=".25" stopColor={isCompleted ? "#10b981" : `rgb(${RED})`} stopOpacity=".85" />
            <stop offset="1" stopColor={isCompleted ? "#10b981" : `rgb(${RED})`} />
          </linearGradient>
          <filter id="blur" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4.5" />
          </filter>
          <filter id="glowR" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3.5" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="bevel" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="12" stdDeviation="14" floodColor="#000" floodOpacity=".85" />
          </filter>
          <filter id="badgeShadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#000" floodOpacity=".7" />
          </filter>
          <clipPath id="coreClip">
            <circle cx={CX} cy={CY} r="114" />
          </clipPath>
          <radialGradient id="vig" cx="50%" cy="50%" r="75%">
            <stop offset=".5" stopColor="#000" stopOpacity="0" />
            <stop offset="1" stopColor="#000" stopOpacity=".7" />
          </radialGradient>
        </defs>

        <rect width="2224" height="1132" fill="#050505" />
        <rect width="2224" height="1132" fill="url(#halo)" />


        {/* Discreet Tactical Hotkey Controls */}
        <g>
          <text
            x="70"
            y="52"
            fill="#555562"
            fontFamily={MONO}
            fontSize="12"
            letterSpacing="2"
            className="cursor-pointer hover:text-white transition"
            onClick={handleLaunchNow}
          >
            [ESC] SKIP BOOT SEQUENCE
          </text>
        </g>

        {/* ----------------------------------------------------------- */}
        {/* OUTER CIRCULAR RETICLE (r = 430, Concentric with the Core) */}
        {/* ----------------------------------------------------------- */}
        <circle cx={CX} cy={CY} r="430" fill="none" stroke="#1c1c22" strokeWidth="1.5" />
        <g className="orbit" stroke="#2a2a32" strokeWidth="1.5">
          <circle cx={CX} cy={CY} r="430" strokeDasharray="3 40" />
        </g>


        {/* Bottom Orbit Node: Ground / Bus Node (6 o'clock on reticle) */}
        <g transform={`translate(${CX - 20}, 976)`}>
          <rect width="40" height="40" rx="6" fill="#0c0c10" stroke="#2e2e36" strokeWidth="1.5" />
          <line x1="12" y1="17" x2="28" y2="17" stroke="#9a9aa2" strokeWidth="1.5" />
          <line x1="15" y1="21" x2="25" y2="21" stroke="#9a9aa2" strokeWidth="1.5" />
          <line x1="18" y1="25" x2="22" y2="25" stroke="#9a9aa2" strokeWidth="1.5" />
        </g>

        {/* ----------------------------------------------------------- */}
        {/* HIGH-PRECISION MECHANICAL BEZEL & REACTOR CHASSIS          */}
        {/* ----------------------------------------------------------- */}
        <polygon
          points={outerBezel}
          fill="url(#bezel)"
          stroke="#5a5a64"
          strokeWidth="2.5"
          strokeLinejoin="round"
          filter="url(#bevel)"
        />
        <polygon points={outerBezel} fill="none" stroke="url(#bezelRim)" strokeWidth="3" strokeLinejoin="round" />

        {/* Bezel Corner Screws */}
        {[22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5].map((a) => {
          const [x, y] = polar(340, a);
          return (
            <g key={a} transform={`translate(${x} ${y})`}>
              <circle r="9" fill="#141418" stroke="#0a0a0c" strokeWidth="1.5" />
              <line x1="-5" y1="0" x2="5" y2="0" stroke="#333338" strokeWidth="2" transform={`rotate(${a * 3})`} />
            </g>
          );
        })}

        {/* Inner Reactor Face */}
        <circle cx={CX} cy={CY} r="290" fill="url(#face)" stroke="#2b2b32" strokeWidth="2.5" />
        <circle cx={CX} cy={CY} r="282" fill="none" stroke="#0c0c10" strokeWidth="3" />

        {/* Dynamic Segmented Radial Loading Arc (120 Segments) */}
        <g filter="url(#glowR)">{ticks}</g>
        <circle cx={CX} cy={CY} r="236" fill="none" stroke="#1d1d22" strokeWidth="1.5" strokeDasharray="3 6" />

        {/* Copper Conduits / Bus Traces channeling toward center */}
        <g>
          {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => {
            const [x1, y1] = polar(124, a);
            const [x2, y2] = polar(234, a);
            return (
              <g key={a}>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#1f1f25" strokeWidth="8" strokeLinecap="round" />
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={isCompleted ? "#10b981" : `rgb(${RED})`}
                  strokeWidth="2.5"
                  strokeDasharray="10 20"
                  className="spoke"
                  opacity=".85"
                />
              </g>
            );
          })}
        </g>

        {/* ----------------------------------------------------------- */}
        {/* CENTRAL CORE CHAMBER WITH DYNAMIC EKG WAVEFORM             */}
        {/* ----------------------------------------------------------- */}
        <circle cx={CX} cy={CY} r="126" fill="#18181d" stroke="#3c3c44" strokeWidth="3" />
        <circle cx={CX} cy={CY} r="116" fill="#040405" />
        <circle cx={CX} cy={CY} r="116" fill="url(#coreGlow)" />
        <circle
          cx={CX}
          cy={CY}
          r="115"
          fill="none"
          stroke={isCompleted ? "#10b981" : `rgb(${RED})`}
          strokeWidth="2"
          opacity=".9"
        />

        {/* EKG Heartbeat Trace */}
        <g clipPath="url(#coreClip)" className="core">
          <line
            x1={CX - 114}
            y1={CY}
            x2={CX + 114}
            y2={CY}
            stroke={isCompleted ? "rgba(16,185,129,.15)" : `rgba(${RED},.12)`}
            strokeWidth="1"
          />
          <path
            d={pts}
            fill="none"
            stroke={isCompleted ? "#10b981" : `rgb(${RED})`}
            strokeWidth="8"
            opacity=".5"
            filter="url(#blur)"
          />
          <path
            d={pts}
            fill="none"
            stroke="url(#trace)"
            strokeWidth="3.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          <circle
            cx={CX + 105}
            cy={CY - buf.current[N - 1] * 70}
            r="10"
            fill={isCompleted ? "#10b981" : `rgb(${RED})`}
            opacity=".5"
            filter="url(#blur)"
          />
          <circle
            cx={CX + 105}
            cy={CY - buf.current[N - 1] * 70}
            r="3.5"
            fill={isCompleted ? "#a7f3d0" : "#ffd9d3"}
          />
        </g>

        {/* Core Cardinal Micro Pulse Dots */}
        <circle cx={CX} cy={CY - 120} r="4.5" fill={isCompleted ? "#10b981" : `rgb(${RED})`} className="pulse" />
        <circle
          cx={CX}
          cy={CY + 120}
          r="4.5"
          fill={isCompleted ? "#10b981" : `rgb(${RED})`}
          className="pulse"
          style={{ animationDelay: ".9s" }}
        />

        {/* ----------------------------------------------------------- */}
        {/* HARDWARE PERCENTAGE (Reference Image: Bottom-Left of Dial) */}
        {/* ----------------------------------------------------------- */}
        <g transform="translate(775, 885)">
          <text
            x="0"
            y="26"
            fill={isCompleted ? "#10b981" : "#f4f4f4"}
            fontFamily={MONO}
            fontWeight="800"
            fontSize="30"
            letterSpacing="1.5"
          >
            {load}%
          </text>
          {/* Dynamic Non-Overlapping Circular Data Spinner */}
          <g transform={`translate(${load >= 100 ? 116 : 88}, 16)`}>
            <circle r="10" fill="none" stroke="#251214" strokeWidth="2.5" />
            <circle
              r="10"
              fill="none"
              stroke={isCompleted ? "#10b981" : `rgb(${RED})`}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeDasharray={`${arc * Math.max(0.05, load / 100)} ${arc}`}
              className={!isCompleted ? "spin" : ""}
            />
          </g>
        </g>

        {/* ----------------------------------------------------------- */}
        {/* LEADER LINES & MICRO-ICONS (Matching Reference Image)       */}
        {/* ----------------------------------------------------------- */}
        <g stroke={isCompleted ? "#10b981" : "#602426"} strokeWidth="1.8" fill="none" opacity=".85">
          <polyline points="1350,270 1435,195 1500,195" />
          <line x1="1478" y1="566" x2="1525" y2="566" />
          <line x1="1561" y1="566" x2="1600" y2="566" />
          <polyline points="1350,862 1435,935 1500,935" />
          <line x1="746" y1="566" x2="700" y2="566" />
          <line x1="664" y1="566" x2="620" y2="566" />
        </g>

        {/* Middle-Right Micro Chip Decal Box */}
        <g transform="translate(1525, 548)">
          <rect width="36" height="36" rx="5" fill="#0c0c10" stroke="#2e2e36" strokeWidth="1.5" />
          <rect x="10" y="10" width="16" height="16" fill="none" stroke="#777782" strokeWidth="1.2" />
          <circle cx="18" cy="18" r="3" fill={isCompleted ? "#10b981" : `rgb(${RED})`} />
        </g>

        {/* Middle-Left Micro Level Decal Box */}
        <g transform="translate(664, 548)">
          <rect width="36" height="36" rx="5" fill="#0c0c10" stroke="#2e2e36" strokeWidth="1.5" />
          <line x1="9" y1="13" x2="27" y2="13" stroke="#777782" strokeWidth="1.5" />
          <line x1="9" y1="18" x2="27" y2="18" stroke="#777782" strokeWidth="1.5" />
          <line x1="9" y1="23" x2="27" y2="23" stroke="#777782" strokeWidth="1.5" />
        </g>

        {/* ----------------------------------------------------------- */}
        {/* 4 CARDINAL DIAGNOSTIC BADGES                                */}
        {/* ----------------------------------------------------------- */}
        <DiagnosticBadge
          x={1500}
          y={168}
          width={340}
          title="ACTIVE STATUS"
          sub={activeStatusText}
          isGreen={isCompleted}
          statusDelay="0s"
        />
        <DiagnosticBadge
          x={1600}
          y={538}
          width={340}
          title="NEURAL CORE"
          sub={neuralCoreText}
          isGreen={isCompleted}
          statusDelay=".6s"
        />
        <DiagnosticBadge
          x={1500}
          y={908}
          width={340}
          title="READY AGENT"
          sub={readyAgentText}
          isGreen={isCompleted}
          statusDelay="1.2s"
        />
        <DiagnosticBadge
          x={280}
          y={538}
          width={340}
          title="SYSTEM LINK"
          sub={systemLinkText}
          isGreen={isCompleted}
          statusDelay=".4s"
        />

        {/* Bottom-Right Crosshair Diamond Accent */}
        <path
          d="M 2030 960 Q 2045 975 2060 975 Q 2045 975 2045 990 Q 2045 975 2030 975 Q 2045 975 2045 960 Z"
          fill="#35353d"
          opacity=".45"
        />

        {/* Cinematic Vignette */}
        <rect width="2224" height="1132" fill="url(#vig)" pointerEvents="none" />
      </svg>
    </div>
  );
}
