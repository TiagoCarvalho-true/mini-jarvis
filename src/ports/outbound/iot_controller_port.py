from abc import ABC, abstractmethod
from typing import List, Dict

class IoTControllerPort(ABC):
    @abstractmethod
    def send_command(self, device_id: str, action: str) -> Dict:
        """Envia um comando para um dispositivo IoT especifico."""
        pass

    @abstractmethod
    def get_status(self, device_id: str) -> Dict:
        """Consulta o status de um dispositivo IoT."""
        pass

    @abstractmethod
    def list_devices(self) -> List[Dict]:
        """Lista todos os dispositivos registrados."""
        pass
