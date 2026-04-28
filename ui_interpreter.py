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
BG    = "#0f0f1a"
BG2   = "#1a1a2e"
BG3   = "#16213e"
ACCENT = "#0f3460"
GREEN = "#4ecca3"
RED   = "#e94560"
YELLOW = "#f9a826"
TEXT  = "#eaeaea"
SUB   = "#a0a0b0"
FONT  = "Segoe UI"
MONO  = "Consolas"

LANGUAGES = {
      "English":    "en", "Spanish":    "es", "French":     "fr",
      "German":     "de", "Japanese":   "ja", "Chinese":    "zh",
      "Hindi":      "hi", "Arabic":     "ar", "Portuguese": "pt",
      "Russian":    "ru", "Korean":     "ko", "Italian":    "it",
      "Turkish":    "tr", "Dutch":      "nl", "Polish":     "pl",
      "Swedish":    "sv", "Indonesian": "id", "Vietnamese": "vi",
      "Thai":       "th", "Ukrainian":  "uk", "Bengali":    "bn",
      "Tamil":      "ta",
}


class InterpreterPanel(tk.Frame):
      """
          Full bidirectional live interpreter UI panel.
              Handles language selection, VB-Cable status, start/stop, and live transcript.
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
              outer = tk.LabelFrame(self, text="  VB-Cable Status  ",
                                                                  fg=SUB, bg=BG2, font=(FONT, 9), relief="flat", bd=1)
              outer.pack(fill="x", padx=14, pady=4)

        self._dev_labels = {}
        checks = [
                      ("cable_a_input",  "CABLE A Input  -> outgoing translated voice"),
                      ("cable_b_output", "CABLE B Output -> incoming caller audio capture"),
        ]
        for key, label in checks:
                      row = tk.Frame(outer, bg=BG2)
                      row.pack(fill="x", padx=8, pady=3)
                      dot = tk.Label(row, text="●", fg=YELLOW, bg=BG2, font=(FONT, 12))
                      dot.pack(side="left")
                      tk.Label(row, text=label, fg=TEXT, bg=BG2,
                               font=(FONT, 9), width=46, anchor="w").pack(side="left", padx=4)
                      status = tk.Label(row, text="checking...", fg=YELLOW, bg=BG2, font=(FONT, 9))
                      status.pack(side="left")
                      self._dev_labels[key] = (dot, status)

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
                                  fg=SUB, bg=BG2, font=(FONT, 8)).pack(side="left", padx=6)

        row2 = tk.Frame(f, bg=BG2)
        row2.pack(fill="x", padx=8, pady=6)
        tk.Label(row2, text="Caller speaks:", fg=TEXT, bg=BG2,
                                  font=(FONT, 10), width=16, anchor="w").pack(side="left")
        self.caller_lang_var = tk.StringVar(value="Spanish")
        ttk.Combobox(row2, textvariable=self.caller_lang_var,
                                          values=list(LANGUAGES.keys()), width=18,
                                          state="readonly").pack(side="left", padx=4)
        tk.Label(row2, text="<- WhatsApp caller's language",
                                  fg=SUB, bg=BG2, font=(FONT, 8)).pack(side="left", padx=6)

    def _build_options(self):
              f = tk.Frame(self, bg=BG)
              f.pack(fill="x", padx=14, pady=2)
              self.monitor_var = tk.BooleanVar(value=False)
              tk.Checkbutton(
                  f,
                  text="Monitor mode: also play your outgoing translation through speakers",
                  variable=self.monitor_var,
                  fg=SUB, bg=BG, selectcolor=ACCENT,
                  activebackground=BG, font=(FONT, 9)
              ).pack(side="left")

    def _build_controls(self):
              f = tk.Frame(self, bg=BG)
              f.pack(fill="x", padx=14, pady=8)

        self.start_btn = tk.Button(
                      f, text="  Start Live Interpreter",
                      command=self._toggle,
                      bg=GREEN, fg=BG,
                      font=(FONT, 12, "bold"),
                      relief="flat", padx=16, pady=10, cursor="hand2"
        )
        self.start_btn.pack(fill="x")

        self.status_lbl = tk.Label(
                      f, text="Interpreter idle - select languages and click Start",
                      fg=SUB, bg=BG, font=(FONT, 9)
        )
        self.status_lbl.pack(pady=(4, 0))

    def _build_transcript(self):
              f = tk.LabelFrame(self, text="  Live Transcript  ",
                                                          fg=SUB, bg=BG3, font=(FONT, 9), relief="flat", bd=1)
              f.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.log = tk.Text(
                      f, bg="#0a0a14", fg=TEXT, font=(MONO, 9),
                      relief="flat", state="disabled", wrap="word"
        )
        self.log.pack(fill="both", expand=True, padx=4, pady=4)

        self.log.tag_config("you",    foreground=GREEN)
        self.log.tag_config("caller", foreground=YELLOW)
        self.log.tag_config("info",   foreground=SUB)
        self.log.tag_config("error",  foreground=RED)

    # ── Actions ────────────────────────────────────────────────────

    def _check_devices(self):
              found = get_all_cable_devices()
              self.after(0, lambda: self._update_device_status(found))

    def _update_device_status(self, found: dict):
              for key, (dot, lbl) in self._dev_labels.items():
                            dev = found.get(key)
                            if dev:
                                              dot.config(fg=GREEN)
                                              lbl.config(text=f"Found: [{dev['index']}] {dev['name']}", fg=GREEN)
else:
                dot.config(fg=RED)
                  lbl.config(text="Not detected - install VB-Audio Cable", fg=RED)

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
                                        "Required VB-Cable devices not found:\n\n" +
                                        "\n".join(f"  - {m}" for m in missing) +
                                        "\n\nDownload free from:\n"
                                        "vb-audio.com/Cable  (VB-Cable)\n"
                                        "vb-audio.com/Cable  (VB-Cable A+B)\n\n"
                                        "After installing, restart Chatterbox."
                      )
                      return

        your_lang   = LANGUAGES[self.your_lang_var.get()]
        caller_lang = LANGUAGES[self.caller_lang_var.get()]

        self.interpreter = BiDirectionalInterpreter(
                      your_language=your_lang,
                      caller_language=caller_lang,
                      also_play_to_speakers_outbound=self.monitor_var.get()
        )
        self.interpreter.on_log = self._on_log

        self.interpreter.start()
        self.running = True

        self.start_btn.config(text="  Stop Interpreter", bg=RED, fg="white")
        self.status_lbl.config(
                      text=f"LIVE  |  You: {self.your_lang_var.get()}  <->  Caller: {self.caller_lang_var.get()}",
                      fg=GREEN
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
