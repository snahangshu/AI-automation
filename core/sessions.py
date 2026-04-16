from datetime import datetime
from config.settings import settings

class SessionManager:
    def __init__(self, db_manager):
        self.db = db_manager.db # MongoDB Database object
        self.collection = self.db["chat_sessions"] if self.db is not None else None

    def get_history(self, session_id: str) -> list:
        if self.collection is None:
            return []
            
        session = self.collection.find_one({"session_id": session_id})
        if session:
            return session.get("history", [])
        return []

    def save_message(self, session_id: str, role: str, content: str):
        if self.collection is None:
            print("[WARN] SessionManager: MongoDB not available. History not saved.")
            return

        # Ensure history starts with the appropriate role (user/assistant)
        # We don't save system prompts to the DB usually to keep it clean, 
        # but we can if preferred.
        
        self.collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"history": {"role": role, "content": content, "timestamp": datetime.now()}},
                "$set": {"last_active": datetime.now()}
            },
            upsert=True
        )

    def clear_session(self, session_id: str):
        if self.collection is not None:
            self.collection.delete_one({"session_id": session_id})

    def get_all_active_sessions(self, limit: int = 50):
        if self.collection is None:
            return []
        return list(self.collection.find().sort("last_active", -1).limit(limit))
