from src.ports.inbound.audio_listener_port import AudioListenerPort
from src.ports.outbound.llm_port import LLMPort
from src.ports.outbound.tts_port import TTSPort
from src.ports.outbound.memory_port import MemoryPort

class JarvisService:
    def __init__(self, audio_listener: AudioListenerPort, llm: LLMPort, tts: TTSPort, memory: MemoryPort):
        self.audio_listener = audio_listener
        self.llm = llm
        self.tts = tts
        self.memory = memory

    def process_command(self, text: str) -> str:
        """Processa um comando de texto, salva na memória e retorna a resposta."""
        # 1. Recupera histórico para contexto
        history = self.memory.get_history(limit=15)
        
        # 2. Adiciona mensagem atual ao histórico para o LLM (temporário)
        current_history = history + [{"role": "user", "content": text}]
        
        # 3. Gera resposta
        response = self.llm.generate_response(text, history=current_history)
        
        # 4. Salva no banco de dados permanentemente
        self.memory.save_message("user", text)
        self.memory.save_message("assistant", response)
        
        return response

    def run(self):
        self.tts.speak("Sistemas online. Servidor de memória carregado. Aguardando comandos.")
        while True:
            # 1. Aguarda a wake word
            if self.audio_listener.listen_for_wake_word():
                self.tts.speak("Sim, senhor?")
                
                # 2. Ouve o comando
                command_text = self.audio_listener.listen_for_command()
                
                if command_text:
                    print(f"Usuario: {command_text}")
                    response = self.process_command(command_text)
                    self.tts.speak(response)
