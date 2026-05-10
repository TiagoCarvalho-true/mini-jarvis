import os
import threading
import uvicorn
from dotenv import load_dotenv

from src.adapters.inbound.microphone_adapter import MicrophoneAdapter
from src.adapters.outbound.openrouter_adapter import OpenRouterAdapter
from src.adapters.outbound.tts_adapter import TTSAdapter
from src.infrastructure.database import SQLiteMemoryAdapter
from src.application.jarvis_service import JarvisService
from src.api import server

def run_api():
    """Inicia o servidor FastAPI."""
    uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="info")

def main():
    # 1. Carregar configuracoes
    load_dotenv()
    
    wake_word = os.getenv("WAKE_WORD", "jarvis")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")

    # 2. Injetar dependencias (DI)
    # Recomendacao para RPi 3: Usar o modelo 'tiny' no MicrophoneAdapter se o 'base' ficar lento
    microphone = MicrophoneAdapter(wake_word=wake_word)
    llm = OpenRouterAdapter(api_key=openrouter_api_key, model=openrouter_model)
    tts = TTSAdapter()
    memory = SQLiteMemoryAdapter()

    # 3. Inicializar Servico
    jarvis = JarvisService(
        audio_listener=microphone, 
        llm=llm, 
        tts=tts, 
        memory=memory
    )
    
    # Compartilhar instancia com a API
    server.jarvis_service = jarvis

    # 4. Iniciar API em uma thread separada
    print("Iniciando Servidor API na porta 8000...")
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # 5. Iniciar Loop de Voz (Main Thread)
    try:
        jarvis.run()
    except KeyboardInterrupt:
        print("\nDesligando sistemas...")
        tts.speak("Sistemas encerrados. Ate logo, senhor.")

if __name__ == "__main__":
    main()
