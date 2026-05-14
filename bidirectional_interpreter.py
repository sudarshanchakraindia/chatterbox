"""
bidirectional_interpreter.py
Runs two simultaneous interpretation pipelines:
  OUTBOUND: Your mic  -> STT -> Translate -> TTS -> CABLE A Input (caller hears)
  INBOUND:  CABLE B Output (caller audio) -> STT -> Translate -> TTS -> Speakers (you hear)
pip install SpeechRecognition deep-translator sounddevice soundfile edge-tts numpy pyaudio
"""

import speech_recognition as sr
from deep_translator import GoogleTranslator
from audio_devices import (
    find_cable_a_input, find_cable_b_output,
    find_default_speakers, find_default_microphone,
    play_audio_bytes_to_device, play_to_multiple_devices,
)
from tts_engine import synthesize
from loopback_capture import LoopbackCapture
import threading

recognizer = sr.Recognizer()


class BiDirectionalInterpreter:
    def __init__(
        self,
        your_language: str = "en",
        caller_language: str = "es",
        cable_a_device_index: int = None,
        cable_b_device_index: int = None,
        speakers_device_index: int = None,
        also_play_to_speakers_outbound: bool = False,
        mic_device_index: int = None,
    ):
        self.your_lang   = your_language
        self.caller_lang = caller_language

        cable_a  = find_cable_a_input()
        cable_b  = find_cable_b_output()
        speakers = find_default_speakers()
        mic      = find_default_microphone()

        self.cable_a_idx  = cable_a_device_index  or (cable_a["index"]  if cable_a  else None)
        self.cable_b_idx  = cable_b_device_index  or (cable_b["index"]  if cable_b  else None)
        self.speakers_idx = speakers_device_index or (speakers["index"] if speakers else None)
        self.mic_idx      = mic_device_index      or (mic["index"]      if mic      else None)
        self.also_play_outbound_locally = also_play_to_speakers_outbound

        self.running = False
        self._outbound_thread = None
        self._loopback = None
        self.on_log = None

    def _log(self, msg: str):
        print(msg)
        if self.on_log:
            self.on_log(msg)

    def _translate(self, text: str, src: str, tgt: str) -> str:
        return GoogleTranslator(source=src, target=tgt).translate(text)

    def _outbound_process(self, audio: sr.AudioData):
        try:
            original   = recognizer.recognize_google(audio, language=self.your_lang)
            self._log(f"[You said] {original}")
            translated = self._translate(original, self.your_lang, self.caller_lang)
            self._log(f"[-> Caller hears] {translated}")
            audio_bytes = synthesize(translated, self.caller_lang)
            targets = [self.cable_a_idx]
            if self.also_play_outbound_locally and self.speakers_idx:
                targets.append(self.speakers_idx)
            play_to_multiple_devices(audio_bytes, [t for t in targets if t is not None])
        except sr.UnknownValueError:
            pass
        except Exception as e:
            self._log(f"[Outbound Error] {e}")

    def _outbound_loop(self):
        mic_kwargs = {"device_index": self.mic_idx} if self.mic_idx is not None else {}
        with sr.Microphone(**mic_kwargs) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            self._log("[Outbound] Listening to your mic...")
            while self.running:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=20)
                    threading.Thread(
                        target=self._outbound_process, args=(audio,), daemon=True
                    ).start()
                except sr.WaitTimeoutError:
                    pass

    def _inbound_process(self, audio: sr.AudioData):
        try:
            original   = recognizer.recognize_google(audio, language=self.caller_lang)
            self._log(f"[Caller said] {original}")
            translated = self._translate(original, self.caller_lang, self.your_lang)
            self._log(f"[-> You hear] {translated}")
            audio_bytes = synthesize(translated, self.your_lang)
            if self.speakers_idx is not None:
                play_audio_bytes_to_device(audio_bytes, self.speakers_idx)
        except sr.UnknownValueError:
            pass
        except Exception as e:
            self._log(f"[Inbound Error] {e}")

    def start(self):
        if self.cable_a_idx is None:
            self._log("[ERROR] CABLE A Input not found.")
            return
        if self.cable_b_idx is None:
            self._log("[ERROR] CABLE B Output not found.")
            return
        self.running = True
        self._outbound_thread = threading.Thread(target=self._outbound_loop, daemon=True)
        self._outbound_thread.start()
        self._loopback = LoopbackCapture(
            device_index=self.cable_b_idx, on_audio_ready=self._inbound_process
        )
        self._loopback.start()
        self._log(f"[BiDirectional] LIVE - You({self.your_lang}) <-> Caller({self.caller_lang})")

    def stop(self):
        self.running = False
        if self._loopback:
            self._loopback.stop()
        self._log("[BiDirectional] Stopped.")

    def set_languages(self, your_lang: str, caller_lang: str):
        self.your_lang   = your_lang
        self.caller_lang = caller_lang
