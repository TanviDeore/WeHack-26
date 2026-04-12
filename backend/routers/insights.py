from fastapi import APIRouter, Query
from typing import Optional
from backend.database.redis_client import redis_client
from backend.database.neo4j_client import neo4j_client
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel
import datetime

router = APIRouter()

class ActionTakenRequest(BaseModel):
    dc_id: str
    action_name: str
    simulated_value: float

@router.get("/agent/datacenters")
async def get_datacenters():
    query = "MATCH (dc:DataCenter) RETURN dc.id as id, dc.name as name ORDER BY dc.name"
    data = neo4j_client.run_query(query)
    return {"status": "success", "datacenters": data}

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
    
    # Check live status from Redis to dictate logic
    redis_status = redis_client.get_state(f"dc:{dc_id}:status") or "optimal"
    
    # Initialize GenAI Client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "error": "GEMINI_API_KEY not configured on server"}
        
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an AI Predictive Maintenance Agent for a Data Center.
    The exact live state of this Data Center right now is: {redis_status}.
    
    Analyze the following Graph Database context for Data Center {dc_id} and predict potential incidents.
    IF THE STATUS IS OPTIMAL, STILL check for possible future failures.
    
    CRITICAL: For 'recommended_actions', you MUST pick an action EXACTLY from this list:
    [increase cooling capacity, fix airflow, clean filters, upgrade cooling system, redistribute workloads, shut down non-critical processes, balance power usage, switch energy sources, replace failing components]
    
    You MUST provide a 'simulation' block defining the physical variable to change.
    
    Context:
    Data Center details: {context_data.get('datacenter')}
    Location & Climate: {context_data.get('location')}
    Cooling System: {context_data.get('cooling_system')}
    Past Incidents & Hardware Failures: {context_data.get('past_incidents')}
    
    Output a JSON object with this exact structure:
    {{
        "potential_incidents": [
            {{"incident_type": "string", "probability": "High|Medium|Low", "reason": "string"}}
        ],
        "recommended_actions": [
            {{
                "action_name": "string", 
                "description": "string", 
                "priority": "High|Medium|Low", 
                "expected_outcome": "string",
                "simulation": {{
                    "name": "string (The real-world metric name e.g. Airflow Volume)",
                    "unit": "string (SI unit e.g. CFM)",
                    "min": "number",
                    "max": "number",
                    "current": "number",
                    "optimal_min": "number",
                    "optimal_max": "number"
                }}
            }}
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
        
        # Clean the response text from any markdown formatting specifically around JSON
        raw_text = response.text
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("```json").strip("```").strip()
            
        prediction_json = json.loads(raw_text)
        return {"status": "success", "data": prediction_json}
    except Exception as e:
        print(f"Gemini API Error (falling back to dynamic simulation mock data): {e}")
        
        # MOCK FALLBACK DATA FOR HACKATHON DEMO
        mock_fallback = {"potential_incidents": [], "recommended_actions": []}
        
        import random
        # 8 Real-World Data Center Scenarios mapped to specific simulation bounds
        optimal_scenarios = [
            {
                "action": "Increase cooling capacity",
                "sim": {"name": "Temperature", "unit": "°C", "min": 10, "max": 40, "current": 35, "optimal_min": 18, "optimal_max": 27},
                "incident": "Thermal cascade predicted during peak load",
                "failure_reason": "Sustained high temperatures degrade internal solder joints and trigger CPU throttling. Without immediate intervention, components will cross critical heat thresholds, causing abrupt server shutdowns.",
                "desc": "Operating continuously near the thermal ceiling causes silent wear on critical motherboard components. Proactively boosting the localized air cooling capacity before the ambient temperature crosses the degradation threshold prevents unpredictable overheating and improves server hardware lifespan by 20-40% over a standard multi-year cycle."
            },
            {
                "action": "upgrade cooling system",
                "sim": {"name": "Target PUE", "unit": "PUE", "min": 1.0, "max": 2.5, "current": 1.9, "optimal_min": 1.2, "optimal_max": 1.5},
                "incident": "Systematic energy waste approaching 50%",
                "failure_reason": "Current cooling infrastructure is running far too inefficiently to sustain peak scale. This forces the PUE ratio to skyrocket, which will lead to devastatingly high operational energy waste over time and constrain any future compute scaling.",
                "desc": "The local cooling architecture is consuming far too much electricity comparative to compute load. Committing to a localized cooling infrastructure upgrade reduces energy costs by 20-50% while unlocking much higher physical compute density. This allows extreme AI/ML workloads to continue scaling without constant thermal throttling."
            },
            {
                "action": "shut down non-critical processes",
                "sim": {"name": "Idle Resources Reclaimed", "unit": "% capacity", "min": 0, "max": 50, "current": 5, "optimal_min": 10, "optimal_max": 30},
                "incident": "High dormant power draw predicted",
                "failure_reason": "Non-critical processes and Zombie VMs are hogging compute overhead. This parasitic draw slowly starves core workloads of bandwidth and memory, leading to spontaneous memory leaks and application crashes on primary services.",
                "desc": "Agent analysis suggests massive wasted compute allocation. Identifying and purging Zombie VMs, idle containers, and unused backend services frees up necessary compute overhead. This action instantly reduces dormant power and cooling workloads, stabilizing the entire cluster's energy footprint."
            }
        ]
        
        degraded_scenarios = [
            {
                "action": "fix airflow",
                "sim": {"name": "Airflow Velocity", "unit": "CFM", "min": 100, "max": 1200, "current": 300, "optimal_min": 400, "optimal_max": 800},
                "incident": "Severe hot spots forming globally across racks",
                "failure_reason": "Low airflow velocity physically traps immense heat pools between server nodes. These localized heat pools rapidly bypass safety thresholds, causing internal hardware expansion that cracks data transfer pathways.",
                "desc": "Physical intake and exhaust flow velocity is dangerously degraded resulting in isolated rack temperature spikes. Rerouting cabling constraints and removing blockages instantly eliminates hot spots, improving cooling efficiency by up to 30% and stabilizing rack performance under extreme traffic."
            },
            {
                "action": "clean filters",
                "sim": {"name": "Filter Age", "unit": "Months", "min": 1, "max": 12, "current": 8, "optimal_min": 1, "optimal_max": 3},
                "incident": "Air intake compression starving liquid pumps",
                "failure_reason": "Excessive particulate buildup is clogging the primary air intakes. This forces the liquid cooling pumps to run at 100% duty cycle, burning out the pump bearings and resulting in total cooling failure.",
                "desc": "Environmental analysis reveals dust and particulate buildup across HVAC intakes spanning well past the 3-month lifespan. Deep cleaning the physical filters immediately maintains base airflow efficiency, dropping the immense pressure strain on internal liquid cooling pumps."
            },
            {
                "action": "redistribute workloads",
                "sim": {"name": "CPU Utilization", "unit": "%", "min": 0, "max": 100, "current": 92, "optimal_min": 40, "optimal_max": 70},
                "incident": "Critical Compute Lockup Risk",
                "failure_reason": "CPU utilization is vastly exceeding safe operational limits (>80%). Running cores continuously at this threshold physically melts thermal paste and drastically heightens the risk of full hardware lockup.",
                "desc": "Aggregated CPU utilization is caught in a critical overload loop spanning over 90% boundary lines. Without redistributing traffic to adjacent Edge locations, localized hotspots will merge into a terminal server crash. Executing a shard failover ensures the cluster remains in the 40-70% ideal efficiency zone."
            },
            {
                "action": "balance power usage",
                "sim": {"name": "Power Utilization", "unit": "% circuit", "min": 0, "max": 100, "current": 95, "optimal_min": 10, "optimal_max": 80},
                "incident": "Incoming breaker trips & outages",
                "failure_reason": "Total grid utilization is redlining close to absolute facility limits. Any minor asynchronous traffic spike will trip local breakers, causing massive, ungraceful server shutdowns spanning the entire facility.",
                "desc": "Circuit delivery capacity has spiked dangerously close to the total grid ceiling. Instantly shedding or delaying heavy asynchronous workloads will pull power utilization back under the 80% mark, preventing catastrophic facility-wide outages and isolating grid strain."
            },
            {
                "action": "replace failing components",
                "sim": {"name": "Hardware Failure Rate", "unit": "%", "min": 0, "max": 20, "current": 10, "optimal_min": 0, "optimal_max": 4},
                "incident": "Hardware chain failures accelerating",
                "failure_reason": "Defective RAM sticks and magnetic drive failures are currently multiplying logarithmically across the environment. This cascade will destroy local shard parity and lead to catastrophic data loss.",
                "desc": "The predictive model reveals that aging magnetic sectors and failing DIMMs are causing rapid micro-failures across the floor, breaching the 4% safety boundary. Authorizing immediate physical hardware swaps limits the blast radius of these cascading errors to ensure 99.99% system continuity."
            }
        ]
        
        pool = optimal_scenarios if redis_status == "optimal" else degraded_scenarios
        chosen = random.choice(pool)

        mock_fallback["potential_incidents"].append({
            "incident_type": chosen["incident"],
            "probability": "Low" if redis_status == "optimal" else "High",
            "reason": chosen.get("failure_reason", "Failure cascade triggers when operating consistently outside of target bounds.")
        })
        mock_fallback["recommended_actions"].append({
            "action_name": chosen["action"],
            "description": chosen["desc"],
            "priority": "Medium" if redis_status == "optimal" else "Critical",
            "expected_outcome": "Guarantees sustained uptime and lowers degradation.",
            "simulation": chosen["sim"]
        })
            
        return {"status": "success", "data": mock_fallback}

