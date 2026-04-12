from typing import TypedDict, Optional, List, Dict, Any

class OperationsState(TypedDict):
    """
    The state for the LangGraph operations agent.
    """
    dc_id: str
    metrics: Dict[str, Any]
    detected_anomalies: List[str]
    recommended_action_title: Optional[str]
    recommended_action_explanation: Optional[str]
    recommended_action_pointers: Optional[List[str]]
    recommended_actions: Optional[List[Dict[str, Any]]]
    action_taken: Optional[str]
    status: str
    historical_context: List[str]

