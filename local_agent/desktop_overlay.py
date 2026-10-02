"""
O.P.S. Native System-Wide Desktop Overlay & Global Hotkey Daemon
Floats ON TOP of all Windows applications (Chrome, WhatsApp, VS Code, Games, Desktop).
Triggered anywhere by pressing:
  • [ Ctrl + Alt ] or [ Ctrl + Alt + Space ] (Voice / Wispr Flow Focus)
  • [ Ctrl + Shift + K ] (Quiet Text Command Focus)
  • Speaking wake phrase: "Hey OPS"
Connected directly to the O.P.S. Tri-Model Multi-Agent Brain & Web HUD.
"""

import sys
import os
import re
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

try:
    import speech_recognition as sr
except ImportError:
    sr = None


class OPSDesktopOverlay:
    """
    O.P.S. Native System-Wide Ambient Overlay.
    Full-duplex synchronization with the central Tri-Model Brain and Web HUD.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("O.P.S. Pop-Up Cockpit")
        
        # Configure frameless, always-on-top window
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.configure(bg="#09090b")  # Pitch Black

        # Position window in bottom-right corner
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = 500
        height = 430
        x = screen_width - width - 30
        y = screen_height - height - 60
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.is_open = True
        self.input_mode = "text"
        self._is_wispr_active = False
        self.backend_url = "http://localhost:8000/api/v1"
        self._typewriter_job = None
        self._cursor_blink_job = None
        self._current_full_text = ""
        self._current_pending_permission = None

        self._build_ui()
        self._setup_hotkeys()
        self._setup_wake_word_listener()
        self._setup_permission_listener()
        
        # Focus on launch
        self.show_overlay()

    def _build_ui(self):
        # Container frame with glowing Crimson Red border
        main_frame = tk.Frame(
            self.root,
            bg="#09090b",
            highlightbackground="#dc2626",
            highlightthickness=2
        )
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Minimal Header Bar
        header_frame = tk.Frame(main_frame, bg="#18181b", height=32, bd=1, relief=tk.RAISED)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.bind("<B1-Motion>", self._on_drag)
        header_frame.bind("<Button-1>", self._start_drag)

        badge_label = tk.Label(
            header_frame,
            text="[OPS]",
            font=("Consolas", 9, "bold"),
            fg="#ffffff",
            bg="#dc2626",
            padx=6,
            pady=1
        )
        badge_label.pack(side=tk.LEFT, padx=(8, 6), pady=4)

        title_label = tk.Label(
            header_frame,
            text="O.P.S. POP-UP COCKPIT",
            font=("Consolas", 8, "bold"),
            fg="#f4f4f5",
            bg="#18181b"
        )
        title_label.pack(side=tk.LEFT, pady=4)

        close_btn = tk.Button(
            header_frame,
            text="[X]",
            font=("Consolas", 8, "bold"),
            fg="#a1a1aa",
            bg="#18181b",
            bd=0,
            activeforeground="#ffffff",
            activebackground="#27272a",
            command=self.hide_overlay
        )
        close_btn.pack(side=tk.RIGHT, padx=8)

        # 2. Control + Windows / Wispr Flow Indicator Banner
        self.wispr_banner = tk.Frame(
            main_frame,
            bg="#18181b",
            bd=1,
            relief=tk.SOLID,
            highlightbackground="#27272a",
            highlightthickness=1,
            cursor="hand2"
        )
        self.wispr_banner.pack(fill=tk.X, padx=10, pady=(6, 2))
        self.wispr_banner.bind("<Button-1>", lambda e: self.toggle_wispr_flow())

        self.wispr_icon_badge = tk.Label(
            self.wispr_banner,
            text="🎙️ [CTRL + WIN]",
            font=("Consolas", 8, "bold"),
            fg="#ef4444",
            bg="#18181b",
            padx=6,
            pady=3,
            cursor="hand2"
        )
        self.wispr_icon_badge.pack(side=tk.LEFT)
        self.wispr_icon_badge.bind("<Button-1>", lambda e: self.toggle_wispr_flow())

        self.wispr_status_label = tk.Label(
            self.wispr_banner,
            text="WISPR FLOW: STANDBY (Press Ctrl+Win to Speak)",
            font=("Consolas", 8),
            fg="#a1a1aa",
            bg="#18181b",
            cursor="hand2"
        )
        self.wispr_status_label.pack(side=tk.LEFT, padx=4)
        self.wispr_status_label.bind("<Button-1>", lambda e: self.toggle_wispr_flow())

        self.wispr_state_badge = tk.Label(
            self.wispr_banner,
            text="[ IDLE ]",
            font=("Consolas", 7, "bold"),
            fg="#71717a",
            bg="#27272a",
            padx=5,
            pady=1,
            cursor="hand2"
        )
        self.wispr_state_badge.pack(side=tk.RIGHT, padx=6)
        self.wispr_state_badge.bind("<Button-1>", lambda e: self.toggle_wispr_flow())

        # 3. Sleek Prompt Bar (Text Input + Send Button)
        input_container = tk.Frame(main_frame, bg="#09090b")
        input_container.pack(fill=tk.X, padx=10, pady=(6, 4))

        self.text_area = tk.Text(
            input_container,
            font=("Consolas", 9),
            bg="#000000",
            fg="#ffffff",
            insertbackground="#ef4444",
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground="#3f3f46",
            wrap=tk.WORD,
            height=2
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        self.text_area.bind("<Return>", self._on_enter_press)

        send_btn = tk.Button(
            input_container,
            text="[ ⚡ SEND ]",
            font=("Consolas", 8, "bold"),
            fg="#ffffff",
            bg="#dc2626",
            activebackground="#991b1b",
            activeforeground="#ffffff",
            bd=1,
            relief=tk.RAISED,
            padx=10,
            command=self.dispatch_prompt
        )
        send_btn.pack(side=tk.RIGHT, fill=tk.Y)

        # 3. Streamlined Response Screen
        resp_container = tk.Frame(main_frame, bg="#09090b")
        resp_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        self.response_text = tk.Text(
            resp_container,
            font=("Consolas", 9),
            bg="#000000",
            fg="#f4f4f5",
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground="#27272a",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.response_text.tag_configure("cursor", foreground="#ef4444", font=("Consolas", 10, "bold"))
        self.response_text.tag_configure("text_body", foreground="#f4f4f5")
        self.response_text.bind("<Button-1>", self._on_response_clicked)
        self.response_text.pack(fill=tk.BOTH, expand=True)

        # 4. Human-in-the-Loop Security Approval Frame (Packed only when permission is requested)
        self.permission_frame = tk.Frame(
            main_frame,
            bg="#18181b",
            highlightbackground="#ef4444",
            highlightthickness=2,
            padx=8,
            pady=6
        )
        
        perm_title_row = tk.Frame(self.permission_frame, bg="#18181b")
        perm_title_row.pack(fill=tk.X)

        self.perm_title_label = tk.Label(
            perm_title_row,
            text="🚨 [SECURITY APPROVAL REQUIRED]",
            font=("Consolas", 8, "bold"),
            fg="#ef4444",
            bg="#18181b"
        )
        self.perm_title_label.pack(side=tk.LEFT)

        self.perm_risk_badge = tk.Label(
            perm_title_row,
            text="[RISK: HIGH]",
            font=("Consolas", 8, "bold"),
            fg="#ffffff",
            bg="#7f1d1d",
            padx=4,
            pady=1
        )
        self.perm_risk_badge.pack(side=tk.RIGHT)

        self.perm_desc_label = tk.Label(
            self.permission_frame,
            text="",
            font=("Consolas", 8),
            fg="#e4e4e7",
            bg="#18181b",
            justify=tk.LEFT,
            anchor="w",
            wraplength=440
        )
        self.perm_desc_label.pack(fill=tk.X, pady=(2, 6))

        # Accept / Deny Buttons (Strict Red, White, Black, Gray Palette)
        perm_btn_row = tk.Frame(self.permission_frame, bg="#18181b")
        perm_btn_row.pack(fill=tk.X)

        self.perm_accept_btn = tk.Button(
            perm_btn_row,
            text="[ ✅ ACCEPT / ALLOW ]",
            font=("Consolas", 8, "bold"),
            fg="#ffffff",
            bg="#3f3f46",
            activebackground="#52525b",
            activeforeground="#ffffff",
            bd=1,
            relief=tk.RAISED,
            padx=10,
            pady=3,
            command=lambda: self.resolve_current_permission("ALLOW_ONCE")
        )
        self.perm_accept_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.perm_deny_btn = tk.Button(
            perm_btn_row,
            text="[ ❌ DENY / BLOCK ]",
            font=("Consolas", 8, "bold"),
            fg="#ffffff",
            bg="#991b1b",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            bd=1,
            relief=tk.RAISED,
            padx=10,
            pady=3,
            command=lambda: self.resolve_current_permission("DENY")
        )
        self.perm_deny_btn.pack(side=tk.LEFT)

        # 5. Clean Minimal Footer
        footer_frame = tk.Frame(main_frame, bg="#09090b")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(2, 6))

        self.status_label = tk.Label(
            footer_frame,
            text="Ctrl+Alt: Open • Ctrl+Win: Wispr Flow • Ctrl+Alt+Space: Close",
            font=("Consolas", 8),
            fg="#71717a",
            bg="#09090b"
        )
        self.status_label.pack(side=tk.LEFT)

        # Dummy references for compatibility
        self.speak_switch_btn = tk.Label(footer_frame)
        self.quiet_type_btn = tk.Label(footer_frame)
        self.wake_banner = tk.Label(footer_frame)

    def toggle_wispr_flow(self):
        """Toggles Wispr Flow voice dictation state on/off (Ctrl + Win)."""
        if getattr(self, "_is_wispr_active", False):
            self.deactivate_wispr_flow()
        else:
            self.activate_wispr_flow()

    def activate_wispr_flow(self):
        """Activates Wispr Flow indicator and primes voice input."""
        self._is_wispr_active = True
        self.input_mode = "voice"
        self.show_overlay(play_sound=False)
        self.wispr_banner.config(bg="#7f1d1d", highlightbackground="#ef4444")
        self.wispr_icon_badge.config(
            text="🔴 🎙️ [CTRL + WIN]",
            fg="#ffffff",
            bg="#7f1d1d"
        )
        self.wispr_status_label.config(
            text="WISPR FLOW: ACTIVE & LISTENING... (Speak directive)",
            fg="#ffffff",
            bg="#7f1d1d"
        )
        self.wispr_state_badge.config(
            text="[ REC ● ]",
            fg="#ffffff",
            bg="#dc2626"
        )
        try:
            import winsound
            winsound.Beep(1760, 60)
        except Exception:
            pass
        self.text_area.focus_set()

    def deactivate_wispr_flow(self):
        """Returns Wispr Flow to standby state."""
        self._is_wispr_active = False
        self.input_mode = "text"
        self.wispr_banner.config(bg="#18181b", highlightbackground="#27272a")
        self.wispr_icon_badge.config(
            text="🎙️ [CTRL + WIN]",
            fg="#ef4444",
            bg="#18181b"
        )
        self.wispr_status_label.config(
            text="WISPR FLOW: STANDBY (Press Ctrl+Win to Speak)",
            fg="#a1a1aa",
            bg="#18181b"
        )
        self.wispr_state_badge.config(
            text="[ IDLE ]",
            fg="#71717a",
            bg="#27272a"
        )

    def trigger_wispr_speech(self):
        """Activates Voice Dictation Focus for Wispr Flow."""
        self.activate_wispr_flow()

    def trigger_quiet_type(self):
        """Switches to Quiet Text Mode."""
        self.deactivate_wispr_flow()
        self.show_overlay()
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

    def play_sound_appear(self):
        """Plays unique starting sound when Pop-Up Cockpit appears."""
        try:
            import winsound
            sound_file = os.path.join(os.path.dirname(__file__), "sounds", "cockpit_appear.wav")
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(1400, 70)
        except Exception as e:
            logger.debug(f"Audio appear play failed: {e}")

    def play_sound_disappear(self):
        """Plays unique disappearing sound when Pop-Up Cockpit disappears."""
        try:
            import winsound
            sound_file = os.path.join(os.path.dirname(__file__), "sounds", "cockpit_disappear.wav")
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(500, 70)
        except Exception as e:
            logger.debug(f"Audio disappear play failed: {e}")

    def play_sound_memory_added(self):
        """Plays signature 90s retro sci-fi memory storage sound when an item is added to memory."""
        try:
            import winsound
            sound_file = os.path.join(os.path.dirname(__file__), "sounds", "memory_added.wav")
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(880, 80)
                winsound.Beep(1760, 120)
        except Exception as e:
            logger.debug(f"Audio memory_added play failed: {e}")

    def _setup_hotkeys(self):
        """
        Global hotkey listeners:
        - Control + Alt: Pop-Up Cockpit appears with unique starting sound
        - Control + Alt + Space: Pop-Up Cockpit disappears with unique disappearing sound
        - Control + Windows: Toggles Wispr Flow voice dictation active indicator
        """
        if keyboard:
            try:
                # 1. Disappear Hotkey: Ctrl + Alt + Space
                keyboard.add_hotkey('ctrl+alt+space', lambda: self.root.after(0, self.hide_overlay))

                # 2. Appear Hotkey: Ctrl + Alt (checked when space is not held)
                def on_ctrl_alt_pressed():
                    try:
                        if not keyboard.is_pressed('space'):
                            self.root.after(0, self.show_overlay)
                    except Exception:
                        self.root.after(0, self.show_overlay)

                keyboard.add_hotkey('ctrl+alt', on_ctrl_alt_pressed)
                keyboard.add_hotkey('ctrl+alt+o', lambda: self.root.after(0, self.show_overlay))
                keyboard.add_hotkey('ctrl+shift+k', lambda: self.root.after(0, self.trigger_quiet_type))

                # 3. Wispr Flow Hotkey: Ctrl + Windows
                def on_ctrl_win_pressed():
                    self.root.after(0, self.toggle_wispr_flow)

                try:
                    keyboard.add_hotkey('ctrl+windows', on_ctrl_win_pressed)
                    keyboard.add_hotkey('ctrl+win', on_ctrl_win_pressed)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Keyboard hotkey hook warning: {e}")

        # Rock-solid Win32 background key polling listener (works across any fullscreen app)
        def win32_key_listener():
            try:
                import ctypes
                user32 = ctypes.windll.user32
                VK_CONTROL = 0x11
                VK_MENU = 0x12  # Alt
                VK_SPACE = 0x20
                VK_LWIN = 0x5B  # Left Windows key
                VK_RWIN = 0x5C  # Right Windows key

                last_trigger = 0
                last_win_trigger = 0
                was_active = False
                was_win_active = False

                while True:
                    try:
                        ctrl = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                        alt = bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000)
                        space = bool(user32.GetAsyncKeyState(VK_SPACE) & 0x8000)
                        win = bool((user32.GetAsyncKeyState(VK_LWIN) & 0x8000) or (user32.GetAsyncKeyState(VK_RWIN) & 0x8000))
                        now = time.time()

                        # Check Ctrl + Windows -> Toggle Wispr Flow
                        if ctrl and win:
                            if not was_win_active and (now - last_win_trigger > 0.35):
                                self.root.after(0, self.toggle_wispr_flow)
                                last_win_trigger = now
                                was_win_active = True
                        else:
                            if not ctrl and not win:
                                was_win_active = False

                        # Check Ctrl + Alt & Ctrl + Alt + Space
                        if ctrl and alt:
                            if not was_active and (now - last_trigger > 0.28):
                                if space:
                                    # Control + Alt + Space -> Disappear
                                    self.root.after(0, self.hide_overlay)
                                    last_trigger = now
                                    was_active = True
                                else:
                                    # Tiny debounce to verify if Space was pressed simultaneously
                                    time.sleep(0.04)
                                    space_second_check = bool(user32.GetAsyncKeyState(VK_SPACE) & 0x8000)
                                    if space_second_check:
                                        self.root.after(0, self.hide_overlay)
                                    else:
                                        self.root.after(0, self.show_overlay)
                                    last_trigger = now
                                    was_active = True
                        else:
                            if not ctrl and not alt:
                                was_active = False

                        time.sleep(0.03)
                    except Exception:
                        time.sleep(0.1)
            except Exception:
                pass

        t = threading.Thread(target=win32_key_listener, daemon=True)
        t.start()

    def _setup_wake_word_listener(self):
        """Background Listener for 'Hey OPS' wake word."""
        if not sr:
            return

        def wake_word_loop():
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True

            while True:
                try:
                    with sr.Microphone() as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        audio = recognizer.listen(source, timeout=3.5, phrase_time_limit=4.0)

                        try:
                            text = recognizer.recognize_google(audio).lower()
                            wake_phrases = ['hey ops', 'he ops', 'hey opps', 'hi ops', 'hey office', 'ops']
                            if any(w in text for w in wake_phrases):
                                cleaned = text
                                for w in wake_phrases:
                                    cleaned = cleaned.replace(w, '')
                                cleaned = cleaned.strip()

                                self.root.after(0, lambda c=cleaned: self._on_hey_ops_wake(c))
                        except Exception:
                            pass
                except Exception:
                    time.sleep(0.5)

        t = threading.Thread(target=wake_word_loop, daemon=True)
        t.start()

    def _on_hey_ops_wake(self, prompt_text=""):
        """Triggered automatically when 'Hey OPS' is spoken."""
        self.trigger_wispr_speech()
        self.wake_banner.config(
            text="⚡ 'HEY OPS' DETECTED! Pop-Up Active!",
            bg="#991b1b",
            fg="#ffffff"
        )
        if prompt_text:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, prompt_text)

        self.root.after(4000, lambda: self.wake_banner.config(
            text="🎙️ Directives: 'Search Google...', 'Build project...', 'Open app...'",
            bg="#18181b",
            fg="#fca5a5"
        ))

    def show_overlay(self, play_sound=True):
        """Brings the Pop-Up Cockpit on screen and plays the unique starting sound."""
        if not self.is_open:
            if play_sound:
                self.play_sound_appear()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.text_area.focus_set()
        self.is_open = True

    def hide_overlay(self, play_sound=True):
        """Hides the Pop-Up Cockpit from screen and plays the unique disappearing sound."""
        if self.is_open:
            if play_sound:
                self.play_sound_disappear()
        self.root.withdraw()
        self.is_open = False

    def toggle_overlay(self):
        if self.is_open:
            self.hide_overlay()
        else:
            self.show_overlay()

    def _on_enter_press(self, event):
        if not event.state & 0x0001:
            self.dispatch_prompt()
            return "break"

    def _cancel_typewriter(self):
        if self._typewriter_job:
            try:
                self.root.after_cancel(self._typewriter_job)
            except Exception:
                pass
            self._typewriter_job = None
        if self._cursor_blink_job:
            try:
                self.root.after_cancel(self._cursor_blink_job)
            except Exception:
                pass
            self._cursor_blink_job = None

    def _on_response_clicked(self, event=None):
        """Clicking the response box instantly finishes typewriter animation."""
        if self._typewriter_job and self._current_full_text:
            self._cancel_typewriter()
            self._render_text_immediate(self._current_full_text)

    def _render_text_immediate(self, text: str):
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert(tk.END, text, "text_body")
        self.response_text.insert(tk.END, " █", "cursor")
        self.response_text.config(state=tk.DISABLED)
        self.response_text.see(tk.END)

    def stream_typewriter_response(self, text: str, speed_ms: int = 22):
        """Streams LLM response word-by-word with a 90s retro blinking block cursor."""
        self._cancel_typewriter()
        self._current_full_text = text

        tokens = re.findall(r'\S+|\s+', text) if text else []
        if not tokens:
            self._render_text_immediate("")
            return

        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete("1.0", tk.END)
        self.response_text.config(state=tk.DISABLED)

        accumulated = []

        def type_step(index: int):
            if index < len(tokens):
                accumulated.append(tokens[index])
                current_str = "".join(accumulated)

                self.response_text.config(state=tk.NORMAL)
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert(tk.END, current_str, "text_body")
                self.response_text.insert(tk.END, " █", "cursor")
                self.response_text.config(state=tk.DISABLED)
                self.response_text.see(tk.END)

                self._typewriter_job = self.root.after(speed_ms, lambda: type_step(index + 1))
            else:
                self._typewriter_job = None
                self._start_cursor_blink()

        type_step(0)

    def _start_cursor_blink(self):
        """Subtle blinking cursor when response streaming is complete."""
        self._cursor_visible = True

        def blink():
            if not self._current_full_text:
                return
            self._cursor_visible = not self._cursor_visible
            self.response_text.config(state=tk.NORMAL)
            self.response_text.delete("1.0", tk.END)
            self.response_text.insert(tk.END, self._current_full_text, "text_body")
            if self._cursor_visible:
                self.response_text.insert(tk.END, " █", "cursor")
            self.response_text.config(state=tk.DISABLED)
            self._cursor_blink_job = self.root.after(700, blink)

        self._cursor_blink_job = self.root.after(700, blink)

    def set_response_content(self, text: str):
        """Displays LLM response in the overlay window using retro typewriter streaming."""
        self.stream_typewriter_response(text, speed_ms=22)

    def speak_audio_response(self, text: str):
        """Calls TTS endpoint to speak response aloud (optional)."""
        def tts_req():
            try:
                clean = text.replace("#", "").replace("*", "").replace("`", "")[:250]
                payload = json.dumps({"text": clean}).encode("utf-8")
                req = urllib.request.Request(
                    f"{self.backend_url}/voice/synthesize/",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req)
            except Exception:
                pass
        threading.Thread(target=tts_req, daemon=True).start()

    def dispatch_prompt(self):
        prompt_text = self.text_area.get("1.0", tk.END).strip()
        if not prompt_text:
            return

        self.status_label.config(text="Deploying Multi-Agent Team...", fg="#f87171")
        self.set_response_content("Thinking & formulating multi-agent plan...")
        
        def send_req():
            try:
                payload = json.dumps({"prompt": prompt_text}).encode("utf-8")
                # Routes to LangGraph multi-agent pipeline (which broadcasts to Web HUD simultaneously)
                req = urllib.request.Request(
                    f"{self.backend_url}/agent/run/",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    category = res_data.get("intent") or res_data.get("category", "EXECUTED")
                    flow = res_data.get("target_flow", "")
                    answer = res_data.get("final_answer", "Execution completed.")

                    # Play retro sound whenever something is added to memory
                    if (
                        category == "WORKSTATION_MEMORY_CAPTURE" or
                        res_data.get("tool_output", {}).get("action") == "workstation_memory_capture" or
                        "COMMITTED TO POSTGRESQL" in answer or
                        "WORKSTATION MEMORY COMMITTED" in answer
                    ):
                        self.play_sound_memory_added()

                    # Update response text in overlay with typewriter streaming animation
                    self.root.after(0, lambda: self.set_response_content(answer))
                    status_badge = f"Completed! [{category}]" if not flow else f"Completed! [{category} • {flow}]"
                    self.root.after(0, lambda: self.status_label.config(
                        text=status_badge, fg="#34d399"
                    ))

            except Exception as err:
                self.root.after(0, lambda: self.set_response_content(f"Error: {err}"))
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Error: {err}", fg="#ef4444"
                ))

        threading.Thread(target=send_req, daemon=True).start()
        self.text_area.delete("1.0", tk.END)

    def show_permission_request(self, perm: dict):
        """Displays the Human-in-the-Loop Security Approval prompt inside the Pop-Up Cockpit."""
        self._current_pending_permission = perm
        action = perm.get("action_type", "action")
        target = (perm.get("command_text") or perm.get("target") or "")
        reason = perm.get("reason", "")
        agent = perm.get("agent_name", "SystemAutomationAgent")
        risk = perm.get("risk_level", "HIGH")

        if action == "launch_app":
            title = "🚨 [AUTHORIZATION REQUIRED: OPEN ITEM]"
            desc = f"• Agent: {agent}\n• Request: Open '{target.upper()}'\n• Permission: Allow O.P.S. to launch this item?"
        elif action == "run_claude_routine":
            title = "🚨 [AUTHORIZATION REQUIRED: CLAUDE WORKFLOW]"
            desc = f"• Agent: {agent}\n• Request: cd D:\\freellmapi -> npm run dev -> launch Claude\n• Permission: Allow terminal routine execution?"
        elif action == "open_in_vscode":
            title = "🚨 [AUTHORIZATION REQUIRED: VS CODE]"
            desc = f"• Agent: {agent}\n• Request: Open '{target}' in Visual Studio Code\n• Permission: Allow VS Code launch?"
        elif action == "browser_dom_task":
            title = "🚨 [AUTHORIZATION REQUIRED: BROWSER DOM TASK]"
            desc = f"• Agent: {agent}\n• Request: DOM automation for '{target}'\n• Permission: Allow browser automation?"
        elif action == "open_file_or_folder":
            title = "🚨 [AUTHORIZATION REQUIRED: OPEN FILE/FOLDER]"
            desc = f"• Agent: {agent}\n• Request: Open '{target}'\n• Permission: Allow file/folder access?"
        elif action == "open_browser_search":
            title = "🚨 [AUTHORIZATION REQUIRED: WEB SEARCH]"
            desc = f"• Agent: {agent}\n• Request: Web search for '{target}'\n• Permission: Allow browser search?"
        elif action == "run_terminal_cmd":
            title = "🚨 [AUTHORIZATION REQUIRED: TERMINAL]"
            desc = f"• Agent: {agent}\n• Command: {target[:70]}\n• Permission: Execute terminal command?"
        else:
            title = "🚨 [SECURITY APPROVAL REQUIRED]"
            desc = f"• Agent: {agent}\n• Action: {action}\n• Target: {target[:70]}"

        if reason and reason not in desc:
            desc += f"\n• Reason: {reason[:75]}"

        self.perm_title_label.config(text=title)
        self.perm_desc_label.config(text=desc)
        self.perm_risk_badge.config(text=f"RISK: {risk}")

        # Pack above response text
        self.permission_frame.pack(fill=tk.X, padx=10, pady=(2, 4), before=self.response_text)
        self.show_overlay()

    def hide_permission_request(self):
        """Hides the Human-in-the-Loop Security Approval prompt."""
        self._current_pending_permission = None
        self.permission_frame.pack_forget()

    def resolve_current_permission(self, decision: str):
        """Sends user approval or denial decision to the backend."""
        if not self._current_pending_permission:
            return

        req_id = self._current_pending_permission.get("request_id")
        self.hide_permission_request()

        def do_resolve():
            try:
                payload = json.dumps({"request_id": str(req_id), "decision": decision}).encode("utf-8")
                req = urllib.request.Request(
                    f"{self.backend_url}/permissions/resolve/",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req) as resp:
                    pass
                msg = "Permission Granted: Item Launched!" if "ALLOW" in decision else "Permission Denied: Blocked!"
                self.root.after(0, lambda: self.status_label.config(
                    text=msg, fg="#34d399" if "ALLOW" in decision else "#ef4444"
                ))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Resolution error: {e}", fg="#ef4444"))

        threading.Thread(target=do_resolve, daemon=True).start()

    def _setup_permission_listener(self):
        """Polls backend for pending Human-In-The-Loop requests to surface in Pop-Up Cockpit."""
        def poll_loop():
            while True:
                try:
                    req = urllib.request.Request(f"{self.backend_url}/permissions/pending/")
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        pending = data.get("pending", [])
                        if pending:
                            curr_id = pending[0].get("request_id")
                            if not self._current_pending_permission or self._current_pending_permission.get("request_id") != curr_id:
                                self.root.after(0, lambda p=pending[0]: self.show_permission_request(p))
                        else:
                            if self._current_pending_permission:
                                self.root.after(0, self.hide_permission_request)
                except Exception:
                    pass
                time.sleep(0.45)

        t = threading.Thread(target=poll_loop, daemon=True)
        t.start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    overlay = OPSDesktopOverlay()
    overlay.run()
