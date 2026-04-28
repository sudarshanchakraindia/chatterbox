"""
main.py
Chatterbox - Live Bidirectional Interpreter
Main application window with tabbed interface.

Run with:  python main.py
Build with: pyinstaller chatterbox.spec
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

BG      = "#0f0f1a"
BG2     = "#1a1a2e"
ACCENT  = "#0f3460"
GREEN   = "#4ecca3"
TEXT    = "#eaeaea"
SUB     = "#a0a0b0"
FONT    = "Segoe UI"


class ChatterboxApp(tk.Tk):
      APP_NAME    = "Chatterbox"
      APP_VERSION = "1.0.0"
      WIN_SIZE    = "1100x780"
      MIN_SIZE    = (900, 640)

    def __init__(self):
              super().__init__()
              self._configure_window()
              self._apply_ttk_style()
              self._build_ui()

    def _configure_window(self):
              self.title(f"{self.APP_NAME}  v{self.APP_VERSION}  -  Live Interpreter")
              self.geometry(self.WIN_SIZE)
              self.minsize(*self.MIN_SIZE)
              self.configure(bg=BG)
              try:
                            self.iconbitmap("chatterbox.ico")
except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_ttk_style(self):
              style = ttk.Style(self)
              style.theme_use("clam")
              style.configure("TNotebook", background=BG, borderwidth=0)
              style.configure("TNotebook.Tab", background=BG2, foreground=SUB,
                              font=(FONT, 10), padding=[16, 6], borderwidth=0)
              style.map("TNotebook.Tab",
                        background=[("selected", ACCENT)],
                        foreground=[("selected", TEXT)])
              style.configure("TCombobox", fieldbackground=BG2, background=BG2,
                              foreground=TEXT, selectbackground=ACCENT, borderwidth=0)
              style.configure("Vertical.TScrollbar", background=BG2, troughcolor=BG,
                              borderwidth=0, arrowcolor=SUB)
              style.configure("TProgressbar", troughcolor=BG2, background=GREEN,
                              borderwidth=0, thickness=6)

    def _build_ui(self):
              # Title bar
              title_bar = tk.Frame(self, bg=ACCENT, height=42)
              title_bar.pack(fill="x")
              title_bar.pack_propagate(False)
              tk.Label(title_bar, text="CHATTERBOX", font=(FONT, 13, "bold"),
                       fg=GREEN, bg=ACCENT).pack(side="left", padx=14, pady=8)
              tk.Label(title_bar, text="Real-Time Bidirectional Live Interpreter",
                       font=(FONT, 9), fg=SUB, bg=ACCENT).pack(side="left")
              tk.Label(title_bar, text=f"v{self.APP_VERSION}",
                       font=(FONT, 8), fg=SUB, bg=ACCENT).pack(side="right", padx=14)

        # Notebook tabs
              self.notebook = ttk.Notebook(self)
              self.notebook.pack(fill="both", expand=True)

        # Import UI panels here to avoid circular imports at module level
              from ui_auto_router import AutoRouterPanel
              from ui_interpreter import InterpreterPanel

        self.router_tab = AutoRouterPanel(self.notebook, bg=BG)
        self.notebook.add(self.router_tab, text="  Audio Setup  ")

        self.interp_tab = InterpreterPanel(self.notebook, bg=BG)
        self.notebook.add(self.interp_tab, text="  Live Interpreter  ")

        self.notebook.add(self._build_help_tab(), text="  Help & Guide  ")

        # Status bar
        status_bar = tk.Frame(self, bg=BG2, height=24)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        tk.Label(status_bar, text="Ready", fg=SUB, bg=BG2,
                                  font=(FONT, 8), anchor="w").pack(side="left", padx=10, pady=4)
        tk.Label(status_bar, text="VB-Audio Virtual Cable required | vb-audio.com/Cable",
                                  fg=SUB, bg=BG2, font=(FONT, 8)).pack(side="right", padx=10)

    def _build_help_tab(self) -> tk.Frame:
              frame = tk.Frame(self.notebook, bg=BG)
              canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
              scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
              inner  = tk.Frame(canvas, bg=BG)
              inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
              canvas.create_window((0, 0), window=inner, anchor="nw")
              canvas.configure(yscrollcommand=scroll.set)
              canvas.pack(side="left", fill="both", expand=True)
              scroll.pack(side="right", fill="y")

        sections = [
                      ("Quick Start (5 steps)", [
                                        ("Step 1", "Install VB-Cable (free) from vb-audio.com/Cable - installs CABLE A pair"),
                                        ("Step 2", "Install VB-Cable A+B (free) from vb-audio.com/Cable - installs CABLE B pair"),
                                        ("Step 3", "Download SoundVolumeView.exe into the /tools folder next to chatterbox"),
                                        ("Step 4", "Open your call app (WhatsApp, Telegram, Zoom...) and start a call"),
                                        ("Step 5", "Go to Audio Setup tab -> click Auto-Configure -> then Live Interpreter -> Start"),
                      ]),
                      ("Supported Apps", [
                                        ("WhatsApp Desktop", "Full support - auto-configured"),
                                        ("Telegram Desktop", "Full support - auto-configured"),
                                        ("Zoom",             "Full support - auto-configured"),
                                        ("Microsoft Teams",  "Full support - auto-configured"),
                                        ("Discord",          "Full support - auto-configured"),
                                        ("Google Meet",      "Via Chrome/Edge - auto-configured"),
                                        ("Skype, Viber, Signal, WeChat, LINE", "Full support - auto-configured"),
                      ]),
                      ("Troubleshooting", [
                                        ("No VB-Cable found",    "Install both VB-Cable and VB-Cable A+B, then reboot"),
                                        ("Caller hears nothing", "Set WhatsApp/Zoom mic to CABLE A Output in their settings"),
                                        ("You hear nothing",     "Check CABLE B Output capture - rescan devices in Audio Setup"),
                                        ("SoundVolumeView warn", "Download SoundVolumeView.exe and place in /tools subfolder"),
                                        ("High latency",         "Use wired headset; close other audio apps"),
                      ]),
        ]

        for section_title, items in sections:
                      tk.Label(inner, text=section_title, font=(FONT, 12, "bold"),
                                                    fg=GREEN, bg=BG, anchor="w").pack(fill="x", padx=20, pady=(16, 4))
                      sep = tk.Frame(inner, bg=ACCENT, height=1)
                      sep.pack(fill="x", padx=20, pady=(0, 8))
                      for label, detail in items:
                                        row = tk.Frame(inner, bg=BG2)
                                        row.pack(fill="x", padx=20, pady=2)
                                        tk.Label(row, text=label, font=(FONT, 9, "bold"), fg=TEXT, bg=BG2,
                                                 width=24, anchor="w").pack(side="left", padx=(10, 4), pady=6)
                                        tk.Label(row, text=detail, font=(FONT, 9), fg=SUB, bg=BG2,
                                                 anchor="w", wraplength=600, justify="left"
                                                ).pack(side="left", padx=4, pady=6, fill="x", expand=True)
                                return frame

    def _on_close(self):
              try:
                            if hasattr(self, 'interp_tab') and hasattr(self.interp_tab, 'interpreter'):
                                              if self.interp_tab.interpreter:
                                                                    self.interp_tab.interpreter.stop()
              except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
      app = ChatterboxApp()
    app.mainloop()
