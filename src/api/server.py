from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from src.application.jarvis_service import JarvisService

app = FastAPI(title="J.A.R.V.I.S. Core Server")

# Injetado pelo main.py
jarvis_service: JarvisService = None

class CommandRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"status": "online", "message": "J.A.R.V.I.S. Core Server is running."}

@app.get("/history")
def get_history(limit: int = 10):
    if not jarvis_service:
        return {"error": "Service not initialized"}
    return jarvis_service.memory.get_history(limit=limit)

@app.post("/ask")
def ask_jarvis(request: CommandRequest):
    if not jarvis_service:
        return {"error": "Service not initialized"}
    
    response = jarvis_service.process_command(request.text)
    return {"response": response}

@app.post("/speak")
def speak_text(request: CommandRequest, background_tasks: BackgroundTasks):
    if not jarvis_service:
        return {"error": "Service not initialized"}
    
    background_tasks.add_task(jarvis_service.tts.speak, request.text)
    return {"message": "Speaking..."}
