import React, { useState, useEffect } from 'react';
import {
  Database,
  Play,
  Trash2,
  Plus,
  RefreshCw,
  ExternalLink,
  Music,
  Film,
  Search,
  AppWindow,
  Clock,
  CheckCircle,
  AlertTriangle,
  FolderOpen,
  Sparkles
} from 'lucide-react';
import { retroSoundEngine } from '../utils/retroSounds';

export default function OpsUserMemoriesTab({ onDispatchCommand }) {
  const [memories, setMemories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [statusMessage, setStatusMessage] = useState('');
  const [isExecutingId, setIsExecutingId] = useState(null);
  const [isDeletingId, setIsDeletingId] = useState(null);

  // Quick Capture Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [formLabel, setFormLabel] = useState('');
  const [formCategory, setFormCategory] = useState('media');
  const [formUrl, setFormUrl] = useState('');
  const [formWindowTitle, setFormWindowTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch all memories from PostgreSQL ops_db
  const fetchMemories = async () => {
    setIsLoading(true);
    try {
      const resp = await fetch('/api/v1/workstation-memory/');
      if (resp.ok) {
        const data = await resp.json();
        setMemories(data.memories || []);
      } else {
        console.error('Failed to fetch memories:', resp.statusText);
      }
    } catch (err) {
      console.error('Error fetching workstation memories:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();

    const handleMemoryEvent = () => {
      fetchMemories();
    };
    window.addEventListener('ops_memory_added', handleMemoryEvent);
    return () => window.removeEventListener('ops_memory_added', handleMemoryEvent);
  }, []);

  // Handle Quick Memory Capture
  const handleCreateMemory = async (e) => {
    e.preventDefault();
    if (!formLabel.trim()) return;

    setIsSubmitting(true);
    setStatusMessage('Committing workstation memory to PostgreSQL...');

    try {
      const resp = await fetch('/api/v1/workstation-memory/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          label: formLabel.trim(),
          category: formCategory,
          target_url: formUrl.trim(),
          window_title: formWindowTitle.trim() || formLabel.trim()
        })
      });

      if (resp.ok) {
        retroSoundEngine.playMemoryStore();
        setFormLabel('');
        setFormUrl('');
        setFormWindowTitle('');
        setShowAddForm(false);
        setStatusMessage(`[✓] MEMORY STORED IN POSTGRESQL: "${formLabel}"`);
        await fetchMemories();
      } else {
        const err = await resp.json();
        setStatusMessage(`[!] Capture error: ${err.message || 'Unknown error'}`);
      }
    } catch (err) {
      setStatusMessage(`[!] Network error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
      setTimeout(() => setStatusMessage(''), 5000);
    }
  };

  // Handle Recall and Auto-Execute Memory
  const handleExecuteMemory = async (mem) => {
    setIsExecutingId(mem.memory_id);
    retroSoundEngine.playMemoryExecute();
    setStatusMessage(`[▶] Recalling and executing memory: "${mem.label}"...`);

    try {
      const resp = await fetch('/api/v1/workstation-memory/execute/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory_id: mem.memory_id })
      });

      if (resp.ok) {
        const data = await resp.json();
        setStatusMessage(`[✓] EXECUTED: ${data.execution_details || `Window navigated to ${mem.label}`}`);
      } else {
        const err = await resp.json();
        setStatusMessage(`[!] Execution failed: ${err.message}`);
      }
    } catch (err) {
      setStatusMessage(`[!] Error triggering playback: ${err.message}`);
    } finally {
      setIsExecutingId(null);
      setTimeout(() => setStatusMessage(''), 6000);
    }
  };

  // Handle Memory Deletion
  const handleDeleteMemory = async (mem) => {
    if (!window.confirm(`Delete memory "${mem.label}" from PostgreSQL?`)) return;

    setIsDeletingId(mem.memory_id);
    try {
      const resp = await fetch(`/api/v1/workstation-memory/${mem.memory_id}/`, {
        method: 'DELETE'
      });

      if (resp.ok) {
        retroSoundEngine.playMemoryErase();
        setStatusMessage(`[🗑] Memory "${mem.label}" deleted from PostgreSQL ops_db.`);
        setMemories((prev) => prev.filter((m) => m.memory_id !== mem.memory_id));
      } else {
        setStatusMessage(`[!] Deletion failed.`);
      }
    } catch (err) {
      setStatusMessage(`[!] Network error: ${err.message}`);
    } finally {
      setIsDeletingId(null);
      setTimeout(() => setStatusMessage(''), 5000);
    }
  };

  // Filter memories by category
  const filteredMemories = memories.filter((m) => {
    if (selectedCategory === 'ALL') return true;
    return (m.category || '').toLowerCase() === selectedCategory.toLowerCase();
  });

  const getCategoryBadge = (cat) => {
    const c = (cat || 'general').toLowerCase();
    switch (c) {
      case 'media':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold bg-red-950 text-red-400 border border-red-800 flex items-center gap-1">
            <Music className="w-3 h-3" /> MEDIA / SONG
          </span>
        );
      case 'social':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold bg-purple-950 text-purple-300 border border-purple-800 flex items-center gap-1">
            <Film className="w-3 h-3" /> SOCIAL / REEL
          </span>
        );
      case 'search':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800 flex items-center gap-1">
            <Search className="w-3 h-3" /> SEARCH QUERY
          </span>
        );
      case 'app':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1">
            <AppWindow className="w-3 h-3" /> APP / WINDOW
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold bg-zinc-900 text-zinc-300 border border-zinc-700 flex items-center gap-1">
            <Database className="w-3 h-3" /> WORKSTATION
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* 90s Retro Tactical HUD Header Banner */}
      <div className="bg-black border border-zinc-800 p-4 relative overflow-hidden shadow-lg">
        <div className="absolute top-0 left-0 w-1 h-full bg-red-600" />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-red-500" />
              <h2 className="text-sm font-extrabold tracking-wider text-white">
                === TAB 03: MY WORKSTATION MEMORIES ===
              </h2>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Persistent user memory vault backed by <span className="text-red-400 font-bold">PostgreSQL 18 (ops_db)</span>.
              Captures active windows, YouTube playback, Instagram reels, searches, and apps.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="px-2.5 py-1 text-xs bg-zinc-950 border border-zinc-800 text-zinc-300 flex items-center gap-2 font-mono">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>POSTGRES: ops_db</span>
              <span className="text-zinc-600">|</span>
              <span className="text-red-400 font-bold">COUNT: {memories.length}</span>
            </div>

            <button
              onClick={fetchMemories}
              disabled={isLoading}
              className="retro-btn px-2.5 py-1 text-xs text-zinc-300 hover:text-white flex items-center gap-1.5"
              title="Refresh memories from PostgreSQL"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-red-500' : ''}`} />
              <span>[ ↻ REFRESH ]</span>
            </button>

            <button
              onClick={() => setShowAddForm((prev) => !prev)}
              className="retro-btn-red px-3 py-1 text-xs font-bold flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{showAddForm ? '[ - CLOSE ]' : '[ + MEMORIZE ITEM ]'}</span>
            </button>
          </div>
        </div>

        {/* Live Status Message Notification */}
        {statusMessage && (
          <div className="mt-3 p-2 bg-zinc-950 border-l-2 border-red-500 text-xs font-mono text-zinc-200 animate-fadeIn">
            {statusMessage}
          </div>
        )}
      </div>

      {/* Manual Memory Capture Form Drawer */}
      {showAddForm && (
        <form
          onSubmit={handleCreateMemory}
          className="bg-black border border-red-900/60 p-4 space-y-3 relative shadow-md"
        >
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <span className="text-xs font-bold text-red-400 flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5" /> [ MEMORIZE CURRENT WINDOW / MEDIA / SEARCH TO POSTGRESQL ]
            </span>
            <span className="text-[10px] text-zinc-500">OPS-DB // PERSISTENT VAULT</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] text-zinc-400 block mb-1">
                MEMORY LABEL / TRIGGER (e.g. "my favorite song", "viral reel") *
              </label>
              <input
                type="text"
                required
                value={formLabel}
                onChange={(e) => setFormLabel(e.target.value)}
                placeholder="e.g. my favorite song"
                className="w-full bg-zinc-950 border border-zinc-800 px-3 py-1.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-red-600 font-mono"
              />
            </div>

            <div>
              <label className="text-[10px] text-zinc-400 block mb-1">CATEGORY</label>
              <select
                value={formCategory}
                onChange={(e) => setFormCategory(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 px-3 py-1.5 text-xs text-white focus:outline-none focus:border-red-600 font-mono"
              >
                <option value="media">Media / Song (YouTube, Spotify, Video)</option>
                <option value="social">Social (Instagram Reel, Twitter/X)</option>
                <option value="search">Search (Google, ArXiv, Wikipedia)</option>
                <option value="app">Application (VS Code, Chrome, Terminal)</option>
                <option value="general">General Workstation Window</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-zinc-400 block mb-1">
                TARGET URL OR APP (Optional, auto-resolved if blank)
              </label>
              <input
                type="text"
                value={formUrl}
                onChange={(e) => setFormUrl(e.target.value)}
                placeholder="e.g. https://www.youtube.com/watch?v=..."
                className="w-full bg-zinc-950 border border-zinc-800 px-3 py-1.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-red-600 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="retro-btn px-3 py-1 text-xs text-zinc-400 hover:text-white"
            >
              [ CANCEL ]
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="retro-btn-red px-4 py-1 text-xs font-bold text-white flex items-center gap-1.5"
            >
              <Database className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'SAVING...' : '[ COMMIT MEMORY TO DB ]'}</span>
            </button>
          </div>
        </form>
      )}

      {/* Category Filter Navigation Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-2">
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {['ALL', 'MEDIA', 'SOCIAL', 'SEARCH', 'APP'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 text-xs font-bold transition ${
                selectedCategory === cat
                  ? 'bg-red-600 text-white border border-red-500'
                  : 'bg-zinc-950 text-zinc-400 border border-zinc-800 hover:text-white hover:border-zinc-700'
              }`}
            >
              [ {cat} ]
            </button>
          ))}
        </div>

        <div className="text-[10px] text-zinc-500 font-mono">
          SHOWING: {filteredMemories.length} OF {memories.length} MEMORIES
        </div>
      </div>

      {/* Main Vault Content Area */}
      {isLoading ? (
        <div className="p-8 text-center bg-black border border-zinc-800 text-zinc-400 text-xs font-mono">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-red-500 mb-2" />
          <span>[ CONNECTING TO POSTGRESQL (ops_db) MEMORY VAULT... ]</span>
        </div>
      ) : memories.length === 0 ? (
        /* Authentic Retro Empty State (User Request: Starts with 0 memories, everything else was an example) */
        <div className="bg-black border-2 border-dashed border-zinc-800 p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-zinc-950 border border-zinc-800 flex items-center justify-center mx-auto text-zinc-600">
            <Database className="w-6 h-6 text-red-600" />
          </div>

          <div>
            <h3 className="text-sm font-extrabold tracking-wider text-white">
              [•] NO WORKSTATION MEMORIES CREATED YET
            </h3>
            <p className="text-xs text-zinc-500 mt-1 max-w-lg mx-auto">
              Your personal PostgreSQL memory vault is currently empty. All previously mentioned songs, reels,
              and windows were examples. Create your first real memory whenever you want!
            </p>
          </div>

          {/* Interactive Tactical Guidance Box */}
          <div className="max-w-xl mx-auto bg-zinc-950 border border-zinc-800 p-4 text-left space-y-2 text-xs font-mono">
            <div className="text-red-400 font-bold flex items-center gap-1.5 border-b border-zinc-800 pb-1.5">
              <Sparkles className="w-3.5 h-3.5" /> HOW TO CAPTURE & RECALL WORKSTATION MEMORIES:
            </div>

            <div className="space-y-1.5 text-zinc-300">
              <div className="flex items-start gap-2">
                <span className="text-red-500 font-bold">1. CAPTURE:</span>
                <span>
                  While playing any song on YouTube, browsing an Instagram reel, or viewing any window, say or type:
                  <br />
                  <code className="text-white bg-black px-1.5 py-0.5 border border-zinc-800 inline-block mt-0.5">
                    "add it to this, my memory, this is my favorite song"
                  </code>
                </span>
              </div>

              <div className="flex items-start gap-2 pt-1">
                <span className="text-emerald-500 font-bold">2. RECALL:</span>
                <span>
                  Anytime later, simply command O.P.S.:
                  <br />
                  <code className="text-white bg-black px-1.5 py-0.5 border border-zinc-800 inline-block mt-0.5">
                    "Add my favorite song from the memory"
                  </code>
                  <br />
                  <span className="text-[11px] text-zinc-500">
                    O.P.S. will automatically open the window, navigate to the target, and initiate playback.
                  </span>
                </span>
              </div>

              <div className="flex items-start gap-2 pt-1">
                <span className="text-blue-500 font-bold">3. DELETE:</span>
                <span>
                  Use the <code>[ 🗑 DELETE MEMORY ]</code> button in this tab whenever you wish to remove an entry.
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => setShowAddForm(true)}
            className="retro-btn-red px-4 py-1.5 text-xs font-bold inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>[ + MEMORIZE YOUR FIRST ITEM NOW ]</span>
          </button>
        </div>
      ) : filteredMemories.length === 0 ? (
        <div className="p-6 text-center bg-black border border-zinc-800 text-zinc-500 text-xs font-mono">
          <span>[•] NO MEMORIES FOUND IN CATEGORY: {selectedCategory}</span>
        </div>
      ) : (
        /* Memory Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredMemories.map((mem) => {
            const isExecuting = isExecutingId === mem.memory_id;
            const isDeleting = isDeletingId === mem.memory_id;

            return (
              <div
                key={mem.memory_id}
                className="bg-black border border-zinc-800 hover:border-red-600/70 p-3.5 flex flex-col justify-between transition group shadow-sm hover:shadow-red-950/20"
              >
                <div>
                  {/* Card Header: Category Badge + Timestamp */}
                  <div className="flex items-center justify-between gap-2 border-b border-zinc-900 pb-2 mb-2">
                    {getCategoryBadge(mem.category)}
                    <span className="text-[10px] text-zinc-500 flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3" />
                      {mem.created_at}
                    </span>
                  </div>

                  {/* Memory Label */}
                  <h4 className="text-sm font-bold text-white group-hover:text-red-400 transition tracking-wide">
                    "{mem.label}"
                  </h4>

                  {/* Window Title / Snippet */}
                  {mem.window_title && mem.window_title !== mem.label && (
                    <p className="text-xs text-zinc-400 mt-1 line-clamp-1 font-mono">
                      <span className="text-zinc-600">WINDOW:</span> {mem.window_title}
                    </p>
                  )}

                  {/* Target URL */}
                  {mem.target_url && (
                    <div className="mt-2 flex items-center gap-1.5 text-xs text-zinc-500">
                      <ExternalLink className="w-3 h-3 text-red-500 shrink-0" />
                      <a
                        href={mem.target_url}
                        target="_blank"
                        rel="noreferrer"
                        className="truncate hover:text-white hover:underline transition font-mono"
                        title={mem.target_url}
                      >
                        {mem.target_url}
                      </a>
                    </div>
                  )}
                </div>

                {/* Card Action Controls: Play / Open & Delete */}
                <div className="mt-4 pt-2 border-t border-zinc-900 flex items-center justify-between gap-2">
                  <button
                    onClick={() => handleExecuteMemory(mem)}
                    disabled={isExecuting}
                    className="retro-btn-red px-3 py-1 text-xs font-bold flex items-center gap-1.5 flex-1 justify-center disabled:opacity-50"
                    title="Automatically open window and execute playback"
                  >
                    <Play className={`w-3 h-3 ${isExecuting ? 'animate-pulse' : ''}`} />
                    <span>{isExecuting ? 'EXECUTING...' : '[ ▶ PLAY / OPEN NOW ]'}</span>
                  </button>

                  <button
                    onClick={() => handleDeleteMemory(mem)}
                    disabled={isDeleting}
                    className="retro-btn px-2.5 py-1 text-xs text-zinc-400 hover:text-red-400 hover:border-red-600 flex items-center gap-1 disabled:opacity-50"
                    title="Delete this memory from PostgreSQL"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">[ DELETE ]</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
