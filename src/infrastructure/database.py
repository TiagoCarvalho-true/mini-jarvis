from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.ports.outbound.memory_port import MemoryPort
from typing import List, Dict

Base = declarative_base()

class MessageModel(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    role = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SQLiteMemoryAdapter(MemoryPort):
    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_message(self, role: str, content: str) -> None:
        session = self.Session()
        new_msg = MessageModel(role=role, content=content)
        session.add(new_msg)
        session.commit()
        session.close()

    def get_history(self, limit: int = 20) -> List[Dict[str, str]]:
        session = self.Session()
        messages = session.query(MessageModel).order_by(MessageModel.id.desc()).limit(limit).all()
        session.close()
        
        # Inverter para ordem cronológica
        history = [{"role": m.role, "content": m.content} for m in reversed(messages)]
        return history

    def clear_history(self) -> None:
        session = self.Session()
        session.query(MessageModel).delete()
        session.commit()
        session.close()
