from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class UserCommand:
    text: str
    is_wake_word_detected: bool

@dataclass
class AIResponse:
    text: str
    action: Optional[str] = None

@dataclass
class Intent:
    type: str  # "iot_command", "conversation", "system"
    device_id: Optional[str] = None
    action: Optional[str] = None
    raw_text: str = ""

@dataclass
class IoTDevice:
    id: str
    name: str
    ip: str
    status: str = "unknown"
    last_seen: Optional[datetime] = None

@dataclass
class RecognizedUser:
    name: str
    confidence: float
    timestamp: datetime
