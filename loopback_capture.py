"""
loopback_capture.py
Captures audio playing through a virtual cable (incoming call audio).
Feeds captured chunks into speech recognition pipeline.
pip install sounddevice numpy SpeechRecognition
"""

import sounddevice as sd
import numpy as np
import speech_recognition as sr
import threading
import queue
import io
import wave


class LoopbackCapture:
    SAMPLE_RATE        = 16000
    CHANNELS           = 1
    CHUNK_DURATION     = 0.5
    SILENCE_THRESHOLD  = 0.01
    SPEECH_BUFFER_SECS = 10

    def __init__(self, device_index: int, on_audio_ready):
        self.device_index   = device_index
        self.on_audio_ready = on_audio_ready
        self.running        = False
        self._audio_queue   = queue.Queue()
        self._capture_thread = None
        self._process_thread = None

    def _capture_loop(self):
        chunk_frames = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        with sd.InputStream(
            device=self.device_index,
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="float32",
            blocksize=chunk_frames,
        ) as stream:
            while self.running:
                data, _ = stream.read(chunk_frames)
                self._audio_queue.put(data.copy())

    def _process_loop(self):
        speech_buffer      = []
        silence_chunks     = 0
        MAX_SILENCE_CHUNKS = int(1.2 / self.CHUNK_DURATION)
        MAX_BUFFER_CHUNKS  = int(self.SPEECH_BUFFER_SECS / self.CHUNK_DURATION)

        while self.running or not self._audio_queue.empty():
            try:
                chunk = self._audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            rms       = float(np.sqrt(np.mean(chunk ** 2)))
            is_speech = rms > self.SILENCE_THRESHOLD

            if is_speech:
                speech_buffer.append(chunk)
                silence_chunks = 0
            else:
                if speech_buffer:
                    silence_chunks += 1
                    speech_buffer.append(chunk)

            flush = (
                (silence_chunks >= MAX_SILENCE_CHUNKS and speech_buffer) or
                (len(speech_buffer) >= MAX_BUFFER_CHUNKS)
            )

            if flush:
                audio_data    = self._buffer_to_audio_data(speech_buffer)
                speech_buffer = []
                silence_chunks = 0
                if audio_data:
                    threading.Thread(
                        target=self.on_audio_ready,
                        args=(audio_data,),
                        daemon=True,
                    ).start()

    def _buffer_to_audio_data(self, chunks: list):
        if not chunks:
            return None
        combined = np.concatenate(chunks, axis=0)
        pcm      = (combined * 32767).astype(np.int16).tobytes()
        wav_buf  = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(pcm)
        wav_buf.seek(0)
        with sr.AudioFile(wav_buf) as source:
            recognizer = sr.Recognizer()
            return recognizer.record(source)

    def start(self):
        self.running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._capture_thread.start()
        self._process_thread.start()
        print(f"[Loopback] Capturing from device index {self.device_index}")

    def stop(self):
        self.running = False
        print("[Loopback] Stopped.")
