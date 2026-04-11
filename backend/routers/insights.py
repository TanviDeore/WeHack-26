from fastapi import APIRouter
from backend.database.redis_client import redis_client
from backend.database.neo4j_client import neo4j_client

router = APIRouter()

@router.get("/agent/context/{dc_id}")
async def get_agent_context(dc_id: str):
    # This endpoint mimics the context gathering phase of an AI agent
    
    # 1. Gather Short-Term Memory (Redis)
    current_state = redis_client.get_state(f"dc:{dc_id}:status")
    active_alert = redis_client.get_state(f"alert:{dc_id}")
    recent_events = redis_client.get_recent_events(f"recent:event:{dc_id}")

    # 2. Historical Context (Removed from Timeseries)
    avg_temp_1h = None

    # 3. Gather Long-Term Causality (Neo4j)
    # Find past incidents and cooling systems for this DC
    neo4j_query = """
    MATCH (dc:DataCenter {id: $dc_id})-[:USES_COOLING]->(cs:CoolingSystem)
    OPTIONAL MATCH (dc)-[:EXPERIENCED]->(inc:Incident)
    RETURN cs.type AS cooling_system, collect(inc.type) AS past_incidents
    """
    long_term_data = neo4j_client.run_query(neo4j_query, {"dc_id": dc_id})

    # Combine into a "Prompt Context" suitable for an LLM
    context = {
        "dc_id": dc_id,
        "realtime": {
            "current_state": current_state,
            "active_alert": active_alert,
            "recent_events": recent_events
        },
        "historical": {
            "avg_temp_last_hour": "N/A (Timeseries Removed)"
        },
        "long_term": {
            "cooling_system": long_term_data[0]["cooling_system"] if long_term_data else "Unknown",
            "historical_incidents": long_term_data[0]["past_incidents"] if long_term_data else []
        }
    }
    
    return {"context": context}
