"""
Processo 1: API Server (Dashboard + REST + WebSocket)
=====================================================
Roda APENAS o FastAPI/Uvicorn. Nao inicializa hardware (mic, tts, camera).
Comandos do Dashboard sao enfileirados no SQLite para o Voice Worker processar.

Uso: python -m src.api_server
"""
import os
import time
import threading
import uvicorn
from dotenv import load_dotenv


def poll_results():
    """Thread que verifica resultados concluidos e envia via WebSocket."""
    from src.infrastructure.task_queue import TaskQueue
    from src.api import server
    import asyncio

    queue = TaskQueue()
    last_id = 0

    while True:
        try:
            results = queue.get_completed(since_id=last_id)
            for r in results:
                last_id = r["id"]
                # Envia resultado para todos os clientes WebSocket
                if server.active_connections:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(
                        server.broadcast_event(
                            "chat",
                            data={"role": "assistant", "content": r["result"]},
                        )
                    )
                    loop.run_until_complete(
                        server.broadcast_event(
                            "log", message=f"Resposta: {r['result'][:80]}..."
                        )
                    )
                    loop.close()

            # Limpa tarefas antigas a cada ciclo
            queue.cleanup_old()
        except Exception as e:
            print(f"[API] Erro no poll: {e}")

        time.sleep(1)  # Verifica a cada 1 segundo


def main():
    load_dotenv()

    print("=" * 50)
    print("  J.A.R.V.I.S. — API Server (Processo 1)")
    print("=" * 50)
    print("[API] Modo: Somente Dashboard (sem hardware)")
    print("[API] Dashboard: http://localhost:8000/dashboard")
    print("[API] Health:    http://localhost:8000/health")
    print("=" * 50)

    # Inicia thread de polling de resultados
    poll_thread = threading.Thread(target=poll_results, daemon=True)
    poll_thread.start()

    # Inicia o servidor FastAPI
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
