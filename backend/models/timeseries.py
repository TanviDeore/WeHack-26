from pydantic import BaseModel
from typing import Optional

class TelemetryDataPoint(BaseModel):
    dc_id: str
    temperature: float
    cpu_usage: float
    pue: float
    latency_ms: float
    event_type: Optional[str] = None
