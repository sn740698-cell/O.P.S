/**
 * Retro '90s Sci-Fi Web Audio Synthesizer
 * Generates instant, zero-latency acoustic chimes for HUD interactions.
 */

class RetroSoundEngine {
  constructor() {
    this.ctx = null;
  }

  _getCtx() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  /**
   * Unique starting sound: Multi-tone upward cybernetic chirp (Ctrl + Alt)
   */
  playAppear() {
    try {
      const ctx = this._getCtx();
      if (!ctx) return;

      const now = ctx.currentTime;

      // 1. Initial Prompt Ping
      const pingOsc = ctx.createOscillator();
      const pingGain = ctx.createGain();
      pingOsc.type = 'triangle';
      pingOsc.frequency.setValueAtTime(987, now); // B5
      pingGain.gain.setValueAtTime(0.12, now);
      pingGain.gain.exponentialRampToValueAtTime(0.01, now + 0.06);

      pingOsc.connect(pingGain);
      pingGain.connect(ctx.destination);
      pingOsc.start(now);
      pingOsc.stop(now + 0.06);

      // 2. Rising Hyper-Chirp (800 Hz -> 2200 Hz)
      const sweepOsc = ctx.createOscillator();
      const sweepGain = ctx.createGain();
      sweepOsc.type = 'sawtooth';
      sweepOsc.frequency.setValueAtTime(800, now + 0.04);
      sweepOsc.frequency.exponentialRampToValueAtTime(2200, now + 0.18);

      sweepGain.gain.setValueAtTime(0.001, now + 0.04);
      sweepGain.gain.linearRampToValueAtTime(0.10, now + 0.08);
      sweepGain.gain.exponentialRampToValueAtTime(0.01, now + 0.20);

      sweepOsc.connect(sweepGain);
      sweepGain.connect(ctx.destination);
      sweepOsc.start(now + 0.04);
      sweepOsc.stop(now + 0.20);

      // 3. Harmonic Lock Chime at 1760 Hz
      const lockOsc = ctx.createOscillator();
      const lockGain = ctx.createGain();
      lockOsc.type = 'sine';
      lockOsc.frequency.setValueAtTime(1760, now + 0.16);
      lockGain.gain.setValueAtTime(0.14, now + 0.16);
      lockGain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);

      lockOsc.connect(lockGain);
      lockGain.connect(ctx.destination);
      lockOsc.start(now + 0.16);
      lockOsc.stop(now + 0.28);
    } catch (e) {
      console.warn('Audio synthesis unavailable:', e);
    }
  }

  /**
   * Unique disappearing sound: Descending tactical power-down swoop (Ctrl + Alt + Space)
   */
  playDisappear() {
    try {
      const ctx = this._getCtx();
      if (!ctx) return;

      const now = ctx.currentTime;

      // Descending swoop (1900 Hz down to 280 Hz)
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(1900, now);
      osc.frequency.exponentialRampToValueAtTime(280, now + 0.22);

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.24);

      // Low pass filter for warm disengage
      const filter = ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(3000, now);
      filter.frequency.exponentialRampToValueAtTime(400, now + 0.22);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.24);
    } catch (e) {
      console.warn('Audio synthesis unavailable:', e);
    }
  }

  /**
   * Unique memory flush / degauss sound: dual decaying wave tone with low-pass resonance sweep
   */
  playMemoryErase() {
    try {
      const ctx = this._getCtx();
      if (!ctx) return;

      const now = ctx.currentTime;
      // Tone 1: High metallic zap dropping down
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = 'square';
      osc1.frequency.setValueAtTime(1400, now);
      osc1.frequency.exponentialRampToValueAtTime(120, now + 0.28);
      gain1.gain.setValueAtTime(0.08, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.30);

      const filter = ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(2500, now);
      filter.frequency.exponentialRampToValueAtTime(200, now + 0.28);

      osc1.connect(filter);
      filter.connect(gain1);
      gain1.connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.30);

      // Tone 2: Degauss hum pulse
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(320, now + 0.05);
      osc2.frequency.linearRampToValueAtTime(80, now + 0.35);
      gain2.gain.setValueAtTime(0.12, now + 0.05);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      osc2.start(now + 0.05);
      osc2.stop(now + 0.35);
    } catch (e) {
      console.warn('Audio synthesis unavailable:', e);
    }
  }

  /**
   * Positive memory capture / commit sound: multi-stage 90s retro cybernetic data-lock chime
   */
  playMemoryStore() {
    try {
      const ctx = this._getCtx();
      if (!ctx) return;
      const now = ctx.currentTime;

      // 1. Initial Data Ping (Sawtooth / Arcade rising chirp: 587 Hz [D5] -> 1174 Hz [D6])
      const sweepOsc = ctx.createOscillator();
      const sweepGain = ctx.createGain();
      sweepOsc.type = 'sawtooth';
      sweepOsc.frequency.setValueAtTime(587.33, now);
      sweepOsc.frequency.exponentialRampToValueAtTime(1174.66, now + 0.10);
      sweepGain.gain.setValueAtTime(0.12, now);
      sweepGain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);

      sweepOsc.connect(sweepGain);
      sweepGain.connect(ctx.destination);
      sweepOsc.start(now);
      sweepOsc.stop(now + 0.12);

      // 2. High-Tech Arpeggiated Lock Chimes (A6: 1760 Hz and D7: 2349 Hz)
      const chime1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      chime1.type = 'triangle';
      chime1.frequency.setValueAtTime(1760, now + 0.08);
      gain1.gain.setValueAtTime(0.14, now + 0.08);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.28);

      chime1.connect(gain1);
      gain1.connect(ctx.destination);
      chime1.start(now + 0.08);
      chime1.stop(now + 0.28);

      const chime2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      chime2.type = 'sine';
      chime2.frequency.setValueAtTime(2349.32, now + 0.14);
      gain2.gain.setValueAtTime(0.15, now + 0.14);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.38);

      chime2.connect(gain2);
      gain2.connect(ctx.destination);
      chime2.start(now + 0.14);
      chime2.stop(now + 0.38);

      // 3. Resonant Holographic Shimmer Subtone (Warm 90s sound chip finish)
      const subOsc = ctx.createOscillator();
      const subGain = ctx.createGain();
      subOsc.type = 'sine';
      subOsc.frequency.setValueAtTime(440, now + 0.02);
      subOsc.frequency.linearRampToValueAtTime(880, now + 0.18);
      subGain.gain.setValueAtTime(0.07, now + 0.02);
      subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.24);

      subOsc.connect(subGain);
      subGain.connect(ctx.destination);
      subOsc.start(now + 0.02);
      subOsc.stop(now + 0.24);
    } catch (e) {
      console.warn('Audio synthesis unavailable:', e);
    }
  }

  /**
   * Memory execute sound: tactical radar lock-on burst
   */
  playMemoryExecute() {
    try {
      const ctx = this._getCtx();
      if (!ctx) return;
      const now = ctx.currentTime;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, now); // A5
      osc.frequency.linearRampToValueAtTime(1760, now + 0.12); // A6
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.18);
    } catch (e) {
      console.warn('Audio synthesis unavailable:', e);
    }
  }
}

export const retroSoundEngine = new RetroSoundEngine();
