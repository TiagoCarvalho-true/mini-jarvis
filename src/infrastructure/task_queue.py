"""
Fila de tarefas baseada em SQLite — substitui Redis/Celery.
Permite que o API Server envie comandos para o Voice Worker
sem dependencias externas.
"""
import time
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class TaskModel(Base):
    __tablename__ = "task_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    command = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending | processing | done
    result = Column(Text, nullable=True)
    created_at = Column(Float, default=lambda: time.time())
    completed_at = Column(Float, nullable=True)


class TaskQueue:
    """Fila thread-safe via SQLite WAL mode."""

    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        # WAL mode permite leitura e escrita simultanea de processos diferentes
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.commit()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    # --- API Server usa estes metodos ---

    def enqueue(self, command: str) -> int:
        """Insere um comando na fila. Retorna o ID da tarefa."""
        session = self.Session()
        try:
            task = TaskModel(command=command, status="pending")
            session.add(task)
            session.commit()
            task_id = task.id
            print(f"[QUEUE] Tarefa #{task_id} enfileirada: '{command[:50]}...'")
            return task_id
        finally:
            session.close()

    def get_completed(self, since_id: int = 0):
        """Retorna tarefas concluidas com ID maior que since_id."""
        session = self.Session()
        try:
            tasks = (
                session.query(TaskModel)
                .filter(TaskModel.status == "done", TaskModel.id > since_id)
                .order_by(TaskModel.id.asc())
                .all()
            )
            return [
                {"id": t.id, "command": t.command, "result": t.result}
                for t in tasks
            ]
        finally:
            session.close()

    # --- Voice Worker usa estes metodos ---

    def dequeue(self):
        """Pega a proxima tarefa pendente (FIFO). Retorna None se vazia."""
        session = self.Session()
        try:
            task = (
                session.query(TaskModel)
                .filter(TaskModel.status == "pending")
                .order_by(TaskModel.id.asc())
                .first()
            )
            if task:
                task.status = "processing"
                session.commit()
                return {"id": task.id, "command": task.command}
            return None
        finally:
            session.close()

    def complete(self, task_id: int, result: str):
        """Marca uma tarefa como concluida com o resultado."""
        session = self.Session()
        try:
            task = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                task.status = "done"
                task.result = result
                task.completed_at = time.time()
                session.commit()
                print(f"[QUEUE] Tarefa #{task_id} concluida.")
        finally:
            session.close()

    def cleanup_old(self, max_age_seconds: int = 3600):
        """Remove tarefas concluidas com mais de 1 hora."""
        session = self.Session()
        try:
            cutoff = time.time() - max_age_seconds
            session.query(TaskModel).filter(
                TaskModel.status == "done",
                TaskModel.completed_at < cutoff,
            ).delete()
            session.commit()
        finally:
            session.close()
