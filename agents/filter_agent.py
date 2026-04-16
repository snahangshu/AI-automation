from agents.base_agent import BaseAgent
from core.llm import LLMEngine
import json

class FilterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="KnowledgeValidator")
        self.llm = LLMEngine()

    def get_system_prompt(self) -> str:
        return (
            "You are a critical Knowledge Validator. Your job is to review a set of retrieved documents "
            "and decide which ones are TRULY relevant to the user's specific query. "
            "Discard documents that are generic, outdated, or unrelated. "
            "Output ONLY a JSON list of indices of the documents to KEEP. "
            "Example: [0, 2]"
        )

    def validate_docs(self, query: str, docs: list) -> list:
        if not docs:
            return []
            
        doc_summaries = ""
        for i, d in enumerate(docs):
            doc_summaries += f"[{i}] {d.get('content')[:200]}...\n"
            
        prompt = (
            f"User Query: {query}\n\n"
            f"Retrieved Documents:\n{doc_summaries}\n\n"
            "Evaluate relevance and output the JSON list of indices to keep."
        )
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.get_completion(messages)
            # Extact JSON from response if LLM added fluff
            if "[" in response and "]" in response:
                response = response[response.find("["):response.rfind("]")+1]
            
            indices = json.loads(response)
            filtered_docs = [docs[i] for i in indices if i < len(docs)]
            print(f"[FILTER] Kept {len(filtered_docs)}/{len(docs)} documents.")
            return filtered_docs
        except Exception as e:
            print(f"[FILTER ERROR] Validation failed: {e}. Returning all docs as fallback.")
            return docs

    def process_transcript(self, transcript: str) -> str:
        # Filter agent doesn't talk to humans directly
        return ""
