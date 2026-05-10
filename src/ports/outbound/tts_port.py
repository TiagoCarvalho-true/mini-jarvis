from abc import ABC, abstractmethod

class TTSPort(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        pass
