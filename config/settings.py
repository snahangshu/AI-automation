import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    # API Keys
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_DB_URI = os.getenv("SUPABASE_DB_URI")
    
    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    DATABASE_NAME = "ai_receptionist"
    
    # LLM Settings
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1800))
    TOP_K = int(os.getenv("TOP_K", 4))
    MODEL_FOR_CHAT = os.getenv("MODEL_FOR_CHAT", "gpt-4o-mini")
    EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
    
    # Audio Settings
    SAMPLE_RATE = 16000
    FRAMES_PER_BUFFER = 800
    CHANNELS = 1
    
settings = Settings()
