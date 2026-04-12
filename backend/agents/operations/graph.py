import os
from langgraph.graph import StateGraph, END
from backend.agents.operations.state import OperationsState
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.database.redis_client import redis_client
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv(".env")

# Try importing from api_secrets if it exists, otherwise use env var
try:
    from backend.api_secrets import GEMINI_API_KEY
except ImportError:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY)

class AnomalyAnalysis(BaseModel):
    anomalies: list[str] = Field(description="List of detected specific issues. Try to be very specific about the surge percentage or metric bounds. Empty if normal.")
    recommended_action: str = Field(description="Single, clear actionable response to mitigate the anomaly. Use 'None' if system is stable.")

structured_llm = llm.with_structured_output(AnomalyAnalysis)

def fetch_metrics(state: OperationsState) -> dict:
    """Fetch real-time metrics for the facility via Redis."""
    dc_id = state.get("dc_id")
    
    # We now fetch the flat keys pushed by simulate_live_redis.py
    keys_to_fetch = ["status", "temp", "cpu_load", "power_usage", "latency", "fan_speed_rpm", "network_bandwidth_gbps"]
    metrics = {}
    for k in keys_to_fetch:
        val = redis_client.get_raw(f"dc:{dc_id}:{k}")
        if val is not None:
            # try converting to float if possible for cleaner LLM injection
            try:
                metrics[k] = float(val) if '.' in val else int(val)
            except ValueError:
                metrics[k] = val
    
    if not metrics:
        return {"metrics": {}, "status": "No Active Telemetry Found"}
    
    return {"metrics": metrics, "status": "Metrics Fetched"}

def analyze_anomalies(state: OperationsState) -> dict:
    """Analyze fetched metrics for anomalies and generate response."""
    metrics = state.get("metrics", {})
    if not metrics:
        return state
    
    prompt = f"""
    You are an AI Operations Agent monitoring Data Center {state['dc_id']}.
    Current live telemtry from Redis stream:
    {metrics}
    
    Task: 
    1. Identify any out of bound anomalies (e.g. Temp > 85, CPU > 85%, memory spikes, etc).
    2. Provide a single, specific recommended action to resolve the most severe anomaly.
    """
    
    analysis = structured_llm.invoke(prompt)
    
    return {
        "detected_anomalies": analysis.anomalies,
        "recommended_action": analysis.recommended_action,
        "status": "Analysis Complete"
    }

# Build LangGraph
builder = StateGraph(OperationsState)
builder.add_node("fetch_metrics", fetch_metrics)
builder.add_node("analyze_anomalies", analyze_anomalies)

builder.set_entry_point("fetch_metrics")
builder.add_edge("fetch_metrics", "analyze_anomalies")
builder.add_edge("analyze_anomalies", END)

operations_graph = builder.compile()
