import sys
import os
import time
import threading
import json
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk

try:
    import keyboard
except ImportError:
    keyboard = None


class OPSDesktopOverlay:
    """
    O.P.S. Native System-Wide Desktop Overlay Daemon.
    Floats ON TOP of all Windows apps (WhatsApp, Chrome, Desktop, VS Code, Games).
    Microphone is OFF by default. Wispr Flow is the PRIMARY Voice Engine (On-Demand only).
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("O.P.S. System-Wide Ambient Overlay")
        
        # Configure frameless, always-on-top window
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.configure(bg="#0f172a")  # Slate-900

        # Position window in bottom-right corner of screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = 440
        height = 320
        x = screen_width - width - 30
        y = screen_height - height - 80
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.is_open = True
        self.input_mode = "text"  # 'text' or 'voice'
        self.backend_url = "http://localhost:8000/api/v1"

        self._build_ui()
        self._setup_hotkeys()
        
        # Show and focus immediately on launch
        self.show_overlay()

    def _build_ui(self):
        # Container frame with glowing border effect
        main_frame = tk.Frame(self.root, bg="#0f172a", highlightbackground="#6366f1", highlightthickness=2)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header bar (draggable window)
        header_frame = tk.Frame(main_frame, bg="#1e293b", height=42)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.bind("<B1-Motion>", self._on_drag)
        header_frame.bind("<Button-1>", self._start_drag)

        title_label = tk.Label(
            header_frame,
            text="🤖 O.P.S. System-Wide Cockpit",
            font=("Segoe UI", 10, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=8)

        # Close button
        close_btn = tk.Button(
            header_frame,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#94a3b8",
            bg="#1e293b",
            bd=0,
            activeforeground="#f8fafc",
            activebackground="#334155",
            command=self.hide_overlay
        )
        close_btn.pack(side=tk.RIGHT, padx=8)

        # Mode Switch Bar (Voice vs. Text Switch)
        switch_frame = tk.Frame(main_frame, bg="#0f172a")
        switch_frame.pack(fill=tk.X, padx=10, pady=(8, 2))

        self.speak_switch_btn = tk.Button(
            switch_frame,
            text="🎙️ Speak via Wispr Flow",
            font=("Segoe UI", 8, "bold"),
            fg="#ffffff",
            bg="#7c3aed",  # Purple
            activebackground="#6d28d9",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=3,
            command=self.trigger_wispr_speech
        )
        self.speak_switch_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.quiet_type_btn = tk.Button(
            switch_frame,
            text="🌙 Quiet Type",
            font=("Segoe UI", 8, "bold"),
            fg="#cbd5e1",
            bg="#334155",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=3,
            command=self.trigger_quiet_type
        )
        self.quiet_type_btn.pack(side=tk.LEFT)

        # Mic Status Banner (Muted / Off by Default)
        self.wake_banner = tk.Label(
            main_frame,
            text="🔒 Mic Status: OFF / RESTING (Turns ON only via Wispr Flow)",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#1e293b",
            pady=4
        )
        self.wake_banner.pack(fill=tk.X, padx=8, pady=(4, 2))

        # Text input area (Focused for Wispr Flow dictation / Typing)
        self.text_area = tk.Text(
            main_frame,
            font=("Segoe UI", 10),
            bg="#020617",
            fg="#f8fafc",
            insertbackground="#a5b4fc",
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground="#6366f1",
            wrap=tk.WORD,
            height=4
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        self.text_area.bind("<Return>", self._on_enter_press)

        # Status footer & Buttons
        footer_frame = tk.Frame(main_frame, bg="#0f172a")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=8)

        self.status_label = tk.Label(
            footer_frame,
            text="Wispr Flow Voice Switch | Hotkey: Ctrl+Win",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#0f172a"
        )
        self.status_label.pack(side=tk.LEFT)

        dispatch_btn = tk.Button(
            footer_frame,
            text="Dispatch Pipeline ⚡",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#4f46e5",
            activebackground="#4338ca",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=4,
            command=self.dispatch_prompt
        )
        dispatch_btn.pack(side=tk.RIGHT)

    def trigger_wispr_speech(self):
        """Activates Voice Dictation Focus for Wispr Flow."""
        self.input_mode = "voice"
        self.show_overlay()
        self.speak_switch_btn.config(bg="#9333ea", fg="#ffffff")
        self.quiet_type_btn.config(bg="#334155", fg="#cbd5e1")
        self.wake_banner.config(
            text="🎙️ Wispr Flow Active: Speak now (Mic turns off when finished)",
            bg="#6b21a8",
            fg="#f3e8ff"
        )
        self.text_area.focus_set()

    def trigger_quiet_type(self):
        """Switches to Quiet Text Mode (Mic OFF)."""
        self.input_mode = "text"
        self.show_overlay()
        self.quiet_type_btn.config(bg="#475569", fg="#ffffff")
        self.speak_switch_btn.config(bg="#7c3aed", fg="#ffffff")
        self.wake_banner.config(
            text="🔒 Mic Status: OFF / RESTING (Quiet Typing Mode)",
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.text_area.focus_set()

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        deltax = event.x - self._drag_x
        deltay = event.y - self._drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _setup_hotkeys(self):
        """Sets up global hotkey listener for Ctrl + Windows in Windows OS using keyboard module & Win32 API."""
        if keyboard:
            try:
                keyboard.add_hotkey('ctrl+windows', lambda: self.root.after(0, self.trigger_wispr_speech))
                keyboard.add_hotkey('ctrl+win', lambda: self.root.after(0, self.trigger_wispr_speech))
            except Exception as e:
                pass

        def listen_win32_keys():
            try:
                import ctypes
                user32 = ctypes.windll.user32
                MOD_CONTROL = 0x0002
                MOD_WIN = 0x0008
                VK_O = 0x4F

                user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_WIN, VK_O)

                msg = ctypes.wintypes.MSG()
                while True:
                    if user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                        if msg.message == 0x0312:  # WM_HOTKEY
                            self.root.after(0, self.trigger_wispr_speech)
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageA(ctypes.byref(msg))
            except Exception as e:
                pass

        t = threading.Thread(target=listen_win32_keys, daemon=True)
        t.start()

    def show_overlay(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.text_area.focus_set()
        self.is_open = True

    def hide_overlay(self):
        self.root.withdraw()
        self.is_open = False

    def toggle_overlay(self):
        if self.is_open:
            self.hide_overlay()
        else:
            self.show_overlay()

    def _on_enter_press(self, event):
        if not event.state & 0x0001:  # Not holding Shift
            self.dispatch_prompt()
            return "break"

    def dispatch_prompt(self):
        prompt_text = self.text_area.get("1.0", tk.END).strip()
        if not prompt_text:
            return

        self.status_label.config(text="Dispatching to O.P.S. Backend...", fg="#a5b4fc")
        
        def send_req():
            try:
                payload = json.dumps({"prompt": prompt_text}).encode("utf-8")
                req = urllib.request.Request(
                    f"{self.backend_url}/orchestrate/",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    category = res_data.get("router", {}).get("category", "PROCESSED")
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"Success! Category: [{category}]", fg="#34d399"
                    ))
            except Exception as err:
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Error: {err}", fg="#f87171"
                ))

        threading.Thread(target=send_req, daemon=True).start()
        self.text_area.delete("1.0", tk.END)

        # Reset Mic Status back to Resting / Muted after dispatch
        self.wake_banner.config(
            text="🔒 Mic Status: OFF / RESTING (Turns ON only via Wispr Flow)",
            bg="#1e293b",
            fg="#94a3b8"
        )

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    overlay = OPSDesktopOverlay()
    overlay.run()
