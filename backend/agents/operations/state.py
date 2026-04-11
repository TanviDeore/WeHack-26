from typing import TypedDict, Optional, List, Dict, Any

class OperationsState(TypedDict):
    """
    The state for the LangGraph operations agent.
    """
    dc_id: str
    metrics: Dict[str, Any]
    detected_anomalies: List[str]
    recommended_action: Optional[str]
    action_taken: Optional[str]
    status: str
