from abc import ABC, abstractmethod
from typing import List, Dict

class MemoryPort(ABC):
    @abstractmethod
    def save_message(self, role: str, content: str) -> None:
        pass

    @abstractmethod
    def get_history(self, limit: int = 20) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def clear_history(self) -> None:
        pass
