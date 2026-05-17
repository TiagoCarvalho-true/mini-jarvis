import aiohttp
import asyncio
import json
import os
from typing import List, Dict, Optional
from src.ports.outbound.iot_controller_port import IoTControllerPort
from src.domain.entities import IoTDevice

class ESP32Adapter(IoTControllerPort):
    def __init__(self):
        self.mock_mode = os.getenv("ESP32_MOCK", "true").lower() == "true"
        self.devices: Dict[str, IoTDevice] = {}
        self._load_devices()

    def _load_devices(self):
        nodes_json = os.getenv("ESP32_NODES", "[]")
        try:
            nodes = json.loads(nodes_json)
            for node in nodes:
                device = IoTDevice(
                    id=node["id"],
                    name=node["name"],
                    ip=node["ip"]
                )
                self.devices[device.id] = device
            print(f"[IOT] {len(self.devices)} dispositivos carregados.")
        except Exception as e:
            print(f"[IOT] Erro ao carregar dispositivos do .env: {e}")

    async def _send_request(self, ip: str, path: str, method="POST", data=None) -> Dict:
        if self.mock_mode:
            print(f"[IOT MOCK] {method} para http://{ip}{path} com {data}")
            return {"status": "success", "mock": True}

        url = f"http://{ip}{path}"
        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, json=data, timeout=3) as resp:
                        return await resp.json()
                else:
                    async with session.get(url, timeout=3) as resp:
                        return await resp.json()
        except Exception as e:
            print(f"[IOT] Erro na comunicacao com {ip}: {e}")
            return {"status": "error", "message": str(e)}

    def send_command(self, device_id: str, action: str) -> Dict:
        if device_id not in self.devices:
            return {"status": "error", "message": "Dispositivo nao encontrado"}
        
        device = self.devices[device_id]
        # Exemplo de mapeamento: "on" -> "/relay/1/on"
        path = f"/relay/1/{action}"
        
        # Como o send_command da Port e sincrono mas aiohttp e async,
        # usamos um loop interno ou transformamos em async se necessario.
        # Para simplificar aqui, vamos rodar de forma sincrona:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._send_request(device.ip, path))

    def get_status(self, device_id: str) -> Dict:
        if device_id not in self.devices:
            return {"status": "error", "message": "Dispositivo nao encontrado"}
        
        device = self.devices[device_id]
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._send_request(device.ip, "/status", method="GET"))

    def list_devices(self) -> List[Dict]:
        return [
            {"id": d.id, "name": d.name, "ip": d.ip, "status": d.status}
            for d in self.devices.values()
        ]
