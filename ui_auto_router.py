"""
ui_auto_router.py
Audio Setup tab UI - one-click automatic Windows audio routing configurator.
Detects running apps, assigns VB-Cable devices, shows status, supports restore.

Usage:
    from ui_auto_router import AutoRouterPanel
        panel = AutoRouterPanel(parent_notebook)
            notebook.add(panel, text="  Audio Setup  ")
            """

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
from audio_router import AudioRoutingConfigurator, AppRoutingResult
from app_detector import detect_communication_apps
from win_audio_policy import PolicyConfigClient
from audio_devices import get_all_cable_devices

# Theme
BG     = "#0f0f1a"
BG2    = "#1a1a2e"
BG3    = "#16213e"
ACCENT = "#0f3460"
GREEN  = "#4ecca3"
RED    = "#e94560"
YELLOW = "#f9a826"
BLUE   = "#4fc3f7"
TEXT   = "#eaeaea"
SUB    = "#a0a0b0"
FONT   = "Segoe UI"
MONO   = "Consolas"

SVV_DOWNLOAD = "https://www.nirsoft.net/utils/soundvolumeview.html"


class AutoRouterPanel(tk.Frame):
      """
          Full automatic audio routing panel.
              One-click configures all running call apps to use VB-Cable.
                  Supports restore to original devices.
                      """

    def __init__(self, parent, **kwargs):
              super().__init__(parent, bg=BG, **kwargs)
              self.configurator = AudioRoutingConfigurator(on_progress=self._on_progress)
              self._build_ui()
              threading.Thread(target=self._initial_scan, daemon=True).start()

    # ── UI Construction ───────────────────────────────────────────

    def _build_ui(self):
              self._build_header()
              self._build_requirements()
              self._build_app_list()
              self._build_progress()
              self._build_buttons()
              self._build_log()

    def _build_header(self):
              f = tk.Frame(self, bg=BG)
              f.pack(fill="x", padx=14, pady=(10, 4))
              tk.Label(f, text="Auto Audio Routing Configurator",
                       font=(FONT, 14, "bold"), fg=GREEN, bg=BG).pack(side="left")
              tk.Label(f,
                       text="Automatically routes WhatsApp, Telegram, Zoom and more through VB-Cable",
                       font=(FONT, 9), fg=SUB, bg=BG).pack(side="left", padx=10)

    def _build_requirements(self):
              outer = tk.LabelFrame(self, text="  Requirements  ",
                                                                  fg=SUB, bg=BG2, font=(FONT, 9), relief="flat", bd=1)
              outer.pack(fill="x", padx=14, pady=4)

        self._req_labels = {}
        reqs = [
                      ("cable_a", "VB-Cable (free)         - CABLE A pair"),
                      ("cable_b", "VB-Cable A+B (free)     - CABLE B pair"),
                      ("svv",     "SoundVolumeView (free)  - per-app routing engine"),
        ]
        req_frame = tk.Frame(outer, bg=BG2)
        req_frame.pack(fill="x", padx=8, pady=6)

        for key, label in reqs:
                      row = tk.Frame(req_frame, bg=BG2)
                      row.pack(fill="x", pady=2)
                      dot = tk.Label(row, text="●", fg=YELLOW, bg=BG2, font=(FONT, 11))
                      dot.pack(side="left")
                      tk.Label(row, text=label, fg=TEXT, bg=BG2,
                               font=(FONT, 9), width=40, anchor="w").pack(side="left", padx=4)
                      status = tk.Label(row, text="checking...", fg=YELLOW, bg=BG2, font=(FONT, 9))
                      status.pack(side="left")
                      self._req_labels[key] = (dot, status)

        # Download buttons
        btn_frame = tk.Frame(outer, bg=BG2)
        btn_frame.pack(fill="x", padx=8, pady=(2, 6))
        for label, url in [
                      ("Download VB-Cable",     "https://vb-audio.com/Cable/"),
                      ("Download VB-Cable A+B", "https://vb-audio.com/Cable/"),
                      ("Download SoundVolumeView", SVV_DOWNLOAD),
        ]:
                      tk.Button(btn_frame, text=label, bg=ACCENT, fg=TEXT,
                                                      font=(FONT, 8), relief="flat", padx=8, cursor="hand2",
                                                      command=lambda u=url: webbrowser.open(u)
                               ).pack(side="left", padx=4)
                  tk.Label(btn_frame, text="<- place SoundVolumeView.exe in /tools folder",
                                            fg=SUB, bg=BG2, font=(FONT, 8)).pack(side="left", padx=8)

    def _build_app_list(self):
              outer = tk.LabelFrame(self, text="  Detected Applications  ",
                                                                  fg=SUB, bg=BG2, font=(FONT, 9), relief="flat", bd=1)
              outer.pack(fill="x", padx=14, pady=4)

        canvas = tk.Canvas(outer, bg=BG2, height=170, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self._app_frame = tk.Frame(canvas, bg=BG2)
        self._app_fr
