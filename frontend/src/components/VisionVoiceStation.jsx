import React, { useState } from 'react';
import { Eye, Mic, Volume2, Camera, Loader2, Play } from 'lucide-react';

export default function VisionVoiceStation() {
  const [screenshot, setScreenshot] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [visionPrompt, setVisionPrompt] = useState('Analyze what is on the screen');
  const [visionResult, setVisionResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const [ttsText, setTtsText] = useState('O.P.S. system online and fully operational.');
  const [synthesizing, setSynthesizing] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  const handleCaptureScreenshot = async () => {
    setCapturing(true);
    try {
      const resp = await fetch('/api/v1/vision/screenshot/');
      const data = await resp.json();
      if (data.base64) {
        setScreenshot(`data:image/png;base64,${data.base64}`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCapturing(false);
    }
  };

  const handleAnalyzeVision = async () => {
    if (!visionPrompt.trim() || analyzing) return;
    setAnalyzing(true);
    try {
      const resp = await fetch('/api/v1/vision/analyze/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: visionPrompt })
      });
      const data = await resp.json();
      setVisionResult(data);
    } catch (err) {
      setVisionResult({ error: err.message });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSynthesizeVoice = async (e) => {
    e.preventDefault();
    if (!ttsText.trim() || synthesizing) return;
    setSynthesizing(true);
    setAudioUrl(null);

    try {
      const resp = await fetch('/api/v1/voice/synthesize/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: ttsText })
      });
      const data = await resp.json();
      if (data.audio_base64) {
        const url = `data:audio/wav;base64,${data.audio_base64}`;
        setAudioUrl(url);
        const audio = new Audio(url);
        audio.play().catch((e) => console.log('Autoplay prevented:', e));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSynthesizing(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Multimodal Screen Perception Panel */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3 flex flex-col">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <Eye className="w-4 h-4 text-red-500" />
            Multimodal Vision & Screen Perception
          </div>
          <button
            onClick={handleCaptureScreenshot}
            disabled={capturing}
            className="px-2.5 py-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center gap-1 transition"
          >
            {capturing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Camera className="w-3 h-3" />}
            <span>CAPTURE SCREEN</span>
          </button>
        </div>

        {/* Screenshot preview area */}
        <div className="h-44 bg-zinc-900 border border-zinc-800 rounded overflow-hidden flex items-center justify-center">
          {screenshot ? (
            <img src={screenshot} alt="Captured Desktop" className="w-full h-full object-contain" />
          ) : (
            <div className="text-zinc-600 text-xs italic">Click CAPTURE SCREEN to grab current desktop frame</div>
          )}
        </div>

        {/* Visual reasoning prompt */}
        <div className="flex gap-2">
          <input
            type="text"
            value={visionPrompt}
            onChange={(e) => setVisionPrompt(e.target.value)}
            placeholder="Visual reasoning prompt..."
            className="flex-1 bg-zinc-900 border border-zinc-700 focus:border-red-500 rounded px-3 py-1.5 text-xs text-white placeholder-zinc-500 outline-none"
          />
          <button
            onClick={handleAnalyzeVision}
            disabled={analyzing || !visionPrompt.trim()}
            className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded text-xs font-semibold border border-zinc-600 flex items-center gap-1 transition"
          >
            {analyzing ? <Loader2 className="w-3 h-3 animate-spin text-red-400" /> : <Play className="w-3 h-3 text-red-400" />}
            <span>ANALYZE</span>
          </button>
        </div>

        {visionResult && (
          <div className="p-2.5 bg-zinc-900 rounded border border-zinc-800 text-xs font-mono text-zinc-300">
            {visionResult.analysis || JSON.stringify(visionResult, null, 2)}
          </div>
        )}
      </div>

      {/* Voice Synthesis & Audio Panel */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3 flex flex-col">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <Volume2 className="w-4 h-4 text-red-500" />
            Neural Voice Engine (Piper TTS & Wispr)
          </div>
          <span className="text-red-400 font-mono text-[10px]">REAL-TIME AUDIO</span>
        </div>

        <form onSubmit={handleSynthesizeVoice} className="space-y-3">
          <textarea
            value={ttsText}
            onChange={(e) => setTtsText(e.target.value)}
            rows={3}
            placeholder="Type text for neural voice synthesis..."
            className="w-full bg-zinc-900 border border-zinc-700 focus:border-red-500 rounded p-2.5 text-xs text-white placeholder-zinc-500 outline-none resize-none"
          />

          <div className="flex items-center justify-between">
            <span className="text-[10px] text-zinc-500 font-mono">Model: en_US-lessac-medium</span>
            <button
              type="submit"
              disabled={synthesizing || !ttsText.trim()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition"
            >
              {synthesizing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Volume2 className="w-3.5 h-3.5" />}
              <span>SPEAK AUDIO</span>
            </button>
          </div>
        </form>

        {audioUrl && (
          <div className="p-3 bg-zinc-900 border border-zinc-800 rounded space-y-2">
            <span className="text-xs font-semibold text-zinc-300">Generated Voice Audio Stream:</span>
            <audio controls src={audioUrl} className="w-full h-8" />
          </div>
        )}
      </div>
    </div>
  );
}
