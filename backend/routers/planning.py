from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import os
import json
from google import genai
from google.genai import types
from backend.database.neo4j_client import neo4j_client

router = APIRouter()

STATE_TO_ZONE = {
    "Texas":      "texas_hot_zone",
    "California": "california_mild_zone",
    "Washington": "california_mild_zone",
    "Virginia":   "virginia_humid_zone",
    "Nevada":     "nevada_desert_zone",
    "New York":   "newyork_cold_zone",
    "Ohio":       "newyork_cold_zone",
    "Illinois":   "newyork_cold_zone",
    "Florida":    "florida_tropical_zone",
}

ZONE_TO_STATE = {
    "texas_hot_zone":        "Texas",
    "california_mild_zone":  "California",
    "virginia_humid_zone":   "Virginia",
    "nevada_desert_zone":    "Nevada",
    "newyork_cold_zone":     "New York",
    "florida_tropical_zone": "Florida",
}

ZONE_COORDS = {
    "texas_hot_zone":        {"lat": 31.0,  "lon": -99.0},
    "california_mild_zone":  {"lat": 36.7,  "lon": -119.4},
    "virginia_humid_zone":   {"lat": 37.4,  "lon": -78.6},
    "nevada_desert_zone":    {"lat": 38.8,  "lon": -116.4},
    "newyork_cold_zone":     {"lat": 40.7,  "lon": -74.0},
    "florida_tropical_zone": {"lat": 27.9,  "lon": -81.5},
}

ALL_US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming"
]


class PlanningRequest(BaseModel):
    budget_million_usd: float
    capacity_mw: float
    preferred_states: List[str]


@router.get("/agent/planning/states")
async def get_all_states():
    return {"status": "success", "states": ALL_US_STATES}


def _query_all_zone_metrics():
    """Pull all available metrics from Neo4j for every zone."""
    zone_rows = neo4j_client.run_query("""
        MATCH (loc:Location)
        OPTIONAL MATCH (loc)<-[:LOCATED_IN]-(dc:DataCenter)
        OPTIONAL MATCH (dc)-[:HAS_PERFORMANCE]->(perf:PerformanceSnapshot)
        OPTIONAL MATCH (dc)-[:USES_COOLING]->(cs:CoolingSystem)
        RETURN
          loc.id AS zone_id, loc.climate AS climate,
          loc.avg_temp AS avg_temp_c, loc.humidity AS humidity_pct,
          loc.energy_cost_index AS energy_cost_index,
          count(DISTINCT dc) AS dc_count,
          avg(dc.capacity_mw) AS avg_capacity_mw,
          sum(dc.capacity_mw) AS total_capacity_mw,
          avg(perf.pue) AS avg_pue, avg(perf.uptime) AS avg_uptime_pct,
          avg(perf.latency_ms) AS avg_latency_ms,
          avg(cs.efficiency_score) AS avg_cooling_efficiency
        ORDER BY zone_id
    """)

    inc_counts = {
        r["zone_id"]: r["total_incidents"]
        for r in neo4j_client.run_query("""
            MATCH (loc:Location)<-[:LOCATED_IN]-(dc:DataCenter)-[:EXPERIENCED]->(inc:Incident)
            RETURN loc.id AS zone_id, count(inc) AS total_incidents
        """)
    }

    maint_rows = {
        r["zone_id"]: r
        for r in neo4j_client.run_query("""
            MATCH (loc:Location)<-[:LOCATED_IN]-(dc:DataCenter)
            MATCH (maint:MaintenanceEvent)-[:RESOLVED_BY]->(:Incident)<-[:EXPERIENCED]-(dc)
            RETURN loc.id AS zone_id,
                   collect(DISTINCT maint.cost_level)[0..3] AS maint_cost_levels,
                   collect(DISTINCT maint.effect)[0..3] AS maint_effects
        """)
    }

    dc_list = neo4j_client.run_query("""
        MATCH (dc:DataCenter)-[:LOCATED_IN]->(loc:Location)
        RETURN dc.id AS id, dc.name AS name, dc.location AS location,
               dc.latitude AS latitude, dc.longitude AS longitude,
               dc.capacity_mw AS capacity_mw, dc.operational_since AS operational_since,
               loc.id AS zone_id
        ORDER BY dc.capacity_mw DESC
    """)

    zones = {}
    for row in zone_rows:
        z = row["zone_id"]
        zones[z] = {
            "zone_id":                z,
            "representative_state":   ZONE_TO_STATE.get(z, z),
            "climate":                row["climate"],
            "avg_temp_c":             round(row["avg_temp_c"] or 0, 1),
            "humidity_pct":           round(row["humidity_pct"] or 0, 1),
            "energy_cost_index":      round(row["energy_cost_index"] or 0, 2),
            "dc_count":               int(row["dc_count"] or 0),
            "avg_capacity_mw":        round(row["avg_capacity_mw"] or 0, 1),
            "total_capacity_mw":      round(row["total_capacity_mw"] or 0, 1),
            "avg_pue":                round(row["avg_pue"] or 0, 4),
            "avg_uptime_pct":         round(row["avg_uptime_pct"] or 0, 4),
            "avg_latency_ms":         round(row["avg_latency_ms"] or 0, 1),
            "avg_cooling_efficiency": round(row["avg_cooling_efficiency"] or 0, 4),
            "total_incidents":        inc_counts.get(z, 0),
            "maintenance_profile":    maint_rows.get(z, {}),
        }
    return zones, dc_list


def _compute_score(z: dict, is_preferred: bool, capacity_mw: float,
                   budget_per_mw: float) -> float:
    """
    Multi-factor scoring for a zone, fully driven by GraphDB values.
    Weights shift based on user-supplied capacity & budget.
    """
    budget_tight = budget_per_mw < 3.0
    dc_count = z["dc_count"] or 1
    ipc = z["total_incidents"] / dc_count

    # --- individual dimension scores (each 0–1, before weighting) -------------
    # Energy cost: lower is better (scale 0.5–1.5 in DB)
    energy = max(0, 1 - (z["energy_cost_index"] - 0.5) / 1.0)

    # PUE: lower is better (DB range ~1.43–1.50)
    pue = max(0, 1 - (z["avg_pue"] - 1.0) / 0.8)

    # Uptime: higher is better (DB range 98.87–99.14)
    uptime = max(0, (z["avg_uptime_pct"] - 98.0) / 2.0)

    # Latency: lower is better (DB range ~83–87 ms)
    latency = max(0, 1 - z["avg_latency_ms"] / 120)

    # Cooling efficiency: higher is better (DB range 0.70–0.86)
    cooling = z["avg_cooling_efficiency"]

    # Incident density: lower is better
    inc = max(0, 1 - ipc / 30)

    # Capacity fit: zero penalty if avg_capacity >= required; else proportional penalty
    cap_ratio = min(1.0, z["avg_capacity_mw"] / max(capacity_mw, 1))

    # --- weights (sum to 100) --------------------------------------------------
    w_energy  = 35 if budget_tight else 20
    w_pue     = 20
    w_uptime  = 10
    w_latency = 5
    w_cooling = 10
    w_inc     = 10
    w_cap     = 25 - (w_energy - 20)   # frees up weight when energy is lower priority

    raw = (
        energy  * w_energy +
        pue     * w_pue +
        uptime  * w_uptime +
        latency * w_latency +
        cooling * w_cooling +
        inc     * w_inc +
        cap_ratio * w_cap
    )

    # Preferred state bonus — meaningful but not overwhelming
    pref_bonus = 12 if is_preferred else 0
    return round(raw + pref_bonus, 3)


@router.post("/agent/planning")
async def run_planning_agent(req: PlanningRequest):
    """
    Planning Agent: uses ONLY Neo4j GraphDB data.
    Scoring is user-input-aware (budget tightness, capacity requirement, preferred states).
    """

    # ── 1. GraphDB data ───────────────────────────────────────────────────────
    zones, dc_list = _query_all_zone_metrics()

    preferred_zone_ids = list({STATE_TO_ZONE[s] for s in req.preferred_states if s in STATE_TO_ZONE})
    preferred_zones    = {z: zones[z] for z in preferred_zone_ids if z in zones}
    all_zones          = zones

    budget_per_mw  = req.budget_million_usd / max(req.capacity_mw, 1)
    budget_tight   = budget_per_mw < 3.0

    # ── 2. Score every zone with user-aware function ──────────────────────────
    scored = sorted(
        [(z, _compute_score(z, z["zone_id"] in preferred_zone_ids, req.capacity_mw, budget_per_mw))
         for z in all_zones.values()],
        key=lambda t: t[1], reverse=True
    )

    max_s = scored[0][1]
    min_s = scored[-1][1]
    def normalise(s):
        if max_s == min_s:
            return 75
        return max(5, min(99, int(40 + (s - min_s) / (max_s - min_s) * 55)))

    best, best_score   = scored[0]
    best_is_pref       = best["zone_id"] in preferred_zone_ids
    alternates_scored  = scored[1:4]

    def build_row(zone, score, is_rec):
        ipc = round(zone["total_incidents"] / zone["dc_count"], 1) if zone["dc_count"] else 0
        is_pref = zone["zone_id"] in preferred_zone_ids
        return {
            "zone_id":              zone["zone_id"],
            "state":                zone["representative_state"],
            "is_recommended":       is_rec,
            "energy_cost_index":    zone["energy_cost_index"],
            "avg_temp_c":           zone["avg_temp_c"],
            "humidity_pct":         zone["humidity_pct"],
            "avg_pue":              round(zone["avg_pue"], 3),
            "avg_uptime_pct":       round(zone["avg_uptime_pct"], 2),
            "avg_latency_ms":       round(zone["avg_latency_ms"], 1),
            "avg_cooling_efficiency": round(zone["avg_cooling_efficiency"], 3),
            "total_incidents":      zone["total_incidents"],
            "incidents_per_dc":     ipc,
            "avg_capacity_mw":      zone["avg_capacity_mw"],
            "overall_score":        normalise(score),
            "score_rationale":      (
                f"{'★ Preferred. ' if is_pref else ''}"
                f"energy={zone['energy_cost_index']}, pue={round(zone['avg_pue'],3)}, "
                f"uptime={round(zone['avg_uptime_pct'],2)}%, inc/dc={ipc}, "
                f"avg_cap={zone['avg_capacity_mw']}MW"
            )
        }

    comparison_table = [build_row(z, s, z["zone_id"] == best["zone_id"]) for z, s in scored]

    ipc_best = round(best["total_incidents"] / best["dc_count"], 1) if best["dc_count"] else 0
    cap_note = ("meets zone average" if req.capacity_mw <= best["avg_capacity_mw"]
                else f"exceeds zone avg by {req.capacity_mw - best['avg_capacity_mw']:.0f}MW")

    # ── 3. LLM call ───────────────────────────────────────────────────────────
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "error": "GEMINI_API_KEY not configured"}

    client = genai.Client(api_key=api_key)

    pref_section = (
        json.dumps(preferred_zones, indent=2)
        if preferred_zones
        else "No preferred zones specified — evaluate all zones on merit."
    )

    prompt = f"""
You are an expert Data Center Site Selection AI Agent with live GraphDB access.
STRICT RULE: Every number in your output MUST come from the GRAPHDB DATA provided.
No invented, estimated, or hallucinated values. Arithmetic on DB values (e.g. total_incidents / dc_count) is allowed.

═══════════════════════════════════════════════════════════
USER REQUIREMENTS
═══════════════════════════════════════════════════════════
Budget:            ${req.budget_million_usd:.1f}M USD  (≈ ${budget_per_mw:.1f}M/MW — {'TIGHT' if budget_tight else 'COMFORTABLE'})
Capacity Required: {req.capacity_mw:.1f} MW
Preferred States:  {', '.join(req.preferred_states) if req.preferred_states else 'None — evaluate all zones equally'}

DECISION CONSTRAINTS:
• PREFERRED STATES ARE HIGH PRIORITY. If any preferred zone exists in the DB, recommend it
  UNLESS its GraphDB metrics are definitively worse on EVERY dimension vs another zone.
• Use the pre-computed scores below as your primary ranking signal.
• Only override a preferred zone if its energy_cost_index is > 1.5× that of a better alternative
  AND its avg_pue is higher AND its incidents/DC is higher.

PRE-COMPUTED SCORES (from server-side user-aware scorer):
{json.dumps([{"zone_id": z["zone_id"], "state": z["representative_state"],
              "is_preferred": z["zone_id"] in preferred_zone_ids,
              "composite_score": round(s, 2),
              "normalised_0_99": normalise(s)}
             for z, s in scored], indent=2)}

═══════════════════════════════════════════════════════════
GRAPHDB — PREFERRED ZONE DETAILS
═══════════════════════════════════════════════════════════
{pref_section}

═══════════════════════════════════════════════════════════
GRAPHDB — ALL ZONES
═══════════════════════════════════════════════════════════
{json.dumps(all_zones, indent=2)}

═══════════════════════════════════════════════════════════
INSTRUCTIONS
═══════════════════════════════════════════════════════════
1. Pick the recommended zone from the pre-computed ranking. Justify with DB values.
2. List 3 alternates from the ranking.
3. Include ALL zones in comparison_table, ordered by overall_score DESC.
4. incidents_per_dc = total_incidents / dc_count.
5. Cite ≥3 specific DB values in recommendation_reasoning.

Return ONLY valid JSON (no markdown wrapper):
{{
  "recommended_zone_id": "string",
  "recommended_state": "string",
  "recommended_zone_coords": {{"lat": number, "lon": number}},
  "recommendation_reasoning": "string",
  "confidence_score": number,
  "alternates": [
    {{"zone_id": "string", "state": "string",
      "zone_coords": {{"lat": number, "lon": number}},
      "brief_reason": "string"}}
  ],
  "comparison_table": [
    {{
      "zone_id": "string", "state": "string", "is_recommended": boolean,
      "energy_cost_index": number, "avg_temp_c": number, "humidity_pct": number,
      "avg_pue": number, "avg_uptime_pct": number, "avg_latency_ms": number,
      "avg_cooling_efficiency": number, "total_incidents": number,
      "incidents_per_dc": number, "avg_capacity_mw": number,
      "overall_score": number, "score_rationale": "string"
    }}
  ],
  "budget_assessment": "string",
  "capacity_feasibility": "string"
}}
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        raw = response.text.strip().strip("```json").strip("```").strip()
        result = json.loads(raw)
        result["existing_dcs"] = dc_list
        result["graphdb_zones"] = all_zones
        return {"status": "success", "data": result}

    except Exception as e:
        print(f"Gemini Planning Error (using deterministic fallback): {e}")

        # Fully deterministic fallback — same user-aware ranking, no randomness
        return {"status": "success", "data": {
            "recommended_zone_id":     best["zone_id"],
            "recommended_state":       best["representative_state"],
            "recommended_zone_coords": ZONE_COORDS.get(best["zone_id"], {"lat": 38.0, "lon": -97.0}),
            "recommendation_reasoning": (
                f"{'Preferred state prioritised. ' if best_is_pref else 'No preferred states in DB — top-ranked zone selected. '}"
                f"{best['representative_state']} leads the user-aware composite score "
                f"(budget ${budget_per_mw:.1f}M/MW — {'tight' if budget_tight else 'comfortable'}): "
                f"energy_cost_index={best['energy_cost_index']}, avg_pue={round(best['avg_pue'],3)}, "
                f"avg_uptime={round(best['avg_uptime_pct'],2)}%, avg_latency={round(best['avg_latency_ms'],1)}ms, "
                f"{ipc_best} incidents/DC, avg_capacity_mw={best['avg_capacity_mw']} ({cap_note})."
            ),
            "confidence_score": normalise(best_score),
            "alternates": [
                {
                    "zone_id": z["zone_id"],
                    "state":   z["representative_state"],
                    "zone_coords": ZONE_COORDS.get(z["zone_id"], {"lat": 38.0, "lon": -97.0}),
                    "brief_reason": (
                        f"energy_cost_index={z['energy_cost_index']}, avg_pue={round(z['avg_pue'],3)}, "
                        f"incidents/DC={round(z['total_incidents']/z['dc_count'],1) if z['dc_count'] else 'N/A'}"
                    )
                }
                for z, s in alternates_scored
            ],
            "comparison_table": sorted(comparison_table, key=lambda r: r["overall_score"], reverse=True),
            "budget_assessment": (
                f"${req.budget_million_usd:.1f}M at ${budget_per_mw:.1f}M/MW is "
                f"{'tight — energy_cost_index weighted at 35%' if budget_tight else 'comfortable — reliability metrics weighted higher'}. "
                f"{best['representative_state']} energy_cost_index={best['energy_cost_index']}."
            ),
            "capacity_feasibility": (
                f"{req.capacity_mw:.1f}MW vs {best['representative_state']} avg_capacity_mw={best['avg_capacity_mw']}MW — {cap_note}."
            ),
            "existing_dcs": dc_list,
            "graphdb_zones": all_zones,
        }}
