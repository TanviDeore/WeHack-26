import random
import uuid
from datetime import datetime, timedelta
from backend.database.neo4j_client import neo4j_client
from backend.database.redis_client import redis_client

def generate_synthetic_graph_data():
    print("Generating Synthetic Graph Data for Neo4j...")
    
    # 1. Clean existing data
    neo4j_client.run_query("MATCH (n) DETACH DELETE n")

    # Synthetic Node Definitions based on expected schemas
    # 1. Location
    locations = [
        {"id": "texas_hot_zone", "climate": "hot", "avg_temp": 38.0, "humidity": 60.0, "energy_cost_index": 0.8},
        {"id": "norway_cold_zone", "climate": "cold", "avg_temp": 5.0, "humidity": 40.0, "energy_cost_index": 0.4},
        {"id": "singapore_humid_zone", "climate": "tropical", "avg_temp": 32.0, "humidity": 85.0, "energy_cost_index": 0.9}
    ]

    # 2. Cooling Systems
    cooling_systems = [
        {"id": "air_cooling_v1", "type": "air_cooling", "efficiency_score": 0.6},
        {"id": "liquid_cooling_v2", "type": "liquid_immersion", "efficiency_score": 0.95},
        {"id": "free_cooling_v1", "type": "ambient_air", "efficiency_score": 0.85}
    ]

    # 3. Data Centers
    datacenters = [
        {"id": "dc_texas_01", "name": "Texas Data Center", "location": "Texas, USA", "latitude": 30.2672, "longitude": -97.7431, "capacity_mw": 50.0, "operational_since": "2022"},
        {"id": "dc_oslo_01", "name": "Oslo Deep Data", "location": "Oslo, Norway", "latitude": 59.9139, "longitude": 10.7522, "capacity_mw": 120.0, "operational_since": "2020"},
        {"id": "dc_sg_02", "name": "Singapore Core", "location": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "capacity_mw": 80.0, "operational_since": "2024"}
    ]

    # Cypher Queries to insert nodes
    for loc in locations:
        neo4j_client.run_query("""
            MERGE (n:Location {id: $id})
            SET n.climate = $climate, n.avg_temp = $avg_temp, n.humidity = $humidity, n.energy_cost_index = $energy_cost_index
        """, loc)

    for cs in cooling_systems:
        neo4j_client.run_query("""
            MERGE (n:CoolingSystem {id: $id})
            SET n.type = $type, n.efficiency_score = $efficiency_score
        """, cs)

    for dc in datacenters:
        neo4j_client.run_query("""
            MERGE (n:DataCenter {id: $id})
            SET n.name = $name, n.location = $location, n.latitude = $latitude, n.longitude = $longitude, n.capacity_mw = $capacity_mw, n.operational_since = $operational_since
        """, dc)

    # Establish Static Relationships
    neo4j_client.run_query("MATCH (dc:DataCenter {id: 'dc_texas_01'}), (loc:Location {id: 'texas_hot_zone'}) MERGE (dc)-[:LOCATED_IN]->(loc)")
    neo4j_client.run_query("MATCH (dc:DataCenter {id: 'dc_texas_01'}), (cs:CoolingSystem {id: 'air_cooling_v1'}) MERGE (dc)-[:USES_COOLING]->(cs)")
    
    neo4j_client.run_query("MATCH (dc:DataCenter {id: 'dc_oslo_01'}), (loc:Location {id: 'norway_cold_zone'}) MERGE (dc)-[:LOCATED_IN]->(loc)")
    neo4j_client.run_query("MATCH (dc:DataCenter {id: 'dc_oslo_01'}), (cs:CoolingSystem {id: 'free_cooling_v1'}) MERGE (dc)-[:USES_COOLING]->(cs)")

    neo4j_client.run_query("MATCH (dc:DataCenter {id: 'dc_sg_02'}), (loc:Location {id: 'singapore_humid_zone'}) MERGE (dc)-[:LOCATED_IN]->(loc)")
    neo4j_client.run_query("MATCH (dc:DataCenter {id: 'dc_sg_02'}), (cs:CoolingSystem {id: 'liquid_cooling_v2'}) MERGE (dc)-[:USES_COOLING]->(cs)")

    # Similar Nodes
    neo4j_client.run_query("MATCH (dc1:DataCenter {id: 'dc_texas_01'}), (dc2:DataCenter {id: 'dc_sg_02'}) MERGE (dc1)-[:SIMILAR_TO {reason: 'high_ambient_temp'}]-(dc2)")

    # 4. Generate Timeseries synthetic events (Incidents, Maintenance, Performance)
    incident_types = ['overheating', 'power_surge', 'network_latency', 'cooling_failure']
    maintenance_types = ['cooling_upgrade', 'server_rack_replacement', 'hvac_calibration']
    
    for i in range(5):
        dc_target = random.choice(datacenters)["id"]
        cool_target = "air_cooling_v1" if dc_target == "dc_texas_01" else ("free_cooling_v1" if dc_target == "dc_oslo_01" else "liquid_cooling_v2")
        
        inc_id = f"incident_00{i}"
        inc = {
            "id": inc_id,
            "type": random.choice(incident_types),
            "severity": random.choice(["low", "medium", "high", "critical"]),
            "timestamp": (datetime.now() - timedelta(days=random.randint(1, 300))).strftime("%Y-%m-%d"),
            "duration_minutes": random.randint(15, 240),
            "root_cause": random.choice(["cooling_failure", "grid_instability", "hardware_aging"])
        }
        
        maint_id = f"maintenance_00{i}"
        maint = {
            "id": maint_id,
            "type": random.choice(maintenance_types),
            "cost_level": random.choice(["low", "medium", "high"]),
            "effect": "reduced_overheating" if inc["type"] == "overheating" else "improved_stability"
        }
        
        perf_id = f"perf_00{i}"
        perf = {
            "id": perf_id,
            "pue": round(random.uniform(1.1, 1.8), 2),
            "latency_ms": random.randint(20, 150),
            "uptime": round(random.uniform(98.0, 99.99), 2)
        }

        # Insert Incident
        neo4j_client.run_query("""
            MERGE (n:Incident {id: $id})
            SET n.type = $type, n.severity = $severity, n.timestamp = $timestamp, n.duration_minutes = $duration_minutes, n.root_cause = $root_cause
        """, inc)
        
        # Insert Maintenance
        neo4j_client.run_query("""
            MERGE (n:MaintenanceEvent {id: $id})
            SET n.type = $type, n.cost_level = $cost_level, n.effect = $effect
        """, maint)

        # Insert Performance
        neo4j_client.run_query("""
            MERGE (n:PerformanceSnapshot {id: $id})
            SET n.pue = $pue, n.latency_ms = $latency_ms, n.uptime = $uptime
        """, perf)

        # Edges
        # DC Experienced Incident
        neo4j_client.run_query("""
            MATCH (dc:DataCenter {id: $dc_id}), (inc:Incident {id: $inc_id})
            MERGE (dc)-[:EXPERIENCED {weight: 0.8, timestamp: $timestamp}]->(inc)
        """, {"dc_id": dc_target, "inc_id": inc_id, "timestamp": inc["timestamp"]})
        
        # Incident Caused By Cooling
        neo4j_client.run_query("""
            MATCH (inc:Incident {id: $inc_id}), (cs:CoolingSystem {id: $cs_id})
            MERGE (inc)-[:CAUSED_BY {weight: 0.9, timestamp: $timestamp}]->(cs)
        """, {"inc_id": inc_id, "cs_id": cool_target, "timestamp": inc["timestamp"]})

        # Maintenance Resolved Incident
        neo4j_client.run_query("""
            MATCH (maint:MaintenanceEvent {id: $maint_id}), (inc:Incident {id: $inc_id})
            MERGE (maint)-[:RESOLVED_BY]->(inc)
        """, {"maint_id": maint_id, "inc_id": inc_id})

        # Maintenance Improved DC Performance
        neo4j_client.run_query("""
            MATCH (maint:MaintenanceEvent {id: $maint_id}), (perf:PerformanceSnapshot {id: $perf_id})
            MERGE (maint)-[:IMPROVED_BY]->(perf)
        """, {"maint_id": maint_id, "perf_id": perf_id})

        # Attach snapshot to DC
        neo4j_client.run_query("""
            MATCH (dc:DataCenter {id: $dc_id}), (perf:PerformanceSnapshot {id: $perf_id})
            MERGE (dc)-[:HAS_PERFORMANCE]->(perf)
        """, {"dc_id": dc_target, "perf_id": perf_id})

    print("Synthetic Graph Data successfully populated into Neo4j!")

if __name__ == "__main__":
    print("Starting synthetic data generation script...")
    generate_synthetic_graph_data()
    print("Process complete!")
