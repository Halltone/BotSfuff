from dataclasses import dataclass
from typing import Optional

@dataclass
class Track:
    title: str
    url: str
    original_url: str
    duration: Optional[int] = None
    requester_id: Optional[int] = None