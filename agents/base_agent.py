from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.conversation_history = []
        self.available_tools = {}

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Returns the system prompt for the agent."""
        pass

    @abstractmethod
    def process_transcript(self, transcript: str) -> str:
        """Processes user input and returns a response."""
        pass

    def get_tools(self) -> list:
        """Returns a list of tool definitions for the LLM."""
        return [tool["spec"] for tool in self.available_tools.values()]

    def register_tool(self, spec: dict, handler: callable):
        """Registers a tool and its handler function."""
        name = spec["function"]["name"]
        self.available_tools[name] = {
            "spec": spec,
            "handler": handler
        }

    def execute_tool(self, name: str, arguments: dict):
        """Executes a registered tool handler."""
        if name in self.available_tools:
            print(f"[TOOL] Executing {name} with args: {arguments}")
            return self.available_tools[name]["handler"](**arguments)
        else:
            print(f"[TOOL ERROR] Tool {name} not found.")
            return f"Error: Tool {name} not found."

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > 20:  # Keep window size manageable
            self.conversation_history.pop(1)  # Keep system prompt at [0]
