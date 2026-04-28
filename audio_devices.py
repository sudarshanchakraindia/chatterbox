"""
audio_devices.py
Discovers all audio devices including VB-Cable virtual devices.
Handles both output (playback) and input (capture/loopback) routing.
pip install sounddevice soundfile numpy
"""

import sounddevice as sd
import numpy as np
import soundfile as sf
import io
import threading

CABLE_KEYWORDS = {
      "cable_a_input":  ["cable input", "vb-audio cable", "cable-a input", "cable a input"],
      "cable_b_input":  ["cable-b input", "cable b input", "vb-audio cable b"],
      "cable_a_output": ["cable output", "cable-a output", "cable a output"],
      "cable_b_output": ["cable-b output", "cable b output"],
}


def list_all_devices():
      devices = sd.query_devices()
      result = []
      for i, d in enumerate(devices):
                result.append({
                              "index": i,
                              "name": d["name"],
                              "inputs": d["max_input_channels"],
                              "outputs": d["max_output_channels"],
                              "samplerate": int(d["default_samplerate"]),
                })
            return result


def find_device_by_keywords(keywords: list, need_output: bool = True):
      for dev in list_all_devices():
                name = dev["name"].lower()
                if any(kw in name for kw in keywords):
                              if need_output and dev["outputs"] > 0:
                                                return dev
                                            if not need_output and dev["inputs"] > 0:
                                                              return dev
                                                  return None


def find_cable_a_input():
      return find_device_by_keywords(CABLE_KEYWORDS["cable_a_input"], need_output=True)


def find_cable_b_output():
      return find_device_by_keywords(CABLE_KEYWORDS["cable_b_output"], need_output=False)


def find_default_speakers():
      idx = sd.default.device[1]
    devs = list_all_devices()
    return devs[idx] if idx >= 0 and idx < len(devs) else None


def find_default_microphone():
      idx = sd.default.device[0]
    devs = list_all_devices()
    return devs[idx] if idx >= 0 and idx < len(devs) else None


def get_all_cable_devices():
      return {
          "cable_a_input":  find_device_by_keywords(CABLE_KEYWORDS["cable_a_input"],  need_output=True),
          "cable_a_output": find_device_by_keywords(CABLE_KEYWORDS["cable_a_output"], need_output=False),
          "cable_b_input":  find_device_by_keywords(CABLE_KEYWORDS["cable_b_input"],  need_output=True),
          "cable_b_output": find_device_by_keywords(CABLE_KEYWORDS["cable_b_output"], need_output=False),
}


def play_audio_bytes_to_device(audio_bytes: bytes, device_index: int):
      try:
                data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
                if data.ndim == 1:
                              data = np.column_stack([data, data])
                          sd.play(data, samplerate=sr, device=device_index, blocking=True)
except Exception as e:
        print(f"[Audio] Playback error on device {device_index}: {e}")


def play_to_multiple_devices(audio_bytes: bytes, device_indices: list):
      threads = []
    for idx in device_indices:
              if idx is not None:
                            t = threading.Thread(
                                              target=play_audio_bytes_to_device,
                                              args=(audio_bytes, idx),
                                              daemon=True
                            )
                            threads.append(t)
                            t.start()
                    for t in threads:
                              t.join()
