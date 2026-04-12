from fastapi import APIRouter
from backend.database.redis_client import redis_client
from backend.database.neo4j_client import neo4j_client
import os
import json
from google import genai
from google.genai import types

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

@router.get("/agent/predictive_maintenance/{dc_id}")
async def get_predictive_maintenance(dc_id: str):
    # Fetch data from Neo4j
    neo4j_query = """
    MATCH (dc:DataCenter {id: $dc_id})
    OPTIONAL MATCH (dc)-[:LOCATED_IN]->(loc:Location)
    OPTIONAL MATCH (dc)-[:USES_COOLING]->(cs:CoolingSystem)
    OPTIONAL MATCH (dc)-[:EXPERIENCED]->(inc:Incident)
    RETURN dc as datacenter, loc as location, cs as cooling_system, collect(inc) as past_incidents
    """
    db_data = neo4j_client.run_query(neo4j_query, {"dc_id": dc_id})
    if not db_data:
        return {"status": "error", "error": "Data center not found"}

    context_data = db_data[0]
    
    # Initialize GenAI Client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "error": "GEMINI_API_KEY not configured on server"}
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an AI Predictive Maintenance Agent for a Data Center.
    Analyze the following Graph Database context for Data Center {dc_id} and predict potential incidents and recommend actions to prevent them.
    
    Context:
    Data Center details: {context_data.get('datacenter')}
    Location: {context_data.get('location')}
    Cooling System: {context_data.get('cooling_system')}
    Past Incidents: {context_data.get('past_incidents')}
    
    Output a JSON object with this exact structure:
    {{
        "potential_incidents": [
            {{"incident_type": "string", "probability": "High|Medium|Low", "reason": "string"}}
        ],
        "recommended_actions": [
            {{"action_name": "string", "description": "string", "priority": "High|Medium|Low", "expected_outcome": "string"}}
        ]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        prediction_json = json.loads(response.text)
        return {"status": "success", "data": prediction_json}
    except Exception as e:
        return {"status": "error", "error": str(e)}
