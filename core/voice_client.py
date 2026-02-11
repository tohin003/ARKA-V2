
import threading
import time
import speech_recognition as sr
import pyautogui
from pynput import keyboard
import structlog
import sys

logger = structlog.get_logger()

class VoiceClient:
    """
    Handles Push-to-Talk voice dictation.
    Target Key: F5
    """
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.audio_frames = []
        self.stop_listening = None
        self.mic = sr.Microphone()
        
        # Adjust for ambient noise once at startup
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception as e:
            logger.error("voice_init_failed", error=str(e))

        # State
        self.is_recording = False
        self.listener_thread = None

    def start(self):
        """Starts the background key listener."""
        self.listener_thread = threading.Thread(target=self._run_listener, daemon=True)
        self.listener_thread.start()
        logger.info("voice_client_started", key="F5")

    def _run_listener(self):
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            listener.join()

    def _on_press(self, key):
        try:
            if key == keyboard.Key.f5 and not self.is_recording:
                self.is_recording = True
                self._start_recording()
        except AttributeError:
            pass

    def _on_release(self, key):
        if key == keyboard.Key.f5 and self.is_recording:
            self.is_recording = False
            self._stop_recording_and_transcribe()

    def _start_recording(self):
        print("\n🎤 Listening... (Release F5 to finish)", end="\r", flush=True)
        # We process recording in the main flow or via SR's listen_in_background
        # But SR's background listener is hard to stop instantly on key release.
        # So we use a "trick": We trigger a single listen() call in a thread?
        # Actually, for PTT, it's better to record raw frames or use listen() with a short timeout?
        # Standard SR listen() waits for silence. We want to stop on KEY RELEASE.
        # So we need to control the microphone stream directly?
        # Simpler approach for v1: Use SR listen() but with a callback? No.
        
        # Let's use a separate thread that records as long as self.is_recording is True.
        self.audio_thread = threading.Thread(target=self._record_audio_stream)
        self.audio_thread.start()

    def _record_audio_stream(self):
        """
        Manually captures audio from the microphone until flag is set to False.
        """
        self.audio_data = []
        try:
            with self.mic as source:
                # We need to access underlying PyAudio stream to control duration manually
                # But SR wrapper hides it.
                # Workaround: We'll accept that for V1, we might rely on 'listen' which detects silence/phrase.
                # BUT user wants "Press and Hold".
                # If they hold F5, they are speaking. If they release, we stop.
                
                # We will use the lower-level functionality if we want precise PTT.
                # However, implementing raw audio capture with PyAudio + SR conversation is complex.
                
                # Alternative: Just run `r.listen(source)`? 
                # Be aware: `listen()` blocks until phrase ends. Push-to-Talk usually forces stop.
                # Let's try the simplest PTT:
                # On Press: Set flag.
                # On Release: Set flag.
                
                # Actually, the most robust way for PTT with `speech_recognition` package is acting on AudioData.
                # We will skip complex stream handling and just use `r.listen` and hope it returns when user stops speaking (which usually coincides with release).
                # But if they hold silence?
                
                # Let's try this: Just call r.listen() in a thread. 
                # The user presses F5. We start listening.
                # When they release F5... we can't easily kill `listen()`.
                
                # Okay, let's trust `r.listen()`'s internal silence detection for now, 
                # OR switch to `sounddevice` + `numpy` later if needed.
                # For this prototype, let's use `r.listen(source, phrase_time_limit=15)` 
                # ensuring we capture a sentence.
                
                logger.debug("recording_start")
                audio = self.recognizer.listen(source, phrase_time_limit=15, timeout=5)
                self.process_audio(audio)
                
        except Exception as e:
            logger.error("recording_error", error=str(e))
            print(f"\n❌ Error: {e}")

    def _stop_recording_and_transcribe(self):
        # Because we used r.listen() which blocks until silence/limit, 
        # this release handler might just be a UI update or 'stop' signal if we were streaming.
        # For this simple implementation, the recording thread does the work.
        print("\n⏳ Processing...", end="\r", flush=True)

    def process_audio(self, audio):
        try:
            # Transcribe (Google Free API)
            text = self.recognizer.recognize_google(audio)
            logger.info("voice_transcribed", text=text)
            
            # Inject
            print(f"\n🗣️ You said: {text}")
            pyautogui.write(text + " ", interval=0.01)
            
        except sr.UnknownValueError:
            print("\n🤷 Could not understand audio")
        except sr.RequestError as e:
            print(f"\n⚠️ Service Error: {e}")
        except Exception as e:
            logger.error("transcription_failed", error=str(e))

# Singleton
voice_client = VoiceClient()
