"""
win_audio_policy.py
Programmatically sets per-application audio input/output devices on Windows.
Uses SoundVolumeView CLI (primary) or Windows registry (fallback).
pip install psutil pywin32
"""

import subprocess
import os
import winreg


class PolicyConfigClient:
      """
          Sets per-app audio device using SoundVolumeView (primary)
              or Windows registry (fallback).
                  """

    def __init__(self):
              self._svv_path = self._find_soundvolumeview()

    def _find_soundvolumeview(self):
              candidates = [
                            os.path.join(os.path.dirname(__file__), "tools", "SoundVolumeView.exe"),
                            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Chatterbox", "SoundVolumeView.exe"),
                            r"C:\tools\SoundVolumeView.exe",
              ]
              for p in candidates:
                            if os.path.exists(p):
                                              return p
                                      return None

    @property
    def svv_available(self) -> bool:
              return self._svv_path is not None

    def set_app_output_device(self, exe_name: str, device_name_keyword: str) -> bool:
              if self._svv_path:
                            return self._svv_set(exe_name, device_name_keyword)
                        return self._registry_set_output(exe_name, device_name_keyword)

    def set_app_input_device(self, exe_name: str, device_name_keyword: str) -> bool:
              if self._svv_path:
                            return self._svv_set(exe_name, device_name_keyword, role="capture")
                        return False

    def _svv_set(self, exe_name: str, device_keyword: str, role: str = "render") -> bool:
              cmd = [
                  self._svv_path,
                  "/SetAppDefault",
                  device_keyword,
                  "all",
                  exe_name
    ]
        try:
                      result = subprocess.run(cmd, capture_output=True, timeout=10)
                      return result.returncode == 0
except Exception as e:
            print(f"[PolicyConfig] SoundVolumeView error: {e}")
            return False

    def _registry_set_output(self, exe_name: str, device_name_keyword: str) -> bool:
              try:
                            import sounddevice as sd
                            devices = sd.query_devices()
                            device_id = None
                            for i, d in enumerate(devices):
                                              if device_name_keyword.lower() in d["name"].lower():
                                                                    if d["max_output_channels"] > 0:
                                                                                              device_id = str(i)
                                                                                              break
                                                                                  if not device_id:
                                                                                                    return False

                                                            key_path = (
                                              r"SOFTWARE\Microsoft\Multimedia\Audio\DefaultEndpointAggregates"
                                              rf"\{exe_name}"
                                              )
                                          with winreg.CreateKeyEx(
                                                            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
                                          ) as key:
                                                            winreg.SetValueEx(key, "Render", 0, winreg.REG_SZ, device_id)
                                                        return True
except Exception as e:
            print(f"[Registry] Error setting output for {exe_name}: {e}")
            return False

    def restore_app_defaults(self, exe_name: str) -> bool:
              if self._svv_path:
                            try:
                                              cmd = [self._svv_path, "/SetAppDefault", "", "all", exe_name]
                                              subprocess.run(cmd, capture_output=True, timeout=10)
                                              return True
except Exception:
                pass
        try:
                      key_path = (
                                        r"SOFTWARE\Microsoft\Multimedia\Audio\DefaultEndpointAggregates"
                                        rf"\{exe_name}"
                      )
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            return True
except FileNotFoundError:
            return True
except Exception as e:
            print(f"[Registry] Error restoring {exe_name}: {e}")
            return False
