"""
audio_router.py
One-click automatic audio routing configurator.
Detects apps, assigns VB-Cable devices, saves undo state, can restore.
"""

import json
import os
import threading
from dataclasses import dataclass
from typing import Callable, Optional

from app_detector import detect_communication_apps
from win_audio_policy import PolicyConfigClient
from audio_devices import find_device_by_keywords

UNDO_FILE = os.path.join(os.path.dirname(__file__), ".audio_routing_undo.json")

CABLE_A_OUTPUT_KEYWORDS = ["cable-a output", "cable a output", "cable output"]
CABLE_B_INPUT_KEYWORDS  = ["cable-b input",  "cable b input",  "cable input"]


@dataclass
class AppRoutingResult:
    display_name: str
    exe_name: str
    icon: str
    is_running: bool
    output_set: Optional[bool] = None
    input_set: Optional[bool] = None
    skipped: bool = False
    skip_reason: str = ""


class AudioRoutingConfigurator:
    def __init__(self, on_progress: Callable = None):
        self.on_progress = on_progress
        self.policy = PolicyConfigClient()
        self._results = []
        self._undo_data = []
        self._configured = False

    def _log(self, msg: str, step: int = 0, total: int = 0):
        print(f"[AutoRouter] {msg}")
        if self.on_progress:
            self.on_progress(msg, step, total)

    def _find_target_devices(self):
        cable_b_in  = find_device_by_keywords(CABLE_B_INPUT_KEYWORDS,  need_output=True)
        cable_a_out = find_device_by_keywords(CABLE_A_OUTPUT_KEYWORDS, need_output=False)
        output_name = cable_b_in["name"]  if cable_b_in  else None
        input_name  = cable_a_out["name"] if cable_a_out else None
        return output_name, input_name

    def configure_all(self) -> list:
        apps = detect_communication_apps()
        running_apps = [a for a in apps if a.is_running]
        not_running  = [a for a in apps if not a.is_running]

        total = len(running_apps) + 2
        self._results = []
        self._undo_data = []

        self._log("Discovering VB-Cable devices...", 1, total)
        output_device_name, input_device_name = self._find_target_devices()

        if not output_device_name and not input_device_name:
            self._log("ERROR: No VB-Cable devices found. Install VB-Cable first.", 1, total)
            return []

        if not self.policy.svv_available:
            self._log("WARNING: SoundVolumeView not found in /tools - using registry fallback.", 1, total)

        for i, app in enumerate(running_apps, start=2):
            self._log(f"Configuring {app.display_name}...", i, total)
            result = AppRoutingResult(
                display_name=app.display_name, exe_name=app.exe_name,
                icon=app.icon, is_running=True,
            )
            undo_entry = {"exe": app.exe_name, "display": app.display_name}

            if output_device_name:
                ok = self.policy.set_app_output_device(app.exe_name, output_device_name)
                result.output_set = ok
                undo_entry["had_output_override"] = ok
                self._log(f"  Output -> {output_device_name}: {'OK' if ok else 'FAILED'}", i, total)

            if input_device_name:
                ok = self.policy.set_app_input_device(app.exe_name, input_device_name)
                result.input_set = ok
                undo_entry["had_input_override"] = ok
                self._log(f"  Input <- {input_device_name}: {'OK' if ok else 'FAILED'}", i, total)

            self._results.append(result)
            self._undo_data.append(undo_entry)

        for app in not_running:
            self._results.append(AppRoutingResult(
                display_name=app.display_name, exe_name=app.exe_name,
                icon=app.icon, is_running=False,
                skipped=True, skip_reason="Not running",
            ))

        self._save_undo_state()
        self._configured = True
        self._log(f"Done! {len(running_apps)} app(s) configured.", total, total)
        return self._results

    def restore_all(self) -> bool:
        undo_data = self._load_undo_state()
        if not undo_data:
            self._log("No saved routing state found. Nothing to restore.")
            return False
        total = len(undo_data)
        for i, entry in enumerate(undo_data, 1):
            exe     = entry.get("exe", "")
            display = entry.get("display", exe)
            self._log(f"Restoring {display}...", i, total)
            self.policy.restore_app_defaults(exe)
        if os.path.exists(UNDO_FILE):
            os.remove(UNDO_FILE)
        self._configured = False
        self._log("All apps restored to system default audio devices.", total, total)
        return True

    def _save_undo_state(self):
        try:
            with open(UNDO_FILE, "w") as f:
                json.dump(self._undo_data, f, indent=2)
        except Exception as e:
            print(f"[AutoRouter] Failed to save undo state: {e}")

    def _load_undo_state(self) -> list:
        try:
            if os.path.exists(UNDO_FILE):
                with open(UNDO_FILE) as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    @property
    def has_saved_state(self) -> bool:
        return os.path.exists(UNDO_FILE)

    def configure_all_async(self, callback: Callable):
        threading.Thread(target=lambda: callback(self.configure_all()), daemon=True).start()

    def restore_all_async(self, callback: Callable):
        threading.Thread(target=lambda: callback(self.restore_all()), daemon=True).start()
