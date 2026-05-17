import os
import threading
import uvicorn
from dotenv import load_dotenv

from src.adapters.inbound.microphone_adapter import MicrophoneAdapter
from src.adapters.inbound.webcam_adapter import WebcamAdapter
from src.adapters.outbound.openrouter_adapter import OpenRouterAdapter
from src.adapters.outbound.tts_adapter import TTSAdapter
from src.adapters.outbound.esp32_adapter import ESP32Adapter
from src.infrastructure.database import SQLiteMemoryAdapter
from src.application.jarvis_service import JarvisService
from src.api import server

def run_api():
    """Inicia o servidor FastAPI."""
    uvicorn.run(server.app, host="0.0.0.0", port=8000, log_level="info")

def main():
    # 1. Carregar configuracoes
    load_dotenv()
    
    wake_word = os.getenv("WAKE_WORD", "computador")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    
    # Configuracoes de Visao
    face_rec_enabled = os.getenv("FACE_RECOGNITION_ENABLED", "true").lower() == "true"
    camera_source = os.getenv("CAMERA_SOURCE", "0")
    vision_mode = os.getenv("VISION_MODE", "on_demand")

    # 2. Injetar dependencias (DI)
    microphone = MicrophoneAdapter(wake_word=wake_word)
    llm = OpenRouterAdapter(api_key=openrouter_api_key, model=openrouter_model)
    tts = TTSAdapter()
    memory = SQLiteMemoryAdapter()
    
    # Vision Adapter
    vision = None
    if face_rec_enabled:
        vision = WebcamAdapter(source=camera_source, mode=vision_mode)
    
    # IoT Adapter
    iot = ESP32Adapter()

    # 3. Inicializar Servico
    jarvis = JarvisService(
        audio_listener=microphone, 
        llm=llm, 
        tts=tts, 
        memory=memory,
        vision=vision,
        iot=iot
    )
    
    # Compartilhar instancia com a API
    server.jarvis_service = jarvis

    # 4. Iniciar API em uma thread separada
    print("[SYSTEM] Iniciando Dashboard API na porta 8000...")
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # 5. Iniciar Loop de Voz (Main Thread)
    try:
        jarvis.run()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Desligando sistemas...")
        if vision:
            try:
                vision.stop()
            except:
                pass
        try:
            tts.speak("Sistemas encerrados. Ate logo, senhor.")
        except:
            pass
        print("[SYSTEM] Encerrado com sucesso.")

if __name__ == "__main__":
    main()
