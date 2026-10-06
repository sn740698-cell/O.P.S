import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

// Pure single-line layered glass 3D text — red / black / grey / white
// Completely transparent, no background box, no grid, zero overlapping.
// Usage: <LayeredText text="O.P.S an Over-Engineered Program System" />

const FONT = "'Arial Black', Impact, sans-serif";

const depthShadow = (steps, blur) =>
  Array.from({ length: steps }, (_, i) => {
    const t = i / Math.max(steps - 1, 1);
    return `0 ${i + 1}px 0 rgb(${Math.round(205 - 155 * t)},${Math.round(18 - 18 * t)},${Math.round(28 - 28 * t)})`;
  }).join(", ") + `, 0 ${blur}px ${blur * 1.2}px rgba(0,0,0,.65)`;

const CSS = `
.lt-pop{display:inline-block;animation:ltPop 0.85s cubic-bezier(.2,1.4,.4,1) both}
@keyframes ltPop{
  0%{opacity:0;transform:translateY(80px) translateZ(-250px) rotateX(65deg) scale(.6)}
  55%{opacity:1}
  75%{transform:translateY(-8px) translateZ(0) rotateX(-4deg) scale(1.04)}
  100%{opacity:1;transform:none}
}
.lt-float{animation:ltFloat 5s ease-in-out 1.8s infinite alternate}
@keyframes ltFloat{from{transform:translateY(0)}to{transform:translateY(-4px)}}

/* smooth glitch: idle most of the loop, then a short eased burst */
.lt-jolt{animation:ltJolt 4.5s ease-in-out 2.6s infinite}
@keyframes ltJolt{
  0%,84%{transform:none}
  87%{transform:skewX(-4deg) translateX(-5px) scaleY(1.01)}
  90%{transform:skewX(3deg) translateX(5px) scaleY(.99)}
  93%{transform:skewX(-1.5deg) translateX(-2px)}
  96%,100%{transform:none}
}
.lt-ghost-r{opacity:0;animation:ltGhostR 4.5s ease-in-out 2.6s infinite}
.lt-ghost-w{opacity:0;animation:ltGhostW 4.5s ease-in-out 2.6s infinite}
@keyframes ltGhostR{
  0%,84%{opacity:0;translate:0 0;clip-path:inset(0 0 100% 0)}
  86%{opacity:.9;translate:-6px 0;clip-path:inset(8% 0 62% 0)}
  89%{translate:7px -2px;clip-path:inset(52% 0 14% 0)}
  92%{translate:-4px 2px;clip-path:inset(28% 0 42% 0)}
  95%{opacity:.6;translate:2px 0;clip-path:inset(0 0 0 0)}
  97%,100%{opacity:0;translate:0 0;clip-path:inset(0 0 100% 0)}
}
@keyframes ltGhostW{
  0%,85%{opacity:0;translate:0 0;clip-path:inset(0 0 100% 0)}
  87%{opacity:.8;translate:6px 1px;clip-path:inset(58% 0 10% 0)}
  90%{translate:-7px -1px;clip-path:inset(12% 0 56% 0)}
  93%{translate:5px 0;clip-path:inset(38% 0 32% 0)}
  96%{opacity:.5;translate:0 0;clip-path:inset(0 0 0 0)}
  98%,100%{opacity:0;clip-path:inset(0 0 100% 0)}
}

.lt-face{
  color:transparent;-webkit-background-clip:text;background-clip:text;
  background-image:linear-gradient(180deg,#ff8a90 0%,#f23a42 16%,#d01a22 44%,#8c0d13 50%,#b5141c 66%,#e0262e 82%,#6a0a0f 100%);
}
.lt-sheen{
  color:transparent;-webkit-background-clip:text;background-clip:text;
  background-image:linear-gradient(110deg,rgba(255,255,255,.12) 35%,rgba(255,255,255,.75) 50%,rgba(255,255,255,.12) 65%);
  background-size:300% 100%;background-position:120% 0;
  animation:ltPop 0.85s cubic-bezier(.2,1.4,.4,1) both, ltSheen 4.5s ease-in-out 2.4s infinite;
}
@keyframes ltSheen{0%{background-position:120% 0}60%,100%{background-position:-20% 0}}
@media (prefers-reduced-motion:reduce){
  .lt-pop,.lt-sheen,.lt-float,.lt-jolt,.lt-ghost-r,.lt-ghost-w{animation:none!important}
  .lt-sheen{background-position:50% 0}
}
`;

function Letters({ text, className = "", baseDelay = 0 }) {
  const step = Math.min(0.08, 1.2 / text.length);
  return text.split("").map((ch, i) => (
    <span
      key={i}
      className={`lt-pop ${className}`}
      style={{ animationDelay: `${baseDelay + i * step}s${className ? ", 2.4s" : ""}` }}
    >
      {ch === " " ? "\u00A0" : ch}
    </span>
  ));
}

const LayeredText = React.memo(function LayeredText({
  text = "O.P.S an Over-Engineered Program System",
  height,
  style = {},
}) {
  const wrapRef = useRef(null);
  const measureRef = useRef(null);
  const stageRef = useRef(null);
  const target = useRef({ x: 0, y: 0, active: false });
  const [fs, setFs] = useState(24);
  const [run, setRun] = useState(0);

  // fit the whole sentence on one line with calibrated font size
  useLayoutEffect(() => {
    const fit = () => {
      if (!wrapRef.current || !measureRef.current) return;
      const w = wrapRef.current.clientWidth * 0.95;
      const unit = (measureRef.current.offsetWidth || 1) / 100;
      setFs(Math.max(14, Math.min(30, w / Math.max(unit, 0.1))));
    };
    fit();
    document.fonts?.ready?.then(fit);
    const ro = new ResizeObserver(fit);
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, [text]);

  // smooth 3D tilt that follows the pointer and eases back to rest
  useEffect(() => {
    let raf,
      cur = { x: 0, y: 0 };
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const tick = () => {
      const tg = target.current;
      const tx = tg.active ? tg.x : 0;
      const ty = tg.active ? tg.y : 0;
      cur.x += (tx - cur.x) * 0.08;
      cur.y += (ty - cur.y) * 0.08;
      if (stageRef.current && !reduce)
        stageRef.current.style.transform = `rotateY(${cur.x}deg) rotateX(${cur.y}deg)`;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    target.current = { x: px * 18, y: -py * 12, active: true };
  };
  const onLeave = () => (target.current.active = false);

  const k = Math.max(0.18, Math.min(0.65, fs / 100));
  const shadow = useMemo(
    () => depthShadow(Math.max(3, Math.round(18 * k)), Math.max(6, Math.round(24 * k))),
    [k]
  );
  const stroke = (px) => `${Math.max(0.8, px * k * 1.5)}px`;
  const off = (x, y) => `${x * k}px ${y * k}px`;

  const layer = (z, extra = {}) => ({
    position: "absolute",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: FONT,
    fontWeight: 900,
    fontStyle: "italic",
    textTransform: "uppercase",
    fontSize: fs,
    letterSpacing: "0.06em",
    wordSpacing: "0.18em",
    lineHeight: 1,
    whiteSpace: "nowrap",
    userSelect: "none",
    transformStyle: "preserve-3d",
    transform: `translateZ(${z}px) skewX(-8deg)`,
    ...extra,
  });

  const H = height || Math.round(fs * 1.8 + 14);

  return (
    <div
      ref={wrapRef}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      onClick={() => setRun((n) => n + 1)}
      style={{
        position: "relative",
        width: "100%",
        height: H,
        background: "transparent",
        overflow: "visible",
        cursor: "pointer",
        perspective: 1200,
        ...style,
      }}
    >
      <style>{CSS}</style>

      {/* hidden ruler used to fit the text to one line */}
      <span
        ref={measureRef}
        aria-hidden
        style={{
          position: "absolute",
          visibility: "hidden",
          whiteSpace: "nowrap",
          fontFamily: FONT,
          fontWeight: 900,
          fontStyle: "italic",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          wordSpacing: "0.18em",
          fontSize: 100,
        }}
      >
        {text}
      </span>

      <div
        key={run}
        ref={stageRef}
        style={{
          position: "relative",
          width: "100%",
          height: H,
          transformStyle: "preserve-3d",
          willChange: "transform",
        }}
      >
        <div className="lt-float" style={{ position: "absolute", inset: 0, transformStyle: "preserve-3d" }}>
          <div className="lt-jolt" style={{ position: "absolute", inset: 0, transformStyle: "preserve-3d" }}>
            {/* blueprint outlines (deep back) */}
            <div
              style={layer(-35, {
                translate: off(-6, 26),
                color: "transparent",
                WebkitTextStroke: `${stroke(1.5)} #fff`,
                opacity: 0.25,
                filter: `blur(${Math.max(0.6, 1.2 * k)}px)`,
              })}
            >
              <Letters text={text} baseDelay={0.3} />
            </div>
            <div
              style={layer(-18, {
                translate: off(-3, 16),
                color: "transparent",
                WebkitTextStroke: `${stroke(1.5)} #fff`,
                opacity: 0.45,
                filter: `blur(${Math.max(0.3, 0.8 * k)}px)`,
              })}
            >
              <Letters text={text} baseDelay={0.18} />
            </div>

            {/* solid extruded red body */}
            <div style={layer(0, { color: "#8f0f15", textShadow: shadow })}>
              <Letters text={text} />
            </div>
            <div style={layer(3, { WebkitTextStroke: `${stroke(1)} rgba(255,160,160,.45)` })}>
              <Letters text={text} className="lt-face" />
            </div>

            {/* grey bevel edge */}
            <div
              style={layer(2, {
                color: "transparent",
                WebkitTextStroke: `${stroke(2.2)} #8c8c8c`,
                opacity: 0.4,
              })}
            >
              <Letters text={text} />
            </div>

            {/* glossy floor reflection - tightly masked */}
            <div
              style={layer(0, {
                transform: `translateZ(0) translateY(${fs * 0.95}px) scaleY(-0.6) skewX(-8deg)`,
                opacity: 0.28,
                filter: "blur(1px)",
                pointerEvents: "none",
                WebkitMaskImage: "linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 70%)",
                maskImage: "linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 70%)",
              })}
            >
              <Letters text={text} className="lt-face" />
            </div>

            {/* glass sheets */}
            <div
              style={layer(40, {
                translate: off(-6, -9),
                color: "rgba(255,255,255,.06)",
                WebkitTextStroke: `${stroke(0.8)} rgba(255,255,255,.28)`,
              })}
            >
              <Letters text={text} baseDelay={0.35} />
            </div>
            <div
              style={layer(24, {
                translate: off(-3, -5),
                color: "rgba(255,255,255,.09)",
                WebkitTextStroke: `${stroke(0.8)} rgba(255,255,255,.32)`,
              })}
            >
              <Letters text={text} baseDelay={0.22} />
            </div>
            <div
              style={layer(12, {
                translate: off(-1, -2),
                WebkitTextStroke: `${stroke(0.8)} rgba(255,255,255,.45)`,
              })}
            >
              <Letters text={text} baseDelay={0.12} className="lt-sheen" />
            </div>

            {/* glitch ghosts: only visible during the glitch burst */}
            <div className="lt-ghost-r" style={layer(20, { color: "#ff1f2d", mixBlendMode: "screen" })}>
              <Letters text={text} />
            </div>
            <div className="lt-ghost-w" style={layer(22, { color: "#e6e6e6", mixBlendMode: "screen" })}>
              <Letters text={text} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

export default LayeredText;
