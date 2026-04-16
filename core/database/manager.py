import psycopg2
import threading
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
import gridfs
from supabase import create_client
from config.settings import settings

class DatabaseManager:
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.fs = None
        self.supabase_client = None
        self.db_uri = settings.SUPABASE_DB_URI
        
        # 🧵 Lazy Init: Start connections in background to avoid hanging the app boot
        print("[TRACE] Starting Database initialization threads...")
        threading.Thread(target=self._init_mongo, daemon=True).start()
        threading.Thread(target=self._init_supabase, daemon=True).start()

    def _init_mongo(self):
        print("[TRACE] Attempting to connect to MongoDB...")
        try:
            self.mongo_client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
            self.mongo_client.server_info()
            self.db = self.mongo_client[settings.DATABASE_NAME]
            self.fs = gridfs.GridFS(self.db)
            print("[INFO] MongoDB connected successfully.")
        except Exception as e:
            print(f"[WARN] MongoDB connection failed (Non-blocking): {e}")
            self.mongo_client = None

    def _init_supabase(self):
        print("[TRACE] Attempting to connect to Supabase Client...")
        try:
            self.supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            print("[INFO] Supabase Client initialized.")
        except Exception as e:
            print(f"[WARN] Supabase connection failed (Non-blocking): {e}")
            self.supabase_client = None

    def save_audio_to_mongo(self, file_path, original_filename, timestamp):
        if not self.fs:
            print("[WARN] GridFS not initialized. Cannot save audio.")
            return None
            
        try:
            with open(file_path, "rb") as f:
                file_id = self.fs.put(
                    f, 
                    filename=original_filename,
                    timestamp=timestamp, 
                    contentType="audio/wav"
                )
            return file_id
        except Exception as e:
            print(f"[ERROR] Failed to save to MongoDB: {e}")
            return None

    def fetch_knowledge_docs(self):
        if not self.supabase_client:
            return []
            
        try:
            response = self.supabase_client.table("website_knowledge").select("id,url,title,content,embedding").execute()
            return response.data or []
        except Exception as e:
            print(f"[ERROR] Failed to fetch from Supabase: {e}")
            return []

    def search_knowledge_rpc(self, query_embedding, match_threshold=0.5, match_count=5):
        """Uses the direct Postgres connection to execute the match_documents function."""
        if not self.db_uri:
            print("[WARN] SUPABASE_DB_URI not set. Falling back to fetch_knowledge_docs (slow).")
            return []
            
        try:
            # Convert numpy array to list for Postgres
            if hasattr(query_embedding, "tolist"):
                query_embedding = query_embedding.tolist()
            
            with psycopg2.connect(self.db_uri) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM match_documents(%s::vector, %s, %s)",
                        (query_embedding, match_threshold, match_count)
                    )
                    results = cur.fetchall()
            return results
        except Exception as e:
            print(f"[ERROR] Direct Postgres search failed: {e}")
            return []
