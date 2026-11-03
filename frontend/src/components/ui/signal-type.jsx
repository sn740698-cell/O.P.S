import React, {
  forwardRef,
  useRef,
  useEffect,
  useMemo,
  useId,
  useSyncExternalStore,
  useImperativeHandle,
} from "react";
import { cn } from "../../lib/utils";

// Presets from ReactBits Signal Type
export const SIGNAL_TYPE_PRESETS = {
  signal: { color: "#FFFFFF", glowColor: "#8B5CF6", glow: 0.6, flash: 1 },
  neon: { color: "#FF9FFC", glowColor: "#5227FF", glow: 1.1, flash: 1.2 },
  tungsten: { color: "#FFF1DC", glowColor: "#FF7A27", glow: 0.8, flash: 1 },
  ice: { color: "#EAF6FF", glowColor: "#2F6BFF", glow: 0.8, flash: 1 },
  mono: { color: "#FFFFFF", glowColor: "#FFFFFF", glow: 0, flash: 0.5 },
  ink: { color: "#0A0A0A", glowColor: "#8B5CF6", glow: 0, flash: 0.3 },
  violet: { color: "#5227FF", glowColor: "#B19EEF", glow: 0.5, flash: 0.7 },
  ops: { color: "#FF6B6B", glowColor: "#EF4444", glow: 1.0, flash: 1.3 },
};

const clamp = (val, min, max) => Math.min(max, Math.max(min, val));

// Deterministic PRNG
const createPrng = (seed) => {
  let t = (0x5bd1e995 ^ Math.floor(7919 * seed)) >>> 0;
  return () => {
    let e = (t = (t + 0x6d2b79f5) >>> 0);
    e = Math.imul(e ^ (e >>> 15), 1 | e);
    return (
      (((e ^= e + Math.imul(e ^ (e >>> 7), 61 | e)) ^ (e >>> 14)) >>> 0) /
      0x100000000
    );
  };
};

const subscribeReducedMotion = (cb) => {
  if (typeof window === "undefined") return () => {};
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
};

const getReducedMotionSnapshot = () => {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
};

const calcGlowAlpha = (glow) => clamp(0.45 * glow, 0, 1);

const srOnlyStyle = {
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0, 0, 0, 0)",
  whiteSpace: "nowrap",
  border: 0,
};

const hiddenSvgStyle = {
  position: "absolute",
  width: 0,
  height: 0,
  overflow: "hidden",
  pointerEvents: "none",
};

const spaceStyle = { whiteSpace: "pre-wrap" };
const wordStyle = { display: "inline-block", whiteSpace: "nowrap" };
const glyphWrapperStyle = { position: "relative", display: "inline-block" };
const layerAbsoluteStyle = {
  position: "absolute",
  inset: 0,
  pointerEvents: "none",
  userSelect: "none",
  WebkitUserSelect: "none",
};

// Generates ignition flicker timeline
const generateIgniteTimeline = (prng, startTime, flickerCount, speed) => {
  const timeline = [];
  let currentTime = startTime;
  const count = Math.round(flickerCount * (0.4 + 0.9 * prng()));
  for (let i = 0; i < count; i++) {
    const onDuration = (0.02 + 0.06 * prng()) / speed;
    const offDuration = (0.035 + 0.13 * prng()) / speed;
    const level = prng() < 0.3 ? 0.28 + 0.32 * prng() : 0.7 + 0.3 * prng();
    timeline.push({ at: currentTime, level, flash: 0.55 });
    timeline.push({ at: currentTime + onDuration, level: 0 });
    currentTime += onDuration + offDuration;
  }
  timeline.push({ at: currentTime, level: 1, flash: 1 });
  return timeline;
};

// Generates click-cycle / instability flicker timeline
const generateCycleTimeline = (prng, speed, isInstability) => {
  const timeline = [];
  let currentTime = 0;
  const burstCount = isInstability
    ? 2 + Math.floor(3 * prng())
    : 1 + Math.floor(2 * prng());
  for (let i = 0; i < burstCount; i++) {
    const dipDuration =
      ((isInstability ? 0.04 : 0.025) +
        prng() * (isInstability ? 0.12 : 0.05)) /
      speed;
    const recoverDuration = (0.02 + 0.05 * prng()) / speed;
    timeline.push({ at: currentTime, level: 0 });
    currentTime += dipDuration;
    const isLast = i === burstCount - 1;
    timeline.push({
      at: currentTime,
      level: isLast ? 1 : prng() < 0.45 ? 0.35 + 0.3 * prng() : 1,
      flash: isLast ? 0.7 : 0.45,
    });
    currentTime += recoverDuration;
  }
  return timeline;
};

/**
 * SignalType — Flickering Neon / Signal Headline Component
 * Official React Bits Pro Implementation
 */
export const SignalType = forwardRef(function SignalType(
  {
    text = "O.P.S AN OVER-ENGINEERED PROGRAM SYSTEM",
    as: Tag = "span",
    preset,
    color,
    glowColor,
    unlit = "outline",
    outlineWidth = 1,
    outlineOpacity = 0.28,
    glow,
    glowSize = 1,
    flash,
    flickers = 3,
    speed = 1,
    stagger = 0.045,
    delay = 0.15,
    order = "random",
    trigger = "view",
    interference = 1,
    interferenceRadius = 90,
    clickCycle = true,
    instability = 0.3,
    loop = false,
    loopDelay = 6,
    seed = 0,
    paused = false,
    onComplete,
    className,
    style,
    children,
  },
  ref
) {
  const displayText = children ? String(children) : text;
  const presetConfig = preset && SIGNAL_TYPE_PRESETS[preset] ? SIGNAL_TYPE_PRESETS[preset] : {};

  const activeColor = color ?? presetConfig.color ?? "currentColor";
  const activeGlowColor = glowColor ?? presetConfig.glowColor ?? "#EF4444";
  const activeGlow = glow ?? presetConfig.glow ?? 0.8;
  const activeFlash = flash ?? presetConfig.flash ?? 1.1;

  const containerRef = useRef(null);
  const controllerRef = useRef(null);
  const rawId = useId();
  const filterId = `signal-outline-${rawId.replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const isReducedMotion = useSyncExternalStore(
    subscribeReducedMotion,
    getReducedMotionSnapshot,
    () => false
  );
  const isDisabled = isReducedMotion || paused;

  // Segment words and graphemes safely
  const parsedWords = useMemo(() => {
    return displayText
      .split(/(\s+)/)
      .filter((w) => w.length > 0)
      .map((w) => ({
        value: w,
        space: /^\s+$/.test(w),
        glyphs:
          typeof Intl === "undefined" || !Intl.Segmenter
            ? Array.from(w)
            : Array.from(
                new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(w),
                (s) => s.segment
              ),
      }));
  }, [displayText]);

  const configRef = useRef({
    glow: activeGlow,
    flash: activeFlash,
    flickers,
    speed,
    stagger,
    delay,
    order,
    trigger,
    interference,
    interferenceRadius,
    clickCycle,
    instability,
    loop,
    loopDelay,
    seed,
    onComplete,
  });

  useEffect(() => {
    configRef.current = {
      glow: activeGlow,
      flash: activeFlash,
      flickers,
      speed,
      stagger,
      delay,
      order,
      trigger,
      interference,
      interferenceRadius,
      clickCycle,
      instability,
      loop,
      loopDelay,
      seed,
      onComplete,
    };
  });

  useEffect(() => {
    const el = containerRef.current;
    if (!el || isDisabled) return;

    const glyphNodes = Array.from(
      el.querySelectorAll("[data-signal-glyph]")
    ).map((node) => ({
      node,
      base: node.querySelector("[data-signal-base]"),
      fill: node.querySelector("[data-signal-fill]"),
      glow: node.querySelector("[data-signal-glow]"),
      level: 0,
      busyUntil: 0,
      x: 0,
      y: 0,
    }));

    const timeouts = new Set();
    const prng = Math.random;
    let needsPositionUpdate = true;
    let isLit = false;
    let isIntersecting = false;
    let lastPointerX = 0;
    let lastPointerY = 0;
    let lastPointerTime = 0;
    let instabilityTimer = 0;

    const schedule = (fn, sec) => {
      const id = window.setTimeout(() => {
        timeouts.delete(id);
        fn();
      }, Math.max(0, 1000 * sec));
      timeouts.add(id);
    };

    const updatePositions = () => {
      if (needsPositionUpdate) {
        needsPositionUpdate = false;
        for (const g of glyphNodes) {
          const rect = g.node.getBoundingClientRect();
          g.x = rect.left + rect.width / 2;
          g.y = rect.top + rect.height / 2;
        }
      }
    };

    const applyTimeline = (glyph, timeline, settleDuration = 0.45) => {
      if (timeline.length === 0) return 0;
      const cfg = configRef.current;
      const glowFactor = calcGlowAlpha(cfg.glow);
      const flashFactor = clamp(cfg.flash, 0, 3);
      const currentFillOpacity =
        Number.parseFloat(getComputedStyle(glyph.fill).opacity) || 0;
      const currentGlowOpacity =
        Number.parseFloat(getComputedStyle(glyph.glow).opacity) || 0;

      for (const target of [glyph.base, glyph.fill, glyph.glow]) {
        target.getAnimations().forEach((a) => a.cancel());
      }

      const finalLevel = timeline[timeline.length - 1].level;
      const totalDuration = Math.max(
        timeline[timeline.length - 1].at + (finalLevel > 0 ? settleDuration : 0.05),
        0.05
      );

      // Interpolate fill opacity keyframes
      const fillKeyframes = [{ opacity: currentFillOpacity, offset: 0 }];
      let lastVal = currentFillOpacity;
      for (const step of timeline) {
        const t = clamp(step.at / totalDuration, 0, 1);
        fillKeyframes.push({ opacity: lastVal, offset: t });
        fillKeyframes.push({ opacity: step.level, offset: t });
        lastVal = step.level;
      }
      fillKeyframes.push({ opacity: lastVal, offset: 1 });

      glyph.base.style.opacity = String(1 - finalLevel);
      glyph.fill.style.opacity = String(finalLevel);
      glyph.glow.style.opacity = String(finalLevel * glowFactor);

      glyph.base.animate(
        fillKeyframes.map((k) => ({ ...k, opacity: 1 - Number(k.opacity) })),
        { duration: 1000 * totalDuration, easing: "linear" }
      );
      glyph.fill.animate(fillKeyframes, {
        duration: 1000 * totalDuration,
        easing: "linear",
      });

      // Compute glow keyframes with phosphor decay
      const glowKeyframes = [{ opacity: currentGlowOpacity, offset: 0 }];
      let prevGlow = currentGlowOpacity;
      timeline.forEach((step, idx) => {
        const nextTime =
          idx + 1 < timeline.length ? timeline[idx + 1].at : totalDuration;
        const offset = clamp(step.at / totalDuration, 0, 1);
        glowKeyframes.push({ opacity: prevGlow, offset });

        if (step.level <= 0) {
          glowKeyframes.push({ opacity: 0, offset });
          prevGlow = 0;
          return;
        }

        const steadyGlow = step.level * glowFactor;
        const peakGlow = clamp(
          steadyGlow + step.level * flashFactor * 0.55 * (step.flash ?? 1),
          0,
          1
        );
        glowKeyframes.push({ opacity: peakGlow, offset });
        prevGlow = peakGlow;

        for (const dt of [0.03, 0.07, 0.13, 0.22, 0.36]) {
          if (step.at + dt >= nextTime) break;
          prevGlow = steadyGlow + (peakGlow - steadyGlow) * Math.exp(-dt / 0.09);
          glowKeyframes.push({
            opacity: prevGlow,
            offset: clamp((step.at + dt) / totalDuration, 0, 1),
          });
        }
      });

      const lastStep = timeline[timeline.length - 1];
      glowKeyframes.push({
        opacity: lastStep ? lastStep.level * glowFactor : prevGlow,
        offset: 1,
      });

      glyph.glow.animate(glowKeyframes, {
        duration: 1000 * totalDuration,
        easing: "linear",
      });

      glyph.level = finalLevel;
      glyph.busyUntil = performance.now() + 1000 * totalDuration;
      return totalDuration;
    };

    const getOrderRanks = (cfg) => {
      const len = glyphNodes.length;
      if (cfg.order === "random") {
        const prngGen = createPrng(cfg.seed + 0.37);
        const indices = glyphNodes.map((_, i) => i);
        for (let i = indices.length - 1; i > 0; i--) {
          const j = Math.floor(prngGen() * (i + 1));
          [indices[i], indices[j]] = [indices[j], indices[i]];
        }
        const ranks = Array(len);
        indices.forEach((val, i) => {
          ranks[val] = i;
        });
        return ranks;
      }
      return glyphNodes.map((_, i) =>
        cfg.order === "end"
          ? len - 1 - i
          : cfg.order === "center"
          ? Math.abs(i - (len - 1) / 2)
          : i
      );
    };

    const scheduleInstability = () => {
      window.clearTimeout(instabilityTimer);
      const cfg = configRef.current;
      if (cfg.instability <= 0) return;
      const waitSec =
        -Math.log(1 - prng()) * (5 / clamp(cfg.instability, 0.05, 3));
      instabilityTimer = window.setTimeout(() => {
        const now = performance.now();
        if (isLit && isIntersecting && document.visibilityState === "visible") {
          const available = glyphNodes.filter(
            (g) => g.level >= 1 && g.busyUntil < now
          );
          const target = available[Math.floor(prng() * available.length)];
          if (target) {
            applyTimeline(target, generateCycleTimeline(prng, cfg.speed, true), 0.3);
          }
        }
        scheduleInstability();
      }, 1000 * waitSec);
    };

    const ignite = () => {
      const cfg = configRef.current;
      const seedPrng = createPrng(cfg.seed);
      const ranks = getOrderRanks(cfg);
      const effectiveSpeed = clamp(cfg.speed, 0.1, 5);
      const effectiveStagger = clamp(cfg.stagger, 0, 1);
      let maxDuration = 0;
      isLit = true;

      glyphNodes.forEach((glyph, i) => {
        const delaySec =
          clamp(cfg.delay, 0, 30) +
          ranks[i] * effectiveStagger +
          seedPrng() * effectiveStagger * 0.8;
        maxDuration = Math.max(
          maxDuration,
          applyTimeline(
            glyph,
            generateIgniteTimeline(
              seedPrng,
              delaySec,
              clamp(cfg.flickers, 0, 12),
              effectiveSpeed
            )
          )
        );
      });

      schedule(() => {
        configRef.current.onComplete?.();
        if (configRef.current.loop) {
          schedule(() => cycle(), clamp(configRef.current.loopDelay, 0.5, 60));
        }
      }, maxDuration);
    };

    const cycle = (originX, originY) => {
      const cfg = configRef.current;
      const seedPrng = createPrng(cfg.seed + performance.now());
      const effectiveSpeed = clamp(cfg.speed, 0.1, 5);
      updatePositions();
      const startX = originX ?? (glyphNodes[0]?.x ?? 0) - 1;
      const startY = originY ?? glyphNodes[0]?.y ?? 0;
      let maxDuration = 0;
      isLit = true;

      glyphNodes.forEach((glyph) => {
        const distDelay =
          Math.hypot(glyph.x - startX, glyph.y - startY) / 1600 / effectiveSpeed;
        const initialDelay = (0.12 + 0.22 * seedPrng()) / effectiveSpeed;
        const timeline = [
          { at: distDelay, level: 0 },
          ...generateIgniteTimeline(
            seedPrng,
            distDelay + initialDelay,
            0.7 * clamp(cfg.flickers, 0, 12),
            effectiveSpeed
          ),
        ];
        maxDuration = Math.max(maxDuration, applyTimeline(glyph, timeline));
      });

      schedule(() => {
        if (configRef.current.loop) {
          schedule(() => cycle(), clamp(configRef.current.loopDelay, 0.5, 60));
        }
      }, maxDuration);
    };

    const powerDown = () => {
      const cfg = configRef.current;
      const seedPrng = createPrng(cfg.seed + 11.3);
      const ranks = getOrderRanks(cfg);
      const effectiveSpeed = clamp(cfg.speed, 0.1, 5);
      const effectiveStagger = 0.5 * clamp(cfg.stagger, 0, 1);
      isLit = false;

      glyphNodes.forEach((glyph, i) => {
        const delaySec = ranks[i] * effectiveStagger + seedPrng() * effectiveStagger;
        applyTimeline(
          glyph,
          seedPrng() < 0.5
            ? [
                { at: delaySec, level: 0 },
                { at: delaySec + 0.05 / effectiveSpeed, level: 0.45, flash: 0.3 },
                { at: delaySec + 0.09 / effectiveSpeed, level: 0 },
              ]
            : [{ at: delaySec, level: 0 }]
        );
      });
    };

    const handlePointerMove = (evt) => {
      const cfg = configRef.current;
      const now = performance.now();
      const dt = Math.max((now - lastPointerTime) / 1000, 1 / 240);
      const velocity =
        lastPointerTime > 0
          ? Math.hypot(evt.clientX - lastPointerX, evt.clientY - lastPointerY) / dt
          : 0;
      lastPointerX = evt.clientX;
      lastPointerY = evt.clientY;
      lastPointerTime = now;

      if (!isLit || cfg.interference <= 0 || evt.pointerType === "touch") return;
      updatePositions();
      const radius = Math.max(cfg.interferenceRadius, 4);

      for (const glyph of glyphNodes) {
        if (glyph.level < 1 || glyph.busyUntil > now) continue;
        const dist = Math.hypot(glyph.x - lastPointerX, glyph.y - lastPointerY) / radius;
        if (dist >= 1) continue;
        const decay = (1 - dist) * (1 - dist);
        const chance =
          cfg.interference * decay * clamp(velocity / 900, 0, 1.6) * 0.35;
        if (prng() < chance) {
          applyTimeline(
            glyph,
            generateCycleTimeline(prng, cfg.speed, false),
            0.3
          );
        }
      }
    };

    const handlePointerEnter = () => {
      needsPositionUpdate = true;
      lastPointerTime = 0;
      if (configRef.current.trigger === "hover") ignite();
    };

    const handlePointerLeave = () => {
      lastPointerTime = 0;
      if (configRef.current.trigger === "hover") powerDown();
    };

    const handlePointerDown = (evt) => {
      if (configRef.current.clickCycle && isLit) {
        needsPositionUpdate = true;
        cycle(evt.clientX, evt.clientY);
      }
    };

    const handleLayoutInvalidation = () => {
      needsPositionUpdate = true;
    };

    const observer =
      typeof IntersectionObserver === "undefined"
        ? null
        : new IntersectionObserver(
            ([entry]) => {
              isIntersecting = entry.isIntersecting;
              if (
                isIntersecting &&
                !isLit &&
                configRef.current.trigger === "view"
              ) {
                ignite();
              }
            },
            { threshold: 0.25 }
          );

    observer?.observe(el);
    if (!observer) isIntersecting = true;

    el.addEventListener("pointermove", handlePointerMove, { passive: true });
    el.addEventListener("pointerenter", handlePointerEnter, { passive: true });
    el.addEventListener("pointerleave", handlePointerLeave, { passive: true });
    el.addEventListener("pointerdown", handlePointerDown, { passive: true });
    window.addEventListener("scroll", handleLayoutInvalidation, {
      passive: true,
      capture: true,
    });
    window.addEventListener("resize", handleLayoutInvalidation, { passive: true });

    const currentTrigger = configRef.current.trigger;
    if (currentTrigger === "mount" || (!observer && currentTrigger === "view")) {
      ignite();
    }

    scheduleInstability();

    const controller = {
      ignite,
      cycle,
      powerDown,
      refresh: () => {
        const glowFactor = calcGlowAlpha(configRef.current.glow);
        const now = performance.now();
        for (const g of glyphNodes) {
          if (g.busyUntil < now) {
            g.glow.style.opacity = String(g.level * glowFactor);
          }
        }
      },
      destroy: () => {
        observer?.disconnect();
        window.clearTimeout(instabilityTimer);
        timeouts.forEach((id) => window.clearTimeout(id));
        timeouts.clear();
        el.removeEventListener("pointermove", handlePointerMove);
        el.removeEventListener("pointerenter", handlePointerEnter);
        el.removeEventListener("pointerleave", handlePointerLeave);
        el.removeEventListener("pointerdown", handlePointerDown);
        window.removeEventListener("scroll", handleLayoutInvalidation, {
          capture: true,
        });
        window.removeEventListener("resize", handleLayoutInvalidation);
        for (const g of glyphNodes) {
          for (const target of [g.base, g.fill, g.glow]) {
            target.getAnimations().forEach((a) => a.cancel());
          }
        }
      },
    };

    controllerRef.current = controller;
    return () => {
      controller.destroy();
      if (controllerRef.current === controller) controllerRef.current = null;
    };
  }, [displayText, isDisabled]);

  useEffect(() => {
    controllerRef.current?.refresh();
  }, [activeGlow]);

  useImperativeHandle(
    ref,
    () => ({
      ignite: () => controllerRef.current?.ignite(),
      cycle: () => controllerRef.current?.cycle(),
      powerDown: () => controllerRef.current?.powerDown(),
    }),
    []
  );

  const ghostFillColor = `color-mix(in srgb, ${activeColor} ${Math.round(
    100 * clamp(outlineOpacity, 0, 1)
  )}%, transparent)`;

  const normalizedGlowSize = clamp(glowSize, 0, 4);

  const baseLayerStyle =
    unlit === "outline"
      ? {
          WebkitTextFillColor: "#000",
          filter: `url(#${filterId})`,
          opacity: isDisabled ? 0 : 1,
        }
      : {
          WebkitTextFillColor:
            unlit === "dim" ? ghostFillColor : "transparent",
          opacity: isDisabled ? 0 : 1,
        };

  const glowLayerStyle = {
    ...layerAbsoluteStyle,
    WebkitTextFillColor: "transparent",
    textShadow: `0 0 ${(0.05 * normalizedGlowSize).toFixed(3)}em ${activeGlowColor}, 0 0 ${(
      0.24 * normalizedGlowSize
    ).toFixed(3)}em ${activeGlowColor}`,
    opacity: isDisabled ? calcGlowAlpha(activeGlow) : 0,
  };

  const is3D = preset === "ops" || preset === "3d" || className?.includes("ops-3d");

  const fillLayerStyle = is3D
    ? {
        ...layerAbsoluteStyle,
        color: "transparent",
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        backgroundImage:
          "linear-gradient(180deg, #ff8a90 0%, #f23a42 16%, #d01a22 44%, #8c0d13 50%, #b5141c 66%, #e0262e 82%, #6a0a0f 100%)",
        WebkitTextStroke: "1px rgba(255, 180, 180, 0.4)",
        textShadow: `
          0 1px 0 #8f0f15,
          0 2px 0 #7a0c11,
          0 3px 0 #63090d,
          0 4px 0 #4a0609,
          0 5px 6px rgba(0, 0, 0, 0.7),
          0 0 16px rgba(239, 68, 68, 0.6)
        `,
        opacity: isDisabled ? 1 : 0,
      }
    : {
        ...layerAbsoluteStyle,
        color: activeColor,
        opacity: isDisabled ? 1 : 0,
      };

  return (
    <Tag
      ref={containerRef}
      className={cn("relative inline-block select-none", className)}
      style={style}
    >
      {/* Screen-reader friendly text */}
      <span style={srOnlyStyle}>{displayText}</span>

      {/* SVG Outline Morphological Filter */}
      {unlit === "outline" ? (
        <svg
          aria-hidden="true"
          width="0"
          height="0"
          focusable="false"
          style={
            activeColor === "currentColor"
              ? hiddenSvgStyle
              : { ...hiddenSvgStyle, color: activeColor }
          }
        >
          <filter
            id={filterId}
            x="-25%"
            y="-25%"
            width="150%"
            height="150%"
            colorInterpolationFilters="sRGB"
          >
            <feMorphology
              in="SourceAlpha"
              operator="dilate"
              radius={clamp(outlineWidth, 0, 8)}
              result="grown"
            />
            <feComposite
              in="grown"
              in2="SourceAlpha"
              operator="out"
              result="ring"
            />
            <feFlood
              floodColor="currentColor"
              floodOpacity={clamp(outlineOpacity, 0, 1)}
            />
            <feComposite in2="ring" operator="in" />
          </filter>
        </svg>
      ) : null}

      {/* Rendered Glyphs */}
      <span aria-hidden="true">
        {parsedWords.map((word, wIdx) =>
          word.space ? (
            <span key={wIdx} style={spaceStyle}>
              {word.value}
            </span>
          ) : (
            <span key={wIdx} style={wordStyle}>
              {word.glyphs.map((char, cIdx) => (
                <span
                  key={cIdx}
                  style={glyphWrapperStyle}
                  data-signal-glyph=""
                >
                  <span data-signal-base="" style={baseLayerStyle}>
                    {char}
                  </span>
                  <span data-signal-glow="" style={glowLayerStyle}>
                    {char}
                  </span>
                  <span data-signal-fill="" style={fillLayerStyle}>
                    {char}
                  </span>
                </span>
              ))}
            </span>
          )
        )}
      </span>
    </Tag>
  );
});

export default SignalType;
