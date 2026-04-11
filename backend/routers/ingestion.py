from fastapi import APIRouter, HTTPException
from backend.models.timeseries import TelemetryDataPoint
from backend.database.redis_client import redis_client
from backend.database.neo4j_client import neo4j_client

router = APIRouter()

@router.post("/telemetry")
async def ingest_telemetry(data: TelemetryDataPoint):
    try:
        # 1. Update Short-Term Memory (Redis)
        live_state = {
            "dc_id": data.dc_id,
            "status": "normal" if data.temperature < 85 else "degraded",
            "temperature": data.temperature,
            "cpu_load": data.cpu_usage,
            "power_usage": data.pue,
            "latency": data.latency_ms
        }
        redis_client.set_state(f"dc:{data.dc_id}:status", live_state)

        # Append to recent events if there's a big spike
        if data.temperature > 90:
            redis_client.push_event(f"recent:event:{data.dc_id}", "temp_spike_detected")
            # Create active alert
            redis_client.set_state(f"alert:{data.dc_id}", {"alert": "cooling_stress_detected", "severity": "high"})

        # 2. Update Historical Memory (InfluxDB) - REMOVED
        

        # 3. IF event is severe, log it into Long-Term Memory (Neo4j)
        if data.event_type and "failure" in data.event_type:
            incident_id = f"inc_{data.dc_id}_{int(data.temperature)}"
            query = """
            MATCH (dc:DataCenter {id: $dc_id})
            MERGE (inc:Incident {id: $incident_id})
            SET inc.type = $event_type, inc.severity = 'high'
            MERGE (dc)-[:EXPERIENCED]->(inc)
            """
            neo4j_client.run_query(query, {"dc_id": data.dc_id, "incident_id": incident_id, "event_type": data.event_type})

        return {"message": "Data successfully ingested into all memory layers."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
