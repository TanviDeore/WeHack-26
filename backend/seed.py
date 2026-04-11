import time
from backend.database.neo4j_client import neo4j_client
from backend.database.redis_client import redis_client

def seed_graph_db():
    print("Seeding Neo4j Graph Database...")
    query = """
    MERGE (dc:DataCenter {id: 'dc_texas_01'})
    SET dc.name = 'Texas Data Center', 
        dc.location = 'Texas, USA', 
        dc.latitude = 30.2672, 
        dc.longitude = -97.7431, 
        dc.capacity_mw = 50.0, 
        dc.operational_since = '2022'

    MERGE (loc:Location {id: 'texas_hot_zone'})
    SET loc.climate = 'hot', 
        loc.avg_temp = 38.0, 
        loc.humidity = 60.0, 
        loc.energy_cost_index = 0.8

    MERGE (cool:CoolingSystem {id: 'air_cooling_v1'})
    SET cool.type = 'air_cooling', 
        cool.efficiency_score = 0.6

    MERGE (inc:Incident {id: 'incident_001'})
    SET inc.type = 'overheating', 
        inc.severity = 'high', 
        inc.timestamp = '2025-10-10', 
        inc.duration_minutes = 45, 
        inc.root_cause = 'cooling_failure'

    MERGE (dc)-[:LOCATED_IN]->(loc)
    MERGE (dc)-[:USES_COOLING]->(cool)
    MERGE (dc)-[:EXPERIENCED {weight: 0.8, timestamp: '2025-10-10'}]->(inc)
    MERGE (inc)-[:CAUSED_BY]->(cool)
    """
    try:
        neo4j_client.run_query(query)
        print("Neo4j seeding successful!")
    except Exception as e:
        print(f"Neo4j seeding failed: {e}")

def seed_redis():
    print("Seeding Redis Realtime Memory...")
    try:
        live_state = {
            "dc_id": "dc_texas_01",
            "status": "degraded",
            "temperature": 92.0,
            "cpu_load": 87.0,
            "power_usage": 78.0,
            "latency": 120.0
        }
        redis_client.set_state("dc:dc_texas_01:status", live_state)
        
        alert = {
            "message": "cooling_stress_detected",
            "severity": "high",
            "timestamp": "2026-04-11T10:05"
        }
        redis_client.set_state("alert:dc_texas_01", alert)
        
        redis_client.push_event("recent:event:dc_texas_01", "temp_spike")
        redis_client.push_event("recent:event:dc_texas_01", "cpu_spike")
        redis_client.push_event("recent:event:dc_texas_01", "fan_speed_increase")
        print("Redis seeding successful!")
    except Exception as e:
        print(f"Redis seeding failed: {e}")

if __name__ == "__main__":
    print("Starting seed script...")
    seed_graph_db()
    seed_redis()
    print("Seed complete!")
