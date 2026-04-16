from agents.base_agent import BaseAgent
from agents.filter_agent import FilterAgent
from core.llm import LLMEngine
from core.rag import RAGEngine

class DoraAgent(BaseAgent):
    def __init__(self, db_manager):
        super().__init__(name="Dora")
        self.llm = LLMEngine()
        self.rag = RAGEngine(db_manager)
        self.filter_agent = FilterAgent()
        
        self.company_info = (
            "Fastigo Technology Private Limited is an Indian technology company specializing in AI agents, "
            "customized software solutions, and enterprise-grade cybersecurity systems."
        )
        
        # Register Tools
        self._register_tools()
        
        # Initial history with system prompt
        self.add_to_history("system", self.get_system_prompt())

    def _register_tools(self):
        appointment_tool = {
            "type": "function",
            "function": {
                "name": "Freeby Helper regarding tech",
                "description": "Helps ti identify the issue and provide the best solution.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date_time": {"type": "string", "description": "ISO format date and time string."},
                        "reason": {"type": "string", "description": "The reason for the meeting."},
                        "caller_name": {"type": "string", "description": "The name of the caller."}
                    },
                    "required": ["date_time", "reason"]
                }
            }
        }
        self.register_tool(appointment_tool, self.book_appointment)

    def book_appointment(self, date_time: str, reason: str, caller_name: str = "Unknown"):
        """Internal handler for booking appointments."""
        # For now, we mock the successful booking
        print(f"[ACTION] Booking appointment for {caller_name} at {date_time} for: {reason}")
        return f"Successfully booked appointment for {date_time}. Reference ID: FAST-{date_time[:4]}-99."

    def get_system_prompt(self) -> str:
        return (
            "You are Dora, a professional tech-support receptionist at Fastigo. "
            "Your role is to help users identify their technical issues and provide the best solutions. "
            "You speak with a sophisticated Indian English accent. Use professional terms and be warm. "
            "Use provided knowledge snippets to give accurate technical advice. "
            "You can use the 'Freeby Helper' tool to log technical issues and provide solutions."
        )

    def process_transcript(self, transcript: str) -> str:
        # Detect language hint (simple heuristic)
        lang_hint = "English"
        hindi_keywords = ["namaste", "kaise", "aap", "tum", "kya", "madad"]
        if any(word in transcript.lower() for word in hindi_keywords):
            lang_hint = "Mixed Hinglish/Hindi"
        
        # 🧩 MULTI-AGENT PIPELINE:
        # 1. Retrieve Raw Results
        raw_docs = self.rag.get_raw_results(transcript, top_k=6)
        
        # 2. Filter via FilterAgent (The "Critic")
        filtered_docs = self.filter_agent.validate_docs(transcript, raw_docs)
        
        # 3. Construct Context from vetted docs
        context = ""
        for d in filtered_docs:
            context += f"Source: {d.get('title')}\n{d.get('content')}\n---\n"
        
        if not context:
            context = "No specific knowledge found. Answer based on company profile or offer escalation."
        
        # 4. Build Messages for Synthesis
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "system", "content": f"Language Tone: {lang_hint}"},
            {"role": "system", "content": f"Company Profile: {self.company_info}"},
            {"role": "system", "content": f"Verified Knowledge:\n{context}"}
        ]
        
        # Add recent history (excluding the first system prompt)
        messages.extend(self.conversation_history[1:])
        messages.append({"role": "user", "content": transcript})
        
        # 5. Get LLM Response (with Tool support)
        response = self.llm.get_completion(
            messages, 
            tools=self.get_tools(),
            agent_ref=self
        )
        
        # 6. Update History
        self.add_to_history("user", transcript)
        self.add_to_history("assistant", response)
        
        return response
