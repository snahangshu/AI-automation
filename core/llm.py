from openai import OpenAI
from huggingface_hub import InferenceClient
from config.settings import settings

class LLMEngine:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.hf_client = InferenceClient("facebook/blenderbot-400M-distill")

    def get_completion(self, messages: list, model: str = settings.MODEL_FOR_CHAT, tools: list = None, agent_ref=None) -> str:
        try:
            params = {
                "model": model,
                "messages": messages,
                "temperature": 0.35,
                "max_tokens": 700
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
                
            response = self.openai_client.chat.completions.create(**params)
            msg = response.choices[0].message
            
            # Handle Tool Calls
            if msg.tool_calls and agent_ref:
                messages.append(msg) # Add assistant's tool call to history
                
                for tool_call in msg.tool_calls:
                    function_name = tool_call.function.name
                    import json
                    args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    result = agent_ref.execute_tool(function_name, args)
                    
                    # Provide result back to LLM
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(result)
                    })
                
                # Recursive call to get final response after tool execution
                return self.get_completion(messages, model, tools, agent_ref)
                
            return msg.content.strip()
        except Exception as e:
            print(f"[ERROR] OpenAI completion failed: {e}. Falling back to HuggingFace...")
            return self.get_hf_fallback(messages[-1]["content"])

    def get_hf_fallback(self, prompt: str) -> str:
        try:
            response = self.hf_client.text_generation(
                prompt,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7
            )
            return response
        except Exception as e:
            print(f"[ERROR] HuggingFace fallback failed: {e}")
            return "Mujhe maaf kijiye, abhi main aapke prashn ka uttar nahi de paa rahi hoon."
