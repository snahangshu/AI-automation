import os
import asyncio
import edge_tts
from gtts import gTTS
from config.settings import settings

class TTSEngine:
    def __init__(self):
        # We no longer need ElevenLabs API keys for high quality
        # Neerja is a high-quality free Indian English voice
        self.voice = "en-IN-NeerjaNeural" 
        self.temp_dir = "temp_audio"
        os.makedirs(self.temp_dir, exist_ok=True)

    def generate_audio(self, text: str) -> str:
        """Generates high-quality audio using Edge-TTS with gTTS fallback."""
        timestamp = int(os.times()[4]) # simple timestamp
        output_path = os.path.join(self.temp_dir, f"speech_{timestamp}.mp3")
        
        try:
            print(f"[TTS] Generating speech with Edge-TTS (Voice: {self.voice})...")
            
            # The edge-tts library is async. We use a dedicated event loop to run it synchronously
            # Rate +20% makes the interaction feel snappier.
            async def _save():
                communicate = edge_tts.Communicate(text, self.voice, rate="+20%")
                await communicate.save(output_path)
            
            asyncio.run(_save())
            return output_path
            
        except Exception as e:
            print(f"[WARN] Edge-TTS failed: {e}. Falling back to gTTS...")
            try:
                # Detect Hindi characters to switch gTTS language
                lang = "hi" if any("\u0900" <= c <= "\u097f" for c in text) else "en"
                tts = gTTS(text=text, lang=lang)
                fallback_path = os.path.join(self.temp_dir, f"fallback_{timestamp}.mp3")
                tts.save(fallback_path)
                return fallback_path
            except Exception as e2:
                print(f"[ERROR] TTS Fallback also failed: {e2}")
                return ""
