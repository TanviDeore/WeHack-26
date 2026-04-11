from pydantic import BaseModel
from typing import List, Optional

class RealtimeStateModel(BaseModel):
    dc_id: str
    status: str
    temperature: float
    cpu_load: float
    power_usage: float
    latency: float
    cooling_system_rpm: Optional[float] = None
    network_packet_loss: Optional[float] = None
    active_memory_gb: Optional[float] = None

class AlertModel(BaseModel):
    dc_id: str
    message: str
    severity: str
    timestamp: str

class AgentTriggerModel(BaseModel):
    agent_type: str
    status: str
    trigger: str
