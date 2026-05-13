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
            ("cable_a", "VB-Cable (free) - CABLE A pair"),
            ("cable_b", "VB-Cable A+B (free) - CABLE B pair"),
            ("svv",     "SoundVolumeView (free) - per-app routing engine"),
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
            ("Download VB-Cable",       "https://vb-audio.com/Cable/"),
            ("Download VB-Cable A+B",   "https://vb-audio.com/Cable/"),
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
        self._app_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._app_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True, padx=8, pady=6)
        scroll.pack(side="right", fill="y")

        # Rescan button
        btn_row = tk.Frame(outer, bg=BG2)
        btn_row.pack(fill="x", padx=8, pady=(0, 6))
        tk.Button(btn_row, text="Rescan Apps", bg=ACCENT, fg=TEXT,
                  font=(FONT, 8), relief="flat", padx=8, cursor="hand2",
                  command=lambda: threading.Thread(
                      target=self._initial_scan, daemon=True).start()
                  ).pack(side="left")
        self._app_count_lbl = tk.Label(btn_row, text="", fg=SUB, bg=BG2, font=(FONT, 8))
        self._app_count_lbl.pack(side="left", padx=10)

    def _build_progress(self):
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=14, pady=(4, 0))
        self._progress_lbl = tk.Label(f, text="", fg=SUB, bg=BG, font=(FONT, 9), anchor="w")
        self._progress_lbl.pack(fill="x")
        self._progress_bar = ttk.Progressbar(f, mode="determinate", length=300)
        self._progress_bar.pack(fill="x", pady=2)

    def _build_buttons(self):
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=14, pady=6)

        self._configure_btn = tk.Button(
            f, text="  Auto-Configure All Apps",
            command=self._run_configure,
            bg=GREEN, fg=BG, font=(FONT, 11, "bold"),
            relief="flat", padx=14, pady=8, cursor="hand2",
        )
        self._configure_btn.pack(side="left", padx=(0, 8))

        self._restore_btn = tk.Button(
            f, text="  Restore Original Devices",
            command=self._run_restore,
            bg=ACCENT, fg=TEXT, font=(FONT, 10),
            relief="flat", padx=14, pady=8, cursor="hand2",
        )
        self._restore_btn.pack(side="left")

    def _build_log(self):
        f = tk.LabelFrame(self, text="  Activity Log  ",
                          fg=SUB, bg=BG, font=(FONT, 9), relief="flat", bd=1)
        f.pack(fill="both", expand=True, padx=14, pady=(4, 10))

        self.log = tk.Text(f, bg=BG2, fg=SUB, font=(MONO, 9),
                           state="disabled", wrap="word", relief="flat",
                           height=6, insertbackground=GREEN)
        scroll = ttk.Scrollbar(f, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.tag_configure("ok",    foreground=GREEN)
        self.log.tag_configure("warn",  foreground=YELLOW)
        self.log.tag_configure("error", foreground=RED)
        self.log.tag_configure("info",  foreground=BLUE)
        self.log.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        scroll.pack(side="right", fill="y")

    # ── Logic ─────────────────────────────────────────────────────

    def _initial_scan(self):
        # Check VB-Cable devices
        devices = get_all_cable_devices()
        cable_a_ok = devices.get("cable_a_input") is not None
        cable_b_ok = devices.get("cable_b_output") is not None
        svv_ok = PolicyConfigClient().svv_available

        def update_req():
            for key, ok in [("cable_a", cable_a_ok), ("cable_b", cable_b_ok), ("svv", svv_ok)]:
                dot, lbl = self._req_labels[key]
                color = GREEN if ok else RED
                dot.config(fg=color)
                lbl.config(text="OK" if ok else "NOT FOUND", fg=color)

        self.after(0, update_req)

        # Scan for apps
        apps = detect_communication_apps()
        running = [a for a in apps if a.is_running]

        def update_apps():
            for w in self._app_frame.winfo_children():
                w.destroy()
            if not running:
                tk.Label(self._app_frame, text="No communication apps detected",
                         fg=SUB, bg=BG2, font=(FONT, 9)).pack(padx=8, pady=4)
            else:
                for app in running:
                    row = tk.Frame(self._app_frame, bg=BG2)
                    row.pack(fill="x", padx=4, pady=1)
                    tk.Label(row, text=app.icon + " " + app.display_name,
                             fg=GREEN, bg=BG2, font=(FONT, 9),
                             width=26, anchor="w").pack(side="left", padx=4)
                    tk.Label(row, text=app.exe_name,
                             fg=SUB, bg=BG2, font=(MONO, 8)).pack(side="left")
            self._app_count_lbl.config(
                text=f"{len(running)} app(s) running"
            )

        self.after(0, update_apps)

    def _on_progress(self, msg: str, step: int, total: int):
        def update():
            self._progress_lbl.config(text=msg)
            if total > 0:
                self._progress_bar["value"] = (step / total) * 100
            tag = "error" if "ERROR" in msg else "warn" if "WARNING" in msg else "ok" if "OK" in msg or "Done" in msg else "info"
            self._log(tag, msg)
        self.after(0, update)

    def _run_configure(self):
        self._configure_btn.config(state="disabled", text="  Configuring...")
        self.configurator.configure_all_async(self._on_configure_done)

    def _on_configure_done(self, results: list):
        def update():
            self._configure_btn.config(state="normal", text="  Auto-Configure All Apps")
            self._progress_bar["value"] = 100
            ok_count = sum(1 for r in results if r.is_running and not r.skipped)
            self._log("ok", f"Configuration complete: {ok_count} app(s) routed through VB-Cable.")
        self.after(0, update)

    def _run_restore(self):
        self._restore_btn.config(state="disabled", text="  Restoring...")
        self.configurator.restore_all_async(self._on_restore_done)

    def _on_restore_done(self, success: bool):
        def update():
            self._restore_btn.config(state="normal", text="  Restore Original Devices")
            if success:
                self._log("ok", "All apps restored to system default audio devices.")
            else:
                self._log("warn", "Nothing to restore (no saved configuration found).")
        self.after(0, update)

    def _log(self, tag: str, msg: str):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")
