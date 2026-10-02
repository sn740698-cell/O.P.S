import React, { useState, useEffect } from 'react';
import { Smartphone, QrCode, ShieldAlert, Key, Loader2, CheckCircle2, RefreshCw } from 'lucide-react';

export default function MobileSyncHub({ onEmergencyHalt }) {
  const [pairingData, setPairingData] = useState(null);
  const [loadingPin, setLoadingPin] = useState(false);
  const [devices, setDevices] = useState([]);
  const [haltStatus, setHaltStatus] = useState('');

  const handleGeneratePin = async () => {
    setLoadingPin(true);
    try {
      const resp = await fetch('/api/v1/mobile/pairing/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expires_in_minutes: 15 })
      });
      const data = await resp.json();
      setPairingData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPin(false);
    }
  };

  const loadDevices = async () => {
    try {
      const resp = await fetch('/api/v1/mobile/devices/');
      const data = await resp.json();
      setDevices(data.devices || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadDevices();
  }, []);

  const triggerHalt = async () => {
    setHaltStatus('Triggering System Kill Switch...');
    try {
      const resp = await fetch('/api/v1/mobile/emergency-halt/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Emergency Halt Triggered from Desktop UI' })
      });
      const data = await resp.json();
      setHaltStatus('🚨 EMERGENCY HALT TRIGGERED — All agent processes stopped.');
      if (onEmergencyHalt) onEmergencyHalt();
    } catch (err) {
      setHaltStatus(`Halt Error: ${err.message}`);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* PIN Pairing Generator */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3 flex flex-col">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <Smartphone className="w-4 h-4 text-red-500" />
            Mobile Companion Pairing
          </div>
          <button
            onClick={handleGeneratePin}
            disabled={loadingPin}
            className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded text-xs font-semibold flex items-center gap-1 transition"
          >
            {loadingPin ? <Loader2 className="w-3 h-3 animate-spin" /> : <Key className="w-3 h-3" />}
            <span>GENERATE PIN</span>
          </button>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center p-4 bg-zinc-900/60 rounded border border-zinc-800 text-center space-y-2">
          {pairingData ? (
            <div className="space-y-2 animate-fadeIn">
              <span className="text-xs text-zinc-400 font-mono">ENTER THIS PIN ON YOUR MOBILE PHONE:</span>
              <div className="text-4xl font-extrabold tracking-widest text-red-500 font-mono py-2 bg-black px-6 rounded-lg border border-red-800 glow-red">
                {pairingData.pin_code}
              </div>
              <div className="text-[11px] text-zinc-400 font-mono">
                Expires in {pairingData.expires_in_seconds / 60} minutes
              </div>
              <div className="text-[10px] text-zinc-500 max-w-xs truncate pt-1">
                Endpoint: {pairingData.qr_payload?.http_endpoint}
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              <QrCode className="w-10 h-10 text-zinc-600 mx-auto" />
              <div className="text-zinc-400 text-xs font-semibold">No active pairing session</div>
              <div className="text-zinc-600 text-[11px]">Click GENERATE PIN to pair phone on local static IP</div>
            </div>
          )}
        </div>

        {/* Registered Devices */}
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>Paired Devices ({devices.length})</span>
            <button onClick={loadDevices} className="text-zinc-500 hover:text-white transition">
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>
          <div className="max-h-24 overflow-y-auto space-y-1 text-xs font-mono">
            {devices.length === 0 ? (
              <div className="text-zinc-600 italic text-[11px]">No mobile devices currently paired.</div>
            ) : (
              devices.map((d) => (
                <div key={d.device_id} className="p-1.5 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-between text-[11px]">
                  <span className="text-zinc-200 font-semibold">{d.device_name} ({d.device_type})</span>
                  <span className="text-red-400">{d.is_active ? 'ACTIVE' : 'INACTIVE'}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Emergency System Kill Switch */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-4 flex flex-col justify-between">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-red-500" />
            Emergency System Kill Switch
          </div>
          <span className="text-red-500 font-mono text-[10px] font-bold">SYSTEM HALT</span>
        </div>

        <div className="space-y-2 text-center py-4">
          <p className="text-xs text-zinc-400 max-w-sm mx-auto">
            Immediately broadcasts a hard halt across all active multi-agent loops, sandbox terminal executions, and WebSocket channels.
          </p>

          <button
            onClick={triggerHalt}
            className="w-full max-w-md mx-auto py-4 rounded-xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-extrabold text-sm uppercase tracking-widest flex items-center justify-center gap-2 shadow-xl border border-red-400 transition"
          >
            <ShieldAlert className="w-6 h-6" />
            <span>TRIGGER EMERGENCY SYSTEM HALT</span>
          </button>
        </div>

        {haltStatus && (
          <div className="p-2.5 rounded bg-red-950/80 border border-red-600 text-xs font-mono text-center text-red-200">
            {haltStatus}
          </div>
        )}
      </div>
    </div>
  );
}
