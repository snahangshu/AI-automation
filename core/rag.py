import numpy as np
import threading
from sentence_transformers import SentenceTransformer
from config.settings import settings
from utils.tokens import TokenHandler

class RAGEngine:
    def __init__(self, db_manager):
        self.db = db_manager
        self.model = None
        self.is_ready = False
        
        # 🧵 Lazy Init: Loading models can take time/hang, do it in background
        print("[TRACE] Initializing RAG background loading...")
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        print("[TRACE] Attempting to load embedding model...")
        try:
            self.model = SentenceTransformer(settings.EMBED_MODEL_NAME)
            self.is_ready = True
            print("[INFO] Embedding model loaded and RAG is ready.")
        except Exception as e:
            print(f"[ERROR] Failed to load embedding model: {e}")

    def get_query_embedding(self, query: str) -> np.ndarray:
        if not self.is_ready:
            print("[WARN] RAG not ready yet, model still loading. Using zero-vector (fallback).")
            return np.zeros(384, dtype=np.float32)
        return self.model.encode(query).astype(np.float32)

    def retrieve_context(self, query: str, top_k: int = settings.TOP_K) -> str:
        qvec = self.get_query_embedding(query)
        
        # 🧩 FIX: Use optimized RPC search instead of fetching all docs
        docs = self.db.search_knowledge_rpc(qvec, match_count=top_k)
        
        if not docs:
            return "No relevant knowledge found."

        context_parts = []
        total_tokens = 0
        for d in docs:
            snippet = d.get("content", "").strip()
            # Handle potential metadata block if it's there
            title = d.get('title') or d.get('metadata', {}).get('title', 'Unknown Source')
            url = d.get('url') or d.get('metadata', {}).get('url', 'N/A')
            
            block = f"Source: {title}\nURL: {url}\n{snippet}\n---\n"
            block_tokens = TokenHandler.count_tokens(block)
            
            if total_tokens + block_tokens > settings.MAX_TOKENS:
                break
                
            context_parts.append(block)
            total_tokens += block_tokens
            
        return "\n".join(context_parts) if context_parts else "No relevant knowledge found."

    def get_raw_results(self, query: str, top_k: int = 10) -> list:
        """Returns raw doc objects for the Filtering Agent to process."""
        qvec = self.get_query_embedding(query)
        return self.db.search_knowledge_rpc(qvec, match_count=top_k)
