from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.agents.operations.graph import operations_graph
from backend.database.neo4j_client import neo4j_client
from backend.database.redis_client import redis_client
from datetime import datetime

router = APIRouter()

class FeedbackPayload(BaseModel):
    dc_id: str
    anomalies: list[str]
    action_taken: str
    root_cause: str | None = "unknown"
    severity: str | None = "medium"

@router.get("/agent/operations/{dc_id}")
async def run_operations_agent(dc_id: str):
    """Trigger the real-time operations agent."""
    try:
        final_state = operations_graph.invoke({"dc_id": dc_id})
        return {
            "dc_id": final_state.get("dc_id", dc_id),
            "metrics_analyzed": final_state.get("metrics", {}),
            "anomalies": final_state.get("detected_anomalies", []),
            "recommended_actions": final_state.get("recommended_actions", []),
            "status": final_state.get("status", "Unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/telemetry/{dc_id}")
async def get_raw_telemetry(dc_id: str):
    """Fetch lightweight live metrics purely from Redis without LLM."""
    try:
        keys_to_fetch = ["status", "temp", "cpu_load", "power_usage", "latency", "fan_speed_rpm", "network_bandwidth_gbps"]
        metrics = {}
        for k in keys_to_fetch:
            val = redis_client.get_raw(f"dc:{dc_id}:{k}")
            if val is not None:
                try:
                    metrics[k] = float(val) if '.' in val else int(val)
                except ValueError:
                    metrics[k] = val
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/operations/feedback")
async def record_feedback(payload: FeedbackPayload):
    """Record operator action into Neo4j graph connecting to DataCenter."""
    try:
        timestamp = datetime.now().isoformat()
        incident_id = f"inc_{dc_id}_{int(datetime.now().timestamp())}"
        
        query = """
        MERGE (dc:DataCenter {id: $dc_id})
        CREATE (inc:Incident {
            id: $inc_id,
            type: $incident_type,
            root_cause: $root_cause,
            severity: $severity,
            timestamp: $ts
        })
        CREATE (a:Action {
            type: $action, 
            timestamp: $ts, 
            anomalies_resolved: $anomalies
        })
        MERGE (dc)-[:EXPERIENCED]->(inc)
        MERGE (a)-[:RESOLVED_BY]->(inc)
        MERGE (dc)-[:TOOK_ACTION]->(a)
        RETURN a
        """
        neo4j_client.run_query(query, {
            "dc_id": payload.dc_id,
            "inc_id": incident_id,
            "incident_type": payload.anomalies[0] if payload.anomalies else "Telemetry Anomaly",
            "root_cause": payload.root_cause,
            "severity": payload.severity,
            "action": payload.action_taken,
            "ts": timestamp,
            "anomalies": ",".join(payload.anomalies) if payload.anomalies else "None"
        })
        return {"message": "Incident & Action successfully recorded in Graph Database."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
