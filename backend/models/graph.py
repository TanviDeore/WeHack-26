from pydantic import BaseModel
from typing import Optional

class DataCenterModel(BaseModel):
    id: str
    name: str
    location: str
    latitude: float
    longitude: float
    capacity_mw: float
    operational_since: str

class LocationModel(BaseModel):
    id: str
    climate: str
    avg_temp: float
    humidity: float
    energy_cost_index: float

class CoolingSystemModel(BaseModel):
    id: str
    type: str
    efficiency_score: float

class IncidentModel(BaseModel):
    id: str
    type: str
    severity: str
    timestamp: str
    duration_minutes: int
    root_cause: str

class MaintenanceEventModel(BaseModel):
    id: str
    type: str
    cost_level: str
    effect: str

class PerformanceSnapshotModel(BaseModel):
    id: str
    pue: float
    latency_ms: int
    uptime: float
