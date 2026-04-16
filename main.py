import time
import json
import threading
import os
import pyaudio
from datetime import datetime
from config.settings import settings
from core.stt import STTEngine
from core.tts import TTSEngine
from core.database.manager import DatabaseManager
from agents.dora import DoraAgent
from utils.audio import AudioHandler

class AIReceptionist:
    def __init__(self):
        print("[TRACE] Initializing AIReceptionist components...")
        
        print("[TRACE] Creating DatabaseManager...")
        self.db = DatabaseManager()
        
        print("[TRACE] Creating DoraAgent...")
        self.agent = DoraAgent(self.db)
        
        print("[TRACE] Creating TTSEngine...")
        self.tts = TTSEngine()
        
        # Audio State
        print("[TRACE] Initializing PyAudio...")
        try:
            self.audio = pyaudio.PyAudio()
            print("[INFO] PyAudio initialized.")
        except Exception as e:
            print(f"[ERROR] PyAudio initialization failed: {e}")
            self.audio = None
        
        self.stream = None
        self.recorded_frames = []
        self.recording_lock = threading.Lock()
        
        # Control flags
        self.paused = False
        self.speaking = False
        self.stop_event = threading.Event()
        
        # Initialize STT
        print("[TRACE] Initializing STTEngine...")
        self.stt = STTEngine(
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        print("[TRACE] STTEngine created.")

    def start(self):
        # Open microphone
        self.stream = self.audio.open(
            input=True,
            frames_per_buffer=settings.FRAMES_PER_BUFFER,
            channels=settings.CHANNELS,
            format=pyaudio.paInt16,
            rate=settings.SAMPLE_RATE
        )
        print("[INFO] Microphone started. AI Receptionist active.")
        
        # Start STT
        self.stt.start()
        
        # 🎤 Initial greeting
        greeting_text = "Hello! I am Dora, your AI receptionist. How can I help you today?"
        print(f"[DORA]: {greeting_text}")
        threading.Thread(target=self.speak, args=(greeting_text,), daemon=True).start()
        
        # Main loop
        try:
            threading.Thread(target=self._audio_loop, daemon=True).start()
            while not self.stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def _audio_loop(self):
        while not self.stop_event.is_set():
            if self.paused: # We only pause for state transitions, not for speaking anymore
                time.sleep(0.01)
                continue
            
            try:
                data = self.stream.read(settings.FRAMES_PER_BUFFER, exception_on_overflow=False)
                with self.recording_lock:
                    self.recorded_frames.append(data)
                
                # Continuous stream to STT - Barge-in depends on this
                self.stt.send_audio(data)
            except Exception as e:
                print(f"[ERROR] Audio capture error: {e}")
                break

    def on_message(self, ws, message):
        data = json.loads(message)
        if data.get("type") == "Turn":
            transcript = data.get("transcript", "").strip()
            is_final = bool(data.get("turn", {}).get("is_final", False))
            
            if not transcript:
                return

            # 🛑 BARGE-IN: If user speaks while Dora is speaking, interrupt her
            if self.speaking:
                print(f"[INTERRUPT] User said: '{transcript}'")
                self.interrupt()
                # We prioritize the new user input instantly
                if is_final:
                    self.process_and_reply(transcript)
                return

            now = time.time()
            if is_final and (now - self.last_reply_ts > self.MIN_REPLY_DEBOUNCE):
                print(f"[USER]: {transcript}")
                self.last_reply_ts = now
                threading.Thread(target=self.process_and_reply, args=(transcript,), daemon=True).start()

    def interrupt(self):
        """Halt playback and reset speaking state."""
        from utils.audio import AudioHandler
        AudioHandler.stop_audio()
        self.speaking = False
        self.paused = False

    def speak(self, text):
        """Generates and plays TTS for the given text."""
        self.speaking = True
        # self.paused = True # Don't pause recording while speaking
        
        audio_path = self.tts.generate_audio(text)
        if audio_path:
            from utils.audio import AudioHandler
            AudioHandler.play_audio(audio_path)
            
        # We don't wait for busy here as play_audio is now async
        # The AudioHandler will manage its own thread.

    def process_and_reply(self, transcript):
        # 1. Get Agent Response
        response = self.agent.process_transcript(transcript)
        print(f"[DORA]: {response}")
        
        # 2. TTS
        self.speak(response)

    def on_error(self, ws, error):
        print(f"[STT ERROR]: {error}")

    def on_close(self, ws, code, msg):
        print(f"[STT CLOSED]: {code} - {msg}")
        self._save_session()

    def _save_session(self):
        if self.recorded_frames:
            temp_path, filename = AudioHandler.save_wav(self.recorded_frames)
            file_id = self.db.save_audio_to_mongo(temp_path, filename, datetime.now().isoformat())
            print(f"[INFO] Session audio saved with ID: {file_id}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def stop(self):
        self.stop_event.set()
        self.stt.stop()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        print("[INFO] AI Receptionist stopped.")

if __name__ == "__main__":
    from datetime import datetime
    receptionist = AIReceptionist()
    receptionist.start()
