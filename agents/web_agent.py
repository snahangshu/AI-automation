from agents.base_agent import BaseAgent
from core.llm import LLMEngine
from core.rag import RAGEngine
from core.sessions import SessionManager
from utils.google_sheets import SheetManager
from config.settings import settings

class WebChatbotAgent(BaseAgent):
    def __init__(self, db_manager):
        super().__init__(name="Fastigo Web Agent")
        self.llm = LLMEngine()
        self.rag = RAGEngine(db_manager)
        self.sessions = SessionManager(db_manager)
        self.sheets = SheetManager()
        
        # We don't use self.conversation_history here since it's multi-session
        # We fetch it from SessionManager instead.
        
        self._register_tools()

    def _register_tools(self):
        lead_tool = {
            "type": "function",
            "function": {
                "name": "submit_lead",
                "description": "Captures user contact info and their specific service interests or budget requirements.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "User's full name."},
                        "service": {"type": "string", "enum": ["AI Service", "CRM Portal", "Cybersecurity", "Custom Tech"], "description": "The category of service they are interested in."},
                        "details": {"type": "string", "description": "Budget, specific requirements, or customization details."},
                        "session_id": {"type": "string", "description": "The current session ID (pass this exactly as received)."}
                    },
                    "required": ["name", "service", "details", "session_id"]
                }
            }
        }
        self.register_tool(lead_tool, self.handle_lead_capture)

    def handle_lead_capture(self, name: str, service: str, details: str, session_id: str):
        success = self.sheets.capture_lead(name, service, details, session_id)
        if success:
            return f"Thank you {name}, I've recorded your interest in {service} with the following details: {details}. Our team will get back to you soon!"
        return "I'm sorry, I couldn't record those details right now. Could you please try again later?"

    def get_system_prompt(self) -> str:
        return (
            "You are the Fastigo Technology Solutions Architect. Your role is to guide users through our custom tech services: "
            "AI Agent development, CRM Portals, Enterprise Cybersecurity, and general custom software solutions. "
            "1. Use the provided context from our website to answer technical and service-related questions. "
            "2. If a user shows interest in a build, ask for their name, the type of service they want, and their budget/specifications. "
            "3. Once you have these details, use the 'submit_lead' tool to save their information. "
            "IMPORTANT: DO NOT USE MARKDOWN OR SPECIAL FORMATTING. Do not use bold (**) symbols, headers (#), or bullet points with symbols. "
            "Provide responses in plain, clean, and conversational text. Use standard punctuation only."
        )

    def _clean_text(self, text: str) -> str:
        """Removes common markdown artifacts for a cleaner plain-text output."""
        import re
        # Remove bold/italic markers
        text = re.sub(r'\*\*|\*|__|_', '', text)
        # Remove header markers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # Clean up double newlines but keep single ones if they are meant for paragraphs
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def process_transcript(self, transcript: str, session_id: str = "default") -> str:
        # 1. Fetch History
        history = self.sessions.get_history(session_id)
        
        # 2. Retrieve Context (RAG)
        context = self.rag.retrieve_context(transcript, top_k=5)
        
        # 3. Build Messages
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "system", "content": f"Session Context (Current Session ID: {session_id})\nKnowledge Snippets:\n{context}"}
        ]
        
        # Add history (convert format if needed - MongoDB stored as {'role', 'content'})
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
            
        messages.append({"role": "user", "content": transcript})
        
        # 4. Get Response
        response = self.llm.get_completion(
            messages, 
            tools=self.get_tools(),
            agent_ref=self
        )
        
        # 🧩 Clean Response (Remove markdown artifacts)
        response = self._clean_text(response)
        
        # 5. Persistent Session
        self.sessions.save_message(session_id, "user", transcript)
        self.sessions.save_message(session_id, "assistant", response)
        
        return response
