import random
from datetime import datetime, timedelta
from backend.database.neo4j_client import neo4j_client

def generate_synthetic_graph_data():
    print("Generating MASSIVE USA-based Synthetic Graph Data for Neo4j...")
    
    # 1. Clean existing data
    neo4j_client.run_query("MATCH (n) DETACH DELETE n")

    # Synthetic Node Definitions
    locations = [
        {"id": "texas_hot_zone", "climate": "hot", "avg_temp": 38.0, "humidity": 60.0, "energy_cost_index": 0.8},
        {"id": "california_mild_zone", "climate": "mild", "avg_temp": 24.0, "humidity": 45.0, "energy_cost_index": 1.2},
        {"id": "virginia_humid_zone", "climate": "temperate", "avg_temp": 28.0, "humidity": 70.0, "energy_cost_index": 0.7},
        {"id": "nevada_desert_zone", "climate": "desert", "avg_temp": 42.0, "humidity": 15.0, "energy_cost_index": 0.6},
        {"id": "newyork_cold_zone", "climate": "cold", "avg_temp": 12.0, "humidity": 55.0, "energy_cost_index": 1.4},
        {"id": "florida_tropical_zone", "climate": "tropical", "avg_temp": 33.0, "humidity": 85.0, "energy_cost_index": 0.9}
    ]

    cooling_systems = [
        {"id": "air_cooling_v1", "type": "air_cooling", "efficiency_score": 0.6},
        {"id": "liquid_cooling_v2", "type": "liquid_immersion", "efficiency_score": 0.95},
        {"id": "free_cooling_v1", "type": "ambient_air", "efficiency_score": 0.85},
        {"id": "evaporative_cooling_v1", "type": "evaporative", "efficiency_score": 0.80}
    ]

    # Generate 50 Random USA Data Centers
    states = ["Texas", "California", "Virginia", "Nevada", "New York", "Florida", "Ohio", "Illinois", "Washington"]
    datacenters = []
    
    for i in range(1, 51):
        state = random.choice(states)
        zone_id = "texas_hot_zone" if state == "Texas" else \
                  "california_mild_zone" if state == "California" else \
                  "nevada_desert_zone" if state == "Nevada" else \
                  "newyork_cold_zone" if state in ["New York", "Ohio", "Illinois"] else \
                  "florida_tropical_zone" if state == "Florida" else "virginia_humid_zone"
                  
        cool_id = random.choice([cs["id"] for cs in cooling_systems])
                  
        dc = {
            "id": f"dc_usa_{i}",
            "name": f"{state} Hub {random.randint(10, 99)}",
            "location": f"{state}, USA",
            "latitude": round(random.uniform(25.0, 48.0), 4),
            "longitude": round(random.uniform(-124.0, -71.0), 4),
            "capacity_mw": round(random.uniform(20.0, 200.0), 1),
            "operational_since": str(random.randint(2010, 2025)),
            "loc_id": zone_id,
            "cool_id": cool_id
        }
        datacenters.append(dc)

    # Insert Base Nodes (Locations & Cooling)
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

    # Insert Data Centers and their loc/cooling relationships
    for dc in datacenters:
        neo4j_client.run_query("""
            MERGE (n:DataCenter {id: $id})
            SET n.name = $name, n.location = $location, n.latitude = $latitude, n.longitude = $longitude, n.capacity_mw = $capacity_mw, n.operational_since = $operational_since
        """, dc)
        
        neo4j_client.run_query("""
            MATCH (d:DataCenter {id: $dc_id}), (loc:Location {id: $loc_id})
            MERGE (d)-[:LOCATED_IN]->(loc)
        """, {"dc_id": dc["id"], "loc_id": dc["loc_id"]})
        
        neo4j_client.run_query("""
            MATCH (d:DataCenter {id: $dc_id}), (cs:CoolingSystem {id: $cool_id})
            MERGE (d)-[:USES_COOLING]->(cs)
        """, {"dc_id": dc["id"], "cool_id": dc["cool_id"]})

    # Group Similar Datacenters
    neo4j_client.run_query("""
        MATCH (dc1:DataCenter)-[:LOCATED_IN]->(l:Location)<-[:LOCATED_IN]-(dc2:DataCenter)
        WHERE id(dc1) > id(dc2)
        MERGE (dc1)-[:SIMILAR_TO {reason: 'same_climate'}]-(dc2)
    """)

    # 4. Generate 1000 Entries (Incidents, Maintenance, Performance)
    print("Injecting 1000 synthetic entries... This may take a minute.")
    incident_types = ['overheating', 'power_surge', 'network_latency', 'cooling_failure', 'cpu_bottleneck', 'high_pue_violation', 'brownout']
    maintenance_types = ['cooling_upgrade', 'server_rack_replacement', 'hvac_calibration', 'power_grid_sync', 'cpu_cluster_upgrade', 'load_balancer_tuning']
    
    
    for i in range(1, 1001):
        target_dc = random.choice(datacenters)
        
        inc_id = f"incident_{i}"
        inc = {
            "id": inc_id,
            "type": random.choice(incident_types),
            "severity": random.choice(["low", "medium", "high", "critical"]),
            "timestamp": (datetime.now() - timedelta(days=random.randint(1, 1500))).strftime("%Y-%m-%d"),
            "duration_minutes": random.randint(15, 240),
            "root_cause": random.choice(["cooling_failure", "grid_instability", "hardware_aging", "high_cpu_spike", "external_grid_failure", "aging_psu", "ambient_weather_anomaly"])
        }
        
        maint_id = f"maintenance_{i}"
        maint_effect = "improved_stability"
        if inc["type"] == "overheating": maint_effect = "reduced_overheating"
        elif inc["type"] == "cpu_bottleneck": maint_effect = "optimized_compute_load"
        elif "power" in inc["type"] or "brownout" in inc["type"]: maint_effect = "stabilized_pue"
        
        maint = {
            "id": maint_id,
            "type": random.choice(maintenance_types),
            "cost_level": random.choice(["low", "medium", "high"]),
            "effect": maint_effect
        }
        
        perf_id = f"perf_{i}"
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

        # Connect Incident to Data Center
        neo4j_client.run_query("""
            MATCH (dc:DataCenter {id: $dc_id}), (inc:Incident {id: $inc_id})
            MERGE (dc)-[:EXPERIENCED {weight: 0.8, timestamp: $timestamp}]->(inc)
        """, {"dc_id": target_dc["id"], "inc_id": inc_id, "timestamp": inc["timestamp"]})
        
        # Incident Caused By Cooling
        neo4j_client.run_query("""
            MATCH (inc:Incident {id: $inc_id}), (cs:CoolingSystem {id: $cs_id})
            MERGE (inc)-[:CAUSED_BY {weight: 0.9, timestamp: $timestamp}]->(cs)
        """, {"inc_id": inc_id, "cs_id": target_dc["cool_id"], "timestamp": inc["timestamp"]})

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
        """, {"dc_id": target_dc["id"], "perf_id": perf_id})

    print("✅ MASSIVE USA-based Synthetic Graph Data successfully populated into Neo4j (Over 3000 nodes)!")

if __name__ == "__main__":
    generate_synthetic_graph_data()
