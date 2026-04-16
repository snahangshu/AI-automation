import os
import wave
import tempfile
import threading
import time
import pygame
from playsound import playsound
from datetime import datetime
from config.settings import settings

class AudioHandler:
    _playback_thread = None
    _abort_playback = False

    @staticmethod
    def save_wav(frames: list, filename: str = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"call_{timestamp}.wav"
        
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp.name
        tmp.close()
        
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(settings.CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(settings.SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
        
        return tmp_path, filename

    @staticmethod
    def play_audio(file_path: str, delete_after: bool = True):
        """Plays audio in a background thread to allow interruptions."""
        AudioHandler.stop_audio() # Stop any existing playback
        AudioHandler._abort_playback = False
        
        def _play():
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    if AudioHandler._abort_playback:
                        pygame.mixer.music.stop()
                        break
                    pygame.time.Clock().tick(20)
                
                try:
                    pygame.mixer.music.unload()
                except:
                    pass
            except Exception as e:
                print(f"[ERROR] Pygame playback failed: {e}")
            finally:
                if delete_after and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass

        AudioHandler._playback_thread = threading.Thread(target=_play, daemon=True)
        AudioHandler._playback_thread.start()

    @staticmethod
    def stop_audio():
        """Immediately stops any ongoing audio playback."""
        AudioHandler._abort_playback = True
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.stop()
        except:
            pass
