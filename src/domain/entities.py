from dataclasses import dataclass
from typing import Optional

@dataclass
class UserCommand:
    text: str
    is_wake_word_detected: bool

@dataclass
class AIResponse:
    text: str
    action: Optional[str] = None
