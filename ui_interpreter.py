"""
ui_interpreter.py
Live Interpreter tab UI panel for Chatterbox.
Provides language selection, start/stop controls, and live transcript log.

Usage:
    from ui_interpreter import InterpreterPanel
    panel = InterpreterPanel(parent_notebook)
    notebook.add(panel, text="  Live Interpreter  ")
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from audio_devices import get_all_cable_devices
from bidirectional_interpreter import BiDirectionalInterpreter

# Theme
BG     = "#0f0f1a"
BG2    = "#1a1a2e"
BG3    = "#16213e"
ACCENT = "#0f3460"
GREEN  = "#4ecca3"
RED    = "#e94560"
YELLOW = "#f9a826"
TEXT   = "#eaeaea"
SUB    = "#a0a0b0"
FONT   = "Segoe UI"
MONO   = "Consolas"

LANGUAGES = {
    "English":    "en",
    "Spanish":    "es",
    "French":     "fr",
    "German":     "de",
    "Japanese":   "ja",
    "Chinese":    "zh",
    "Hindi":      "hi",
    "Arabic":     "ar",
    "Portuguese": "pt",
    "Russian":    "ru",
    "Korean":     "ko",
    "Italian":    "it",
    "Turkish":    "tr",
    "Dutch":      "nl",
    "Polish":     "pl",
    "Swedish":    "sv",
    "Indonesian": "id",
    "Vietnamese": "vi",
    "Thai":       "th",
    "Ukrainian":  "uk",
    "Bengali":    "bn",
    "Tamil":      "ta",
}


class InterpreterPanel(tk.Frame):
    """
    Live Interpreter tab panel.
    Lets user pick language pair, start/stop interpretation,
    and view live transcript.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.interpreter = None
        self.running = False
        self._build_ui()
        threading.Thread(target=self._check_devices, daemon=True).start()

    def _build_ui(self):
        self._build_header()
        self._build_device_status()
        self._build_language_pickers()
        self._build_options()
        self._build_controls()
        self._build_transcript()

    def _build_header(self):
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(f, text="Live Bidirectional Interpreter",
                 font=(FONT, 14, "bold"), fg=GREEN, bg=BG).pack(side="left")
        tk.Label(f, text="WhatsApp  Telegram  Zoom  Teams  Discord  Any App",
                 font=(FONT, 9), fg=SUB, bg=BG).pack(side="left", padx=12)

    def _build_device_status(self):
        outer = tk.LabelFrame(self, text="  VB-Cable Device Status  ",
                              fg=SUB, bg=BG2, font=(FONT, 9), relief="flat", bd=1)
        outer.pack(fill="x", padx=14, pady=4)

        self._dev_labels = {}
        devs = [
            ("cable_a", "CABLE A Input  (your translated voice -> caller)"),
            ("cable_b", "CABLE B Output (caller audio -> you)"),
        ]
        f = tk.Frame(outer, bg=BG2)
        f.pack(fill="x", padx=8, pady=6)
        for key, label in devs:
            row = tk.Frame(f, bg=BG2)
            row.pack(fill="x", pady=2)
            dot = tk.Label(row, text="●", fg=YELLOW, bg=BG2, font=(FONT, 11))
            dot.pack(side="left")
            tk.Label(row, text=label, fg=TEXT, bg=BG2,
                     font=(FONT, 9), width=46, anchor="w").pack(side="left", padx=4)
            lbl = tk.Label(row, text="checking...", fg=YELLOW, bg=BG2, font=(FONT, 9))
            lbl.pack(side="left")
            self._dev_labels[key] = (dot, lbl)

    def _build_language_pickers(self):
        f = tk.LabelFrame(self, text="  Language Pair  ",
                          fg=SUB, bg=BG2, font=(FONT, 9), relief="flat", bd=1)
        f.pack(fill="x", padx=14, pady=4)

        row1 = tk.Frame(f, bg=BG2)
        row1.pack(fill="x", padx=8, pady=6)
        tk.Label(row1, text="You speak:", fg=TEXT, bg=BG2,
                 font=(FONT, 10), width=16, anchor="w").pack(side="left")
        self.your_lang_var = tk.StringVar(value="English")
        ttk.Combobox(row1, textvariable=self.your_lang_var,
                     values=list(LANGUAGES.keys()), width=18,
                     state="readonly").pack(side="left", padx=4)
        tk.Label(row1, text="<- your mic language",
                 fg=SUB, bg=BG2, font=(FONT, 8)).pack(side="left", padx=8)

        row2 = tk.Frame(f, bg=BG2)
        row2.pack(fill="x", padx=8, pady=(0, 6))
        tk.Label(row2, text="Caller speaks:", fg=TEXT, bg=BG2,
                 font=(FONT, 10), width=16, anchor="w").pack(side="left")
        self.caller_lang_var = tk.StringVar(value="Spanish")
        ttk.Combobox(row2, textvariable=self.caller_lang_var,
                     values=list(LANGUAGES.keys()), width=18,
                     state="readonly").pack(side="left", padx=4)
        tk.Label(row2, text="<- caller's language",
                 fg=SUB, bg=BG2, font=(FONT, 8)).pack(side="left", padx=8)

    def _build_options(self):
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=14, pady=(2, 0))
        self.monitor_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            f, text="Also play your translated voice through local speakers",
            variable=self.monitor_var,
            fg=SUB, bg=BG, selectcolor=ACCENT,
            activebackground=BG, font=(FONT, 9),
        ).pack(side="left")

    def _build_controls(self):
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=14, pady=8)

        self.start_btn = tk.Button(
            f, text="  Start Live Interpreter",
            command=self._toggle,
            bg=GREEN, fg=BG,
            font=(FONT, 12, "bold"),
            relief="flat", padx=16, pady=10, cursor="hand2",
        )
        self.start_btn.pack(fill="x")

        self.status_lbl = tk.Label(
            f, text="Interpreter idle - select languages and click Start",
            fg=SUB, bg=BG, font=(FONT, 9),
        )
        self.status_lbl.pack(pady=(4, 0))

    def _build_transcript(self):
        f = tk.LabelFrame(self, text="  Live Transcript  ",
                          fg=SUB, bg=BG, font=(FONT, 9), relief="flat", bd=1)
        f.pack(fill="both", expand=True, padx=14, pady=(4, 10))

        self.log = tk.Text(f, bg=BG2, fg=SUB, font=(MONO, 9),
                           state="disabled", wrap="word", relief="flat",
                           height=10, insertbackground=GREEN)
        scroll = ttk.Scrollbar(f, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.tag_configure("you",    foreground=GREEN)
        self.log.tag_configure("caller", foreground="#4fc3f7")
        self.log.tag_configure("error",  foreground=RED)
        self.log.tag_configure("info",   foreground=YELLOW)
        self.log.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        scroll.pack(side="right", fill="y")

        btn_row = tk.Frame(f, bg=BG)
        btn_row.pack(fill="x", padx=6, pady=(0, 4))
        tk.Button(btn_row, text="Clear Transcript", bg=ACCENT, fg=TEXT,
                  font=(FONT, 8), relief="flat", padx=8, cursor="hand2",
                  command=self._clear_log).pack(side="left")

    def _check_devices(self):
        devices = get_all_cable_devices()
        mapping = {
            "cable_a": devices.get("cable_a_input"),
            "cable_b": devices.get("cable_b_output"),
        }

        def update():
            for key, dev in mapping.items():
                dot, lbl = self._dev_labels[key]
                if dev:
                    dot.config(fg=GREEN)
                    lbl.config(text=f"Found: [{dev['index']}] {dev['name']}", fg=GREEN)
                else:
                    dot.config(fg=RED)
                    lbl.config(text="Not detected - install VB-Audio Cable", fg=RED)

        self.after(0, update)

    def _toggle(self):
        if not self.running:
            self._start()
        else:
            self._stop()

    def _start(self):
        found = get_all_cable_devices()
        missing = []
        if not found.get("cable_a_input"):
            missing.append("CABLE A Input")
        if not found.get("cable_b_output"):
            missing.append("CABLE B Output")

        if missing:
            messagebox.showwarning(
                "VB-Cable Devices Missing",
                "Required VB-Cable devices not found:\n" + "\n".join(missing) +
                "\n\nPlease install VB-Cable and VB-Cable A+B, then reboot."
            )
            return

        your_lang   = LANGUAGES[self.your_lang_var.get()]
        caller_lang = LANGUAGES[self.caller_lang_var.get()]

        self.interpreter = BiDirectionalInterpreter(
            your_language=your_lang,
            caller_language=caller_lang,
            also_play_to_speakers_outbound=self.monitor_var.get(),
        )
        self.interpreter.on_log = self._on_log

        self.interpreter.start()
        self.running = True

        self.start_btn.config(text="  Stop Interpreter", bg=RED, fg="white")
        self.status_lbl.config(
            text=f"LIVE  |  You: {self.your_lang_var.get()}  <->  Caller: {self.caller_lang_var.get()}",
            fg=GREEN,
        )
        self._log("info", f"Started: {self.your_lang_var.get()} <-> {self.caller_lang_var.get()}")
        self._log("info", "Tip: In WhatsApp/Zoom, set mic = 'CABLE A Output (VB-Audio)'")
        self._log("info", "Tip: Caller audio routed via CABLE B - speak and listen naturally")

    def _stop(self):
        if self.interpreter:
            self.interpreter.stop()
            self.interpreter = None
        self.running = False
        self.start_btn.config(text="  Start Live Interpreter", bg=GREEN, fg=BG)
        self.status_lbl.config(text="Interpreter stopped.", fg=SUB)
        self._log("info", "Interpreter stopped.")

    def _on_log(self, msg: str):
        tag = "info"
        if "[You said]" in msg:
            tag = "you"
        elif "[Caller said]" in msg:
            tag = "caller"
        elif "Error" in msg or "ERROR" in msg:
            tag = "error"
        self.after(0, lambda: self._log(tag, msg))

    def _log(self, tag: str, msg: str):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
