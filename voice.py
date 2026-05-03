"""
voice.py — Voice Engine for JARVIS
Handles:
  - Wake word detection (keyword matching via Vosk)
  - Speech-to-text (Vosk offline STT)
  - Text-to-speech (pyttsx3 offline TTS)

No internet required. Everything runs locally.
"""

import os
import json
import queue
import time
import threading
from utils import logger

# ── TTS (Text-to-Speech) ──────────────────────────────────────────────────────
try:
    import pyttsx3
    _tts_available = True
except ImportError:
    _tts_available = False
    logger.warning("pyttsx3 not installed. TTS disabled. Run: pip install pyttsx3")

# ── STT (Speech-to-Text) via Vosk ─────────────────────────────────────────────
try:
    import vosk
    import sounddevice as sd
    _stt_available = True
except ImportError:
    _stt_available = False
    logger.warning("vosk or sounddevice not installed. STT disabled.")
    logger.warning("Run: pip install vosk sounddevice")


class VoiceEngine:
    """
    Central voice system.
    - speak()             → converts text to speech
    - wait_for_wake_word()→ blocks until "jarvis" (or custom word) is heard
    - listen_for_command()→ records one command and returns transcribed text
    """

    SAMPLE_RATE = 16000   # Vosk works best at 16 kHz
    BLOCK_SIZE  = 8000    # Audio chunk size (~0.5s at 16kHz)
    SILENCE_LIMIT = 2.0   # Seconds of silence before we stop recording a command

    def __init__(self, wake_word: str = "jarvis", model_path: str = "models/vosk-model"):
        self.wake_word   = wake_word.lower()
        self.model_path  = model_path
        self._model      = None
        self._tts_engine = None
        self._tts_lock   = threading.Lock()

        self._init_tts()
        self._init_stt()

    # ── TTS ───────────────────────────────────────────────────────────────────

    def _init_tts(self):
        if not _tts_available:
            return
        try:
            self._tts_engine = pyttsx3.init()
            # Tune voice properties for a calm, British assistant feel
            self._tts_engine.setProperty("rate", 165)      # words per minute
            self._tts_engine.setProperty("volume", 0.9)

            # Try to pick a male English voice if available
            voices = self._tts_engine.getProperty("voices")
            for v in voices:
                if "male" in v.name.lower() or "david" in v.name.lower():
                    self._tts_engine.setProperty("voice", v.id)
                    break
            logger.info("TTS engine initialised.")
        except Exception as e:
            logger.error(f"TTS init failed: {e}")
            self._tts_engine = None

    def speak(self, text: str):
        """Convert text to speech. Falls back to console print if TTS unavailable."""
        print(f"\n[JARVIS]: {text}\n")
        if not self._tts_engine:
            return
        try:
            with self._tts_lock:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")

    # ── STT ───────────────────────────────────────────────────────────────────

    def _init_stt(self):
        if not _stt_available:
            logger.warning("STT not available — running in text-input mode.")
            return

        if not os.path.isdir(self.model_path):
            logger.error(
                f"Vosk model not found at '{self.model_path}'.\n"
                "Download a small model from https://alphacephei.com/vosk/models\n"
                "  e.g. vosk-model-small-en-us-0.15\n"
                "Extract it and rename the folder to 'models/vosk-model'."
            )
            return

        try:
            vosk.SetLogLevel(-1)                      # silence Vosk's verbose output
            self._model = vosk.Model(self.model_path)
            logger.info("Vosk STT model loaded.")
        except Exception as e:
            logger.error(f"Vosk model load failed: {e}")

    def _transcribe_stream(self, duration_secs: float = None, stop_on_silence: bool = False) -> str:
        """
        Internal: Open microphone, run Vosk recogniser, return transcript.
        If stop_on_silence=True, recording stops after SILENCE_LIMIT seconds of quiet.
        If duration_secs is set, records for exactly that many seconds.
        """
        if not self._model:
            # ── Fallback: keyboard input ───────────────────────────────────
            return input("(Type your command — STT unavailable): ").strip()

        rec = vosk.KaldiRecognizer(self._model, self.SAMPLE_RATE)
        result_text = ""
        audio_queue: queue.Queue = queue.Queue()
        last_sound_time = time.time()
        start_time = time.time()

        def audio_callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"Audio status: {status}")
            audio_queue.put(bytes(indata))

        try:
            with sd.RawInputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=self.BLOCK_SIZE,
                dtype="int16",
                channels=1,
                callback=audio_callback,
            ):
                while True:
                    # ── Timeout checks ────────────────────────────────────
                    elapsed = time.time() - start_time
                    if duration_secs and elapsed >= duration_secs:
                        break
                    if stop_on_silence and (time.time() - last_sound_time) > self.SILENCE_LIMIT:
                        break

                    # ── Process audio chunk ───────────────────────────────
                    try:
                        data = audio_queue.get(timeout=0.3)
                    except queue.Empty:
                        continue

                    if rec.AcceptWaveform(data):
                        part = json.loads(rec.Result()).get("text", "")
                        if part:
                            result_text += " " + part
                            last_sound_time = time.time()  # reset silence timer
                    else:
                        partial = json.loads(rec.PartialResult()).get("partial", "")
                        if partial:
                            last_sound_time = time.time()

            # Grab any final words
            final = json.loads(rec.FinalResult()).get("text", "")
            if final:
                result_text += " " + final

        except Exception as e:
            logger.error(f"Audio stream error: {e}")

        return result_text.strip()

    def wait_for_wake_word(self, timeout_secs: float = 5.0) -> bool:
        """
        Listen for the wake word for `timeout_secs` seconds.
        Returns True if wake word was heard, False otherwise.
        """
        transcript = self._transcribe_stream(duration_secs=timeout_secs)
        if self.wake_word in transcript.lower():
            logger.info(f"Wake word '{self.wake_word}' detected in: '{transcript}'")
            return True
        return False

    def listen_for_command(self, timeout_secs: float = 10.0) -> str:
        """
        Listen for a user command. Records until silence or timeout.
        Returns the transcribed text.
        """
        logger.info("Listening for command...")
        transcript = self._transcribe_stream(
            duration_secs=timeout_secs,
            stop_on_silence=True,
        )
        logger.info(f"Transcribed: '{transcript}'")
        return transcript
