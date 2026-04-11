from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.agents.operations.graph import operations_graph
from backend.database.neo4j_client import neo4j_client
from datetime import datetime

router = APIRouter()

class FeedbackPayload(BaseModel):
    dc_id: str
    anomalies: list[str]
    action_taken: str

@router.get("/agent/operations/{dc_id}")
async def run_operations_agent(dc_id: str):
    """Trigger the real-time operations agent."""
    try:
        final_state = operations_graph.invoke({"dc_id": dc_id})
        return {
            "dc_id": final_state.get("dc_id", dc_id),
            "metrics_analyzed": final_state.get("metrics", {}),
            "anomalies": final_state.get("detected_anomalies", []),
            "recommended_action": final_state.get("recommended_action", "None"),
            "status": final_state.get("status", "Unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/operations/feedback")
async def record_feedback(payload: FeedbackPayload):
    """Record operator action into Neo4j graph connecting to DataCenter."""
    try:
        timestamp = datetime.now().isoformat()
        query = """
        MERGE (dc:DataCenter {id: $dc_id})
        CREATE (a:Action {
            type: $action, 
            timestamp: $ts, 
            anomalies_resolved: $anomalies
        })
        MERGE (dc)-[:TOOK_ACTION]->(a)
        RETURN a
        """
        neo4j_client.run_query(query, {
            "dc_id": payload.dc_id,
            "action": payload.action_taken,
            "ts": timestamp,
            "anomalies": ",".join(payload.anomalies) if payload.anomalies else "None"
        })
        return {"message": "Action successfully safely recorded in historical Graph Database (Neo4j)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
