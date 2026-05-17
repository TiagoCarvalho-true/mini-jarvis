from abc import ABC, abstractmethod
from typing import List, Optional

class VisionPort(ABC):
    @abstractmethod
    def start(self) -> None:
        """Inicia a thread de captura continua (se suportado)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Encerra a thread de captura."""
        pass

    @abstractmethod
    def get_detected_user(self) -> Optional[str]:
        """Retorna o nome do ultimo usuario detectado."""
        pass

    @abstractmethod
    def check_once(self) -> Optional[str]:
        """Realiza uma deteccao unica (modo on_demand)."""
        pass

    @abstractmethod
    def register_face(self, name: str, image_data: bytes) -> bool:
        """Cadastra um novo rosto no sistema."""
        pass

    @abstractmethod
    def list_registered_faces(self) -> List[str]:
        """Lista nomes dos rostos cadastrados."""
        pass
