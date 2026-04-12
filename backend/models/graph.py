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

# --- Mock Data Instantiation ---

MOCK_DATACENTER = DataCenterModel(
    id="dc_texas_01",
    name="Texas Data Center",
    location="Texas, USA",
    latitude=30.2672,
    longitude=-97.7431,
    capacity_mw=50.0,
    operational_since="2022"
)

MOCK_LOCATION = LocationModel(
    id="texas_hot_zone",
    climate="hot",
    avg_temp=38.0,
    humidity=60.0,
    energy_cost_index=0.8
)

MOCK_COOLING_SYSTEM = CoolingSystemModel(
    id="air_cooling_v1",
    type="air_cooling",
    efficiency_score=0.6
)

MOCK_INCIDENT_1 = IncidentModel(
    id="incident_001",
    type="overheating",
    severity="high",
    timestamp="2025-10-10",
    duration_minutes=45,
    root_cause="cooling_failure"
)

MOCK_INCIDENT_2 = IncidentModel(
    id="incident_002",
    type="power_surge",
    severity="medium",
    timestamp="2026-01-15",
    duration_minutes=15,
    root_cause="grid_instability"
)

MOCK_PERFORMANCE = PerformanceSnapshotModel(
    id="perf_001",
    pue=1.45,
    latency_ms=120,
    uptime=99.98
)

def get_mock_graph_data():
    return {
        "datacenter": MOCK_DATACENTER.model_dump(),
        "location": MOCK_LOCATION.model_dump(),
        "cooling_system": MOCK_COOLING_SYSTEM.model_dump(),
        "past_incidents": [MOCK_INCIDENT_1.model_dump(), MOCK_INCIDENT_2.model_dump()],
        "recent_performance": MOCK_PERFORMANCE.model_dump()
    }
