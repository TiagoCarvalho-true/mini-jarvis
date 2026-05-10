from abc import ABC, abstractmethod
from typing import List, Dict

class LLMPort(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        pass
