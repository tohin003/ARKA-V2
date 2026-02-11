from smolagents import tool
from core.memory import MemoryManager

@tool
def remember_fact(fact: str) -> str:
    """
    Learns a new fact about the user or the system and saves it to long-term memory.
    Use this proactively when the user states a preference (e.g., "I like dark mode", "My API key is X").
    
    Args:
        fact: The fact to remember (e.g., "User prefers Python over JS").
    """
    memory = MemoryManager()
    return memory.append_fact(fact)
