from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
from jinja2 import Environment, FileSystemLoader
import json
import os

app = FastAPI(title="J.A.R.V.I.S. Core Server")

# Configura arquivos estaticos e templates
app.mount("/static", StaticFiles(directory="src/api/static"), name="static")
jinja_env = Environment(loader=FileSystemLoader("src/api/templates"), autoescape=True)

# Conexoes WebSocket ativas
active_connections: List[WebSocket] = []


class CommandRequest(BaseModel):
    text: str


# --- WebSocket Manager ---
async def broadcast_event(event_type: str, message: str = None, data: dict = None):
    payload = {"type": event_type}
    if message:
        payload["message"] = message
    if data:
        payload.update(data)

    dead_connections = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(payload))
        except:
            dead_connections.append(connection)

    for dead in dead_connections:
        if dead in active_connections:
            active_connections.remove(dead)


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantem conexao viva
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


# --- Endpoints Dashboard ---
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    template = jinja_env.get_template("dashboard.html")
    return HTMLResponse(content=template.render())


@app.get("/health")
def health_check():
    """Status dos componentes — o API Server so sabe do que ele pode verificar."""
    from src.infrastructure.task_queue import TaskQueue

    queue = TaskQueue()
    pending = len(queue.get_completed(since_id=0))
    return {
        "api": "ok",
        "queue_tasks_done": pending,
        "worker": "verifique o Terminal 2",
    }


@app.get("/")
def read_root():
    return {"status": "online", "message": "J.A.R.V.I.S. Core Server is running."}


@app.get("/history")
def get_history(limit: int = 15):
    """Consulta historico diretamente no SQLite (sem precisar do worker)."""
    from src.infrastructure.database import SQLiteMemoryAdapter

    memory = SQLiteMemoryAdapter()
    return memory.get_history(limit=limit)


@app.get("/api/status")
def get_status():
    return {
        "mode": "distributed",
        "api": "online",
        "worker": "verifique Terminal 2",
    }


# --- Endpoints IoT (proxy — envia para a fila) ---
@app.get("/api/devices")
def list_devices():
    """No modo distribuido, retorna lista estatica do .env."""
    nodes_json = os.getenv("ESP32_NODES", "[]")
    try:
        return json.loads(nodes_json)
    except:
        return []


@app.post("/api/devices/{device_id}/command")
async def device_command(device_id: str, action: str):
    """Enfileira comando IoT para o worker processar."""
    from src.infrastructure.task_queue import TaskQueue

    queue = TaskQueue()
    command_text = f"ligar {device_id}" if action == "on" else f"desligar {device_id}"
    task_id = queue.enqueue(command_text)
    await broadcast_event("log", f"Comando IoT enfileirado: {action} -> {device_id}")
    return {"status": "enfileirado", "task_id": task_id}


# --- Endpoints Face Recognition ---
@app.get("/api/faces")
def list_faces():
    faces_dir = "known_faces"
    if not os.path.exists(faces_dir):
        return []
    return [f.replace(".jpg", "") for f in os.listdir(faces_dir) if f.endswith(".jpg")]


@app.post("/api/faces/register")
async def register_face(name: str = Form(...), file: UploadFile = File(...)):
    os.makedirs("known_faces", exist_ok=True)
    contents = await file.read()
    path = f"known_faces/{name}.jpg"
    with open(path, "wb") as f:
        f.write(contents)
    await broadcast_event("log", f"Novo rosto cadastrado: {name}")
    return {"status": "success"}


@app.delete("/api/faces/{name}")
async def delete_face(name: str):
    path = f"known_faces/{name}.jpg"
    if os.path.exists(path):
        os.remove(path)
        await broadcast_event("log", f"Rosto removido: {name}")
        return {"status": "success"}
    return {"status": "error", "message": "Rosto nao encontrado"}


# --- Endpoint Principal: /ask (Enfileira no SQLite) ---
@app.post("/ask")
async def ask_jarvis(request: CommandRequest):
    """Recebe comando do Dashboard e enfileira para o Voice Worker processar."""
    from src.infrastructure.task_queue import TaskQueue

    queue = TaskQueue()
    task_id = queue.enqueue(request.text)

    await broadcast_event("log", f"Pergunta enfileirada (#{task_id}): {request.text}")
    await broadcast_event("chat", data={"role": "user", "content": request.text})

    return {
        "status": "enfileirado",
        "task_id": task_id,
        "message": "O Voice Worker vai processar sua pergunta.",
    }
