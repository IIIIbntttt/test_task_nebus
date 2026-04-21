from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OutboxEvent:
    id: int
    event_type: str
    payload: dict[str, object]
    created_at: datetime
