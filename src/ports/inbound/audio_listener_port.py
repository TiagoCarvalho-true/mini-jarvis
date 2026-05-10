from abc import ABC, abstractmethod

class AudioListenerPort(ABC):
    @abstractmethod
    def listen_for_wake_word(self) -> bool:
        pass

    @abstractmethod
    def listen_for_command(self) -> str:
        pass
