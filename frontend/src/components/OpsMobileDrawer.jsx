import React, { useState, useEffect } from 'react';
import { Smartphone, QrCode, Key, Loader2, RefreshCw, X, Shield } from 'lucide-react';

export default function OpsMobileDrawer({ isOpen, onClose }) {
  const [pinData, setPinData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [devices, setDevices] = useState([]);

  const generatePin = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/mobile/pairing/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expires_in_minutes: 15 })
      });
      const data = await resp.json();
      setPinData(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadDevices = async () => {
    try {
      const resp = await fetch('/api/v1/mobile/devices/');
      const data = await resp.json();
      setDevices(data.devices || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDevices();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono">
      <div className="retro-box-red max-w-md w-full p-4 shadow-2xl space-y-3.5 glow-red">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2.5">
          <div className="flex items-center gap-2">
            <div className="px-1.5 py-0.5 bg-red-600 text-white font-black text-xs border border-red-500">
              MOBILE
            </div>
            <h3 className="text-xs font-bold text-white tracking-wider uppercase">
              === MOBILE COMPANION PAIRING ===
            </h3>
          </div>
          <button onClick={onClose} className="retro-btn px-2 py-0.5 text-zinc-400 hover:text-white text-xs">
            [X]
          </button>
        </div>

        {/* Pairing Display */}
        <div className="flex flex-col items-center justify-center p-4 bg-black border border-zinc-800 text-center space-y-2">
          {pinData ? (
            <div className="space-y-2">
              <span className="text-[11px] text-zinc-400 font-mono">&gt; ENTER THIS 6-DIGIT PIN ON MOBILE:</span>
              <div className="text-3xl font-black tracking-widest text-red-500 font-mono py-2 px-6 bg-zinc-950 border border-red-800 glow-red">
                {pinData.pin_code}
              </div>
              <div className="text-[10px] text-zinc-500 font-mono">
                LAN/Static IP &bull; Expires in {pinData.expires_in_seconds / 60}m
              </div>
            </div>
          ) : (
            <div className="space-y-2 py-2">
              <QrCode className="w-8 h-8 text-zinc-600 mx-auto" />
              <button
                onClick={generatePin}
                disabled={loading}
                className="retro-btn-red px-3.5 py-1.5 text-xs font-bold flex items-center gap-1.5 mx-auto disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Key className="w-3.5 h-3.5" />}
                <span>[ GENERATE PAIRING PIN ]</span>
              </button>
            </div>
          )}
        </div>

        {/* Devices list */}
        <div className="space-y-1.5 text-xs">
          <div className="flex items-center justify-between text-zinc-400">
            <span>PAIRED_DEVICES ({devices.length}):</span>
            <button onClick={loadDevices} className="retro-btn px-1.5 py-0.5 text-[10px] text-zinc-400 hover:text-white flex items-center gap-1">
              <RefreshCw className="w-2.5 h-2.5" />
              <span>[SYNC]</span>
            </button>
          </div>
          <div className="max-h-28 overflow-y-auto space-y-1 text-xs">
            {devices.length === 0 ? (
              <div className="text-zinc-600 italic text-[11px] text-center py-2 bg-black border border-zinc-900">
                [No mobile companion connected yet]
              </div>
            ) : (
              devices.map((d) => (
                <div key={d.device_id} className="p-1.5 bg-black border border-zinc-800 flex items-center justify-between text-[11px]">
                  <span className="text-zinc-200">{d.device_name} ({d.device_type})</span>
                  <span className="text-red-400 font-bold">[{d.is_active ? 'ONLINE' : 'OFFLINE'}]</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
