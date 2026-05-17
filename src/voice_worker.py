"""
Processo 2: Voice Worker (Hardware — Mic + TTS + Visao + IoT)
==============================================================
Dono exclusivo do hardware de audio. Processa comandos locais (voz)
e comandos da fila SQLite (vindos do Dashboard via API Server).

Uso: python -m src.voice_worker
"""
import os
import time
from dotenv import load_dotenv


def main():
    load_dotenv()

    print("=" * 50)
    print("  J.A.R.V.I.S. — Voice Worker (Processo 2)")
    print("=" * 50)

    # --- Importacoes pesadas (hardware) so aqui ---
    from src.adapters.inbound.microphone_adapter import MicrophoneAdapter
    from src.adapters.inbound.webcam_adapter import WebcamAdapter
    from src.adapters.outbound.openrouter_adapter import OpenRouterAdapter
    from src.adapters.outbound.tts_adapter import TTSAdapter
    from src.adapters.outbound.esp32_adapter import ESP32Adapter
    from src.infrastructure.database import SQLiteMemoryAdapter
    from src.infrastructure.task_queue import TaskQueue
    from src.application.jarvis_service import JarvisService

    # --- Configuracoes ---
    wake_word = os.getenv("WAKE_WORD", "jarvis")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    face_rec_enabled = os.getenv("FACE_RECOGNITION_ENABLED", "true").lower() == "true"
    camera_source = os.getenv("CAMERA_SOURCE", "0")
    vision_mode = os.getenv("VISION_MODE", "on_demand")

    # --- Inicializar adaptadores ---
    print("[WORKER] Inicializando adaptadores...")
    microphone = MicrophoneAdapter(wake_word=wake_word)
    llm = OpenRouterAdapter(api_key=openrouter_api_key, model=openrouter_model)
    tts = TTSAdapter()
    memory = SQLiteMemoryAdapter()
    queue = TaskQueue()

    vision = None
    if face_rec_enabled:
        try:
            vision = WebcamAdapter(source=camera_source, mode=vision_mode)
        except Exception as e:
            print(f"[WORKER] Visao desativada: {e}")

    iot = ESP32Adapter()

    # --- Inicializar Servico ---
    jarvis = JarvisService(
        audio_listener=microphone,
        llm=llm,
        tts=tts,
        memory=memory,
        vision=vision,
        iot=iot,
    )

    print("=" * 50)
    print("[WORKER] Todos os sistemas inicializados!")
    print("[WORKER] Aguardando wake word ou comandos da fila...")
    print("=" * 50)

    tts.speak("Sistemas online. Aguardando comandos.")

    # --- Loop Principal ---
    try:
        while True:
            # ====== PRIORIDADE 1: Fila do Dashboard ======
            task = queue.dequeue()
            if task:
                task_id = task["id"]
                command = task["command"]
                print(f"[WORKER] >>> Tarefa #{task_id} da fila: '{command}'")

                try:
                    response = jarvis.process_command(command)
                    print(f"[WORKER] Resposta: {response[:80]}...")
                    tts.speak(response)
                    queue.complete(task_id, response)
                except Exception as e:
                    error_msg = f"Erro ao processar: {e}"
                    print(f"[WORKER] {error_msg}")
                    queue.complete(task_id, error_msg)

                continue  # Volta para o inicio (verifica se tem mais tarefas)

            # ====== PRIORIDADE 2: Escuta por Voz ======
            if microphone.listen_for_wake_word():
                # Verifica quem esta falando
                user = None
                if vision:
                    try:
                        user = vision.check_once()
                    except Exception as e:
                        print(f"[VISION] Erro: {e}")

                if user and user != "Desconhecido":
                    tts.speak(f"Sim, {user}. Em que posso ajudar?")
                else:
                    tts.speak("Sim, senhor?")

                # Ouve o comando (tenta ate 2 vezes)
                command_text = ""
                for attempt in range(2):
                    command_text = microphone.listen_for_command()
                    if command_text:
                        break
                    if attempt == 0:
                        print("[WORKER] Nao entendi, tentando novamente...")

                if command_text:
                    print(f"[WORKER] Comando por voz: '{command_text}'")
                    response = jarvis.process_command(command_text)
                    print(f"[WORKER] Resposta: {response[:80]}...")
                    tts.speak(response)
                else:
                    print("[WORKER] Nenhum comando detectado.")
                    tts.speak("Desculpe, nao consegui ouvir. Tente novamente.")

    except KeyboardInterrupt:
        print("\n[WORKER] Desligando sistemas...")
        if vision:
            try:
                vision.stop()
            except:
                pass
        try:
            tts.speak("Sistemas encerrados. Ate logo, senhor.")
        except:
            pass
        print("[WORKER] Encerrado com sucesso.")


if __name__ == "__main__":
    main()
