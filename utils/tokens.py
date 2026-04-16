import tiktoken
from config.settings import settings

class TokenHandler:
    @staticmethod
    def count_tokens(text: str, model_name: str = settings.MODEL_FOR_CHAT) -> int:
        try:
            enc = tiktoken.encoding_for_model(model_name)
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))

    @staticmethod
    def truncate_context(text: str, max_tokens: int = settings.MAX_TOKENS) -> str:
        """
        Truncates text to fit within max_tokens. 
        Uses a simple character-based heuristic first, then checks with tokenizer.
        """
        # Quick check
        if TokenHandler.count_tokens(text) <= max_tokens:
            return text
            
        # Truncate heuristic (approx 4 chars per token)
        allowed_chars = max_tokens * 4
        return text[:allowed_chars] + "..."
