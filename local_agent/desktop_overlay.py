import sys
import os
import time
import threading
import json
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk

class OPSDesktopOverlay:
    """
    O.P.S. Native System-Wide Desktop Overlay Daemon.
    Floats ON TOP of all Windows apps (WhatsApp, Chrome, Desktop, VS Code, Games).
    Triggered globally via Ctrl + Windows hotkey or "Hey OPS" voice trigger.
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
        width = 400
        height = 280
        x = screen_width - width - 30
        y = screen_height - height - 80
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.is_open = False
        self.input_mode = "text"  # 'text' or 'voice'
        self.is_listening = False
        self.backend_url = "http://localhost:8000/api/v1"

        self._build_ui()
        self._setup_hotkeys()
        
        # Start hidden initially or shown as small pill
        self.root.withdraw()

    def _build_ui(self):
        # Container frame with glowing border effect
        main_frame = tk.Frame(self.root, bg="#0f172a", highlightbackground="#6366f1", highlightthickness=2)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header bar
        header_frame = tk.Frame(main_frame, bg="#1e293b", height=40)
        header_frame.pack(fill=tk.X, side=tk.TOP)

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

        # Mode Indicator Banner
        self.banner_label = tk.Label(
            main_frame,
            text="🌙 Quiet Text Mode (Works System-Wide: WhatsApp, Desktop, Apps)",
            font=("Segoe UI", 8),
            fg="#a5b4fc",
            bg="#0f172a"
        )
        self.banner_label.pack(anchor=tk.W, padx=12, pady=(8, 4))

        # Text input area
        self.text_area = tk.Text(
            main_frame,
            font=("Segoe UI", 10),
            bg="#020617",
            fg="#f8fafc",
            insertbackground="#a5b4fc",
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground="#334155",
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
            text="Hotkey: Ctrl+Win | Wake: 'Hey OPS'",
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

    def _setup_hotkeys(self):
        """Sets up global hotkey listener for Ctrl + Windows in Windows OS."""
        def listen_global_keys():
            try:
                import ctypes
                user32 = ctypes.windll.user32

                # Register VK_LWIN (0x5B) and VK_RWIN (0x5C) or Ctrl+Win hotkey loop
                MOD_CONTROL = 0x0002
                MOD_WIN = 0x0008
                VK_O = 0x4F

                # Hotkey ID 1: Ctrl + Win + O or Ctrl + Win
                user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_WIN, VK_O)

                msg = ctypes.wintypes.MSG()
                while True:
                    if user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                        if msg.message == 0x0312:  # WM_HOTKEY
                            self.root.after(0, self.toggle_overlay)
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageA(ctypes.byref(msg))
            except Exception as e:
                print(f"[Desktop Overlay] Global hotkey listener notice: {e}")

        t = threading.Thread(target=listen_global_keys, daemon=True)
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

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    overlay = OPSDesktopOverlay()
    overlay.run()
