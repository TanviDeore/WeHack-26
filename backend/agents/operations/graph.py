import os
from langgraph.graph import StateGraph, END
from backend.agents.operations.state import OperationsState
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.database.redis_client import redis_client
from backend.database.neo4j_client import neo4j_client
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv(".env")

# Try importing from api_secrets if it exists, otherwise use env var
try:
    from backend.api_secrets import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY)

# ----------------- Models -----------------
class AnomalyDetection(BaseModel):
    root_cause_tags: list[str] = Field(description="Strict categorical tags mapping the issue. Use EXACTLY from: ['overheating', 'power_surge', 'network_latency', 'cooling_failure', 'hardware_aging']. Empty if stable.")
    anomalies: list[str] = Field(description="Human readable description of the anomalies.")

class RecommendedAction(BaseModel):
    action_title: str = Field(description="The short actionable fix (e.g., Deploy Secondary Cooling Unit).")
    action_explanation: str = Field(description="A clear, simple 1-sentence explanation of what the action broadly means so a non-technical user can understand it.")
    confidence_score: int = Field(description="Confidence score from 0-100 indicating how likely this resolves the anomaly based on historical success and relevance.")
    reasoning_pointers: list[str] = Field(description="List of 2-3 specific pointer-length sentences explaining why this action was chosen based on historical context, citing exact matches.")

class ActionResolution(BaseModel):
    recommendations: list[RecommendedAction] = Field(description="A list of 2-3 possible recommendations, ordered by confidence score.")

anomaly_llm = llm.with_structured_output(AnomalyDetection)
resolution_llm = llm.with_structured_output(ActionResolution)


# ----------------- Nodes -----------------
def fetch_metrics(state: OperationsState) -> dict:
    """Fetch real-time metrics for the facility via Redis."""
    dc_id = state.get("dc_id")
    
    keys_to_fetch = ["status", "temp", "cpu_load", "power_usage", "latency", "fan_speed_rpm", "network_bandwidth_gbps"]
    metrics = {}
    for k in keys_to_fetch:
        val = redis_client.get_raw(f"dc:{dc_id}:{k}")
        if val is not None:
            try:
                metrics[k] = float(val) if '.' in val else int(val)
            except ValueError:
                metrics[k] = val
    
    if not metrics:
        return {"metrics": {}, "status": "No Active Telemetry Found", "historical_context": []}
    
    return {"metrics": metrics, "status": "Metrics Fetched", "historical_context": []}

def detect_anomalies(state: OperationsState) -> dict:
    """Analyze fetched metrics for anomalies and generate root cause tags."""
    metrics = state.get("metrics", {})
    
    prompt = f"""
    You are an AI Operations Agent monitoring Data Center telemetry.

    Current live metrics:
    {metrics}

    Available root_cause_tags (choose 1–2 max):
    ['overheating','power_surge','network_latency','cooling_failure',
     'thermal_stress','cooling_efficiency_drop','power_instability',
     'network_degradation','memory_pressure','compute_saturation',
     'sensor_anomaly','multi_signal_risk','coolant_loop_failure']

    Task:
    1. Detect if system is degraded
    2. Identify MOST LIKELY root cause using MULTIPLE signals

    Signal logic:
    - thermal_stress: temp rising + load/memory increase
    - cooling_efficiency_drop: temp rising + cooling RPM dropping
    - power_instability/power_surge: sudden power spike ± temp impact
    - network_degradation/network_latency: high packet loss
    - memory_pressure: active_memory near capacity
    - compute_saturation: sustained high CPU/load
    - sensor_anomaly: inconsistent/unrealistic readings
    - multi_signal_risk: multiple moderate anomalies together
    - coolant_loop_failure: coolant_temp_out spikes significantly (>30F) above ambient temp.
    - pump_malfunction: coolant_temp_out is high but fan_speed_rpm is normal/low.

    Guidelines:
    - DO NOT default to overheating
    - Use at least 2 correlated signals when possible
    - Prefer specific tags over generic ones
    - If no strong issue → return empty tags

    Output:
    - root_cause_tags: list (max 2)
    - anomalies: short explanation with metric values
    """
    
    analysis = anomaly_llm.invoke(prompt)
    
    combined = []
    if analysis.root_cause_tags:
        combined.append(f"TAGS: {','.join(analysis.root_cause_tags)}")
    combined.extend(analysis.anomalies)

    return {
        "detected_anomalies": combined,
        "status": "Anomalies Detected" if combined else "Normal"
    }

def retrieve_context(state: OperationsState) -> dict:
    """Query Neo4j globally for incidents matching the current anomaly signature."""
    anomalies = state.get("detected_anomalies", [])
    
    tags = []
    if len(anomalies) > 0 and anomalies[0].startswith("TAGS: "):
        tags = [t.strip() for t in anomalies[0].replace("TAGS: ", "").split(",")]
    
    historical_context = []
    
    # Global Incident Signature Search: Ignore DC ID and focus on the Problem Signature
    # This finds incidents with the same root cause or type across the entire network
    for tag in tags:
        query = """
        MATCH (inc:Incident)
        WHERE inc.root_cause = $tag OR inc.type = $tag
        MATCH (inc)<-[:RESOLVED_BY]-(maint:MaintenanceEvent)
        RETURN 
            inc.type AS type, 
            inc.severity AS severity, 
            maint.type AS fix, 
            maint.effect AS effect
        ORDER BY inc.severity DESC
        LIMIT 3
        """
        results = neo4j_client.run_query(query, {"tag": tag})
        for r in results:
            ctx = f"Historical Context: A past '{r['type']}' incident was successfully resolved by [{r['fix']}] resulting in {r['effect']}."
            historical_context.append(ctx)
            
    if not historical_context:
        historical_context.append("NO SIMILAR INCIDENTS FOUND IN GLOBAL HISTORICAL GRAPHDB.")
        
    return {"historical_context": list(set(historical_context)), "status": "Context Retrieved"}

def generate_resolution(state: OperationsState) -> dict:
    """Synthesize final resolution purely from metrics and Neo4j historical context."""
    anomalies = state.get("detected_anomalies", [])
    context = state.get("historical_context", [])
    metrics = state.get("metrics", {})
    
    prompt = f"""
    You are an AI Operations Agent resolving a live anomaly.
    
    Live Metrics: {metrics}
    Identified Issues: {anomalies}
    
    CRITICAL HISTORICAL CONTEXT (Similar Incidents from GraphDB):
    {context}
    
    Task: Write a strictly formatted resolution providing multiple reasonable fixes. 
    
    STRICT SCORING RULES:
    1. If 'CRITICAL HISTORICAL CONTEXT' contains matching historical records, score based on relevance (up to 95%).
    2. If 'CRITICAL HISTORICAL CONTEXT' indicates "NO SIMILAR INCIDENTS FOUND" (or is empty), the 'confidence_score' MUST BE between 10% and 30% only. DO NOT exceed 30%.
    
    CONTENT RULES:
    - Provide a clear 'action_title'.
    - Provide a clear 1-sentence 'action_explanation'.
    - Use 'reasoning_pointers' to explicitly explain WHY this action was chosen.
    - If context was missing, start the FIRST pointer with: "⚠️ UNVERIFIED: No similar historical patterns were found in logs. This is a zero-shot recommendation with 10-30% confidence."
    - Do NOT guess data points.
    """
    
    resolution = resolution_llm.invoke(prompt)
    
    return {
        "recommended_actions": [r.dict() for r in resolution.recommendations], 
        "status": "Resolution Complete"
    }




# ----------------- Build LangGraph -----------------
builder = StateGraph(OperationsState)
builder.add_node("fetch_metrics", fetch_metrics)
builder.add_node("detect_anomalies", detect_anomalies)
builder.add_node("retrieve_context", retrieve_context)
builder.add_node("generate_resolution", generate_resolution)

builder.set_entry_point("fetch_metrics")

# Automatically escape graph execution if system is entirely optimal
def should_continue(state: OperationsState):
    metrics = state.get("metrics", {})
    if not metrics or metrics.get("status") == "optimal":
        return END
    return "detect_anomalies"

builder.add_conditional_edges("fetch_metrics", should_continue)
builder.add_edge("detect_anomalies", "retrieve_context")
builder.add_edge("retrieve_context", "generate_resolution")
builder.add_edge("generate_resolution", END)

operations_graph = builder.compile()
