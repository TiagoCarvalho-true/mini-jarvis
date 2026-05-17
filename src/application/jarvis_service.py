import threading
from datetime import datetime
from typing import Optional
from src.ports.inbound.audio_listener_port import AudioListenerPort
from src.ports.inbound.vision_port import VisionPort
from src.ports.outbound.llm_port import LLMPort
from src.ports.outbound.tts_port import TTSPort
from src.ports.outbound.memory_port import MemoryPort
from src.ports.outbound.iot_controller_port import IoTControllerPort
from src.domain.intent_parser import IntentParser

class JarvisService:
    def __init__(
        self, 
        audio_listener: AudioListenerPort, 
        llm: LLMPort, 
        tts: TTSPort, 
        memory: MemoryPort,
        vision: Optional[VisionPort] = None,
        iot: Optional[IoTControllerPort] = None
    ):
        self.audio_listener = audio_listener
        self.llm = llm
        self.tts = tts
        self.memory = memory
        self.vision = vision
        self.iot = iot
        self.intent_parser = IntentParser(llm)
        self.start_time = datetime.now()
        self._lock = threading.Lock() # Semáforo para evitar concorrência na API

    def process_command(self, text: str) -> str:
        """Processa um comando garantindo execução única via Semáforo."""
        with self._lock:
            # 1. Classifica a intencao (Local)
            intent = self.intent_parser.parse(text)
            print(f"[JARVIS] Intencao detectada: {intent.type}")

            # 2. Executa acao se for IoT
            if intent.type == "iot_command" and self.iot:
                result = self.iot.send_command(intent.device_id, intent.action)
                if result.get("status") == "success":
                    response = f"Com certeza, senhor. Acionei o dispositivo {intent.device_id}."
                else:
                    response = f"Desculpe, senhor. Tive um problema ao acessar o dispositivo {intent.device_id}."
                
                self.memory.save_message("user", text)
                self.memory.save_message("assistant", response)
                return response

            # 3. Fluxo de conversa normal (Chamada API)
            history = self.memory.get_history(limit=15)
            current_history = history + [{"role": "user", "content": text}]
            response = self.llm.generate_response(text, history=current_history)
            
            self.memory.save_message("user", text)
            self.memory.save_message("assistant", response)
            
            return response

    def get_system_status(self):
        uptime = datetime.now() - self.start_time
        return {
            "uptime": str(uptime).split(".")[0],
            "messages_count": len(self.memory.get_history(limit=1000)),
            "devices_online": len(self.iot.list_devices()) if self.iot else 0,
            "last_user": self.vision.get_detected_user() if self.vision else "Ninguem"
        }

    def run(self):
        self.tts.speak("Sistemas online. Dashboard ativo. Aguardando comandos.")
        
        while True:
            # 1. Aguarda a wake word (Voz ou Palmas)
            if self.audio_listener.listen_for_wake_word():
                
                # 2. Verifica quem esta falando (Visao)
                user = None
                if self.vision:
                    try:
                        user = self.vision.check_once()
                    except Exception as e:
                        print(f"[VISION] Erro ao verificar: {e}")
                
                if user and user != "Desconhecido":
                    # Ajustado para evitar "Senhor Senhor"
                    self.tts.speak(f"Sim, {user}. Em que posso ajudar?")
                else:
                    self.tts.speak("Sim, senhor?")
                
                # 3. Ouve o comando (tenta ate 2 vezes)
                command_text = ""
                for attempt in range(2):
                    command_text = self.audio_listener.listen_for_command()
                    if command_text:
                        break
                    if attempt == 0:
                        print("[JARVIS] Nao entendi, tentando novamente...")
                
                if command_text:
                    print(f"[JARVIS] Comando recebido: {command_text}")
                    response = self.process_command(command_text)
                    print(f"[JARVIS] Resposta: {response[:80]}...")
                    self.tts.speak(response)
                else:
                    print("[JARVIS] Nenhum comando detectado.")
                    self.tts.speak("Desculpe, nao consegui ouvir. Tente novamente.")
