import json
import re
from typing import Optional
from src.domain.entities import Intent

class IntentParser:
    """Classificador de intenção LOCAL por palavras-chave.
    Não usa a API LLM, economizando chamadas e evitando 429."""
    
    def __init__(self, llm_port=None):
        # LLM não é mais necessário para classificação
        self.llm = llm_port
        
        # Palavras-chave para comandos IoT
        self.iot_keywords = {
            "desligar": "off", "desligue": "off", "desativar": "off", "desative": "off",
            "apagar": "off", "apague": "off", "fechar": "off", "feche": "off",
            "ligar": "on", "ligue": "on", "acender": "on", "acenda": "on",
            "ativar": "on", "ative": "on", "abrir": "on", "abra": "on"
        }
        
        # Dispositivos conhecidos
        self.devices = [
            "luz", "luzes", "lampada", "lâmpada",
            "sala", "quarto", "cozinha", "banheiro", "garagem",
            "ventilador", "ar condicionado", "ar-condicionado",
            "tv", "televisão", "televisao",
            "portão", "portao", "porta"
        ]
        
        # Comandos de sistema
        self.system_keywords = [
            "status", "limpar memória", "limpar memoria", 
            "reiniciar", "desligar sistema", "quais dispositivos"
        ]

    def parse(self, text: str) -> Intent:
        text_lower = text.lower().strip()
        
        # 1. Verifica comandos de sistema
        for keyword in self.system_keywords:
            if keyword in text_lower:
                return Intent(type="system", raw_text=text)
        
        # 2. Verifica comandos IoT
        action = None
        for keyword, act in self.iot_keywords.items():
            if keyword in text_lower:
                action = act
                break
        
        if action:
            # Tenta encontrar o dispositivo mencionado
            device_id = None
            for device in self.devices:
                if device in text_lower:
                    device_id = device
                    break
            
            if device_id:
                print(f"[INTENT] IoT detectado: {action} -> {device_id}")
                return Intent(
                    type="iot_command",
                    device_id=device_id,
                    action=action,
                    raw_text=text
                )
        
        # 3. Default: conversa normal (vai para a IA)
        return Intent(type="conversation", raw_text=text)
