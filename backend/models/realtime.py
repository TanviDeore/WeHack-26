from pydantic import BaseModel
from typing import List, Optional

class RealtimeStateModel(BaseModel):
    dc_id: str
    status: str
    temperature: float
    cpu_load: float
    power_usage: float
    latency: float

class AlertModel(BaseModel):
    dc_id: str
    message: str
    severity: str
    timestamp: str

class AgentTriggerModel(BaseModel):
    agent_type: str
    status: str
    trigger: str
