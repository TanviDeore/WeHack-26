import time
import random
import os
import redis

def simulate_realtime_data():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    r = redis.Redis(host=host, port=port, db=0, decode_responses=True)
    
    print("🚀 Starting Reactive Live Redis Log Simulator...")
    print("Press Ctrl+C to stop.")
    
    datacenters = [f"dc_usa_{i}" for i in range(1, 51)]
    
    try:
        while True:
            # Check for focused data center from the frontend
            active_dc = r.get("active_dc")
            if active_dc:
                print(f"🎯 Simulation focused on: {active_dc}")
                if active_dc not in datacenters:
                    datacenters.append(active_dc) # Ensure it gets data
            
            for dc in datacenters:
                # 1. Base metrics (Normal Operation)
                # If active_dc is set, give it a 30% chance of an incident every loop
                # Others have a very small random chance
                is_active = (dc == active_dc)
                
                if is_active:
                    # Focused DC has high probability of being 'interesting'
                    is_incident = random.random() > 0.7 
                else:
                    # Background DCs rarely have incidents
                    is_incident = random.random() > 0.98
                
                status = "degraded" if is_incident else "optimal"
                temp = random.randint(85, 105) if is_incident else random.randint(65, 75)
                cpu_load = random.randint(85, 99) if is_incident else random.randint(30, 60)
                power_usage = random.randint(75, 95) if is_incident else random.randint(40, 60)
                latency = random.randint(100, 250) if is_incident else random.randint(15, 30)
                
                # Additional rich fields for incident context
                fan_speed_rpm = random.randint(8000, 12000) if is_incident else random.randint(4000, 6000)
                coolant_temp_out = temp - random.randint(2, 5) if is_incident else temp - 15
                power_draw_kw = power_usage * random.randint(10, 15)
                network_bandwidth_gbps = random.uniform(8.0, 10.0) if is_incident else random.uniform(2.0, 5.0)
                coolant_temp_out = (temp + random.randint(30, 50)) if is_incident else (temp + 15)

                # 2. Write to flat Redis Keys
                r.set(f"dc:{dc}:status", status)
                r.set(f"dc:{dc}:temp", temp)
                r.set(f"dc:{dc}:cpu_load", cpu_load)
                r.set(f"dc:{dc}:power_usage", power_usage)
                r.set(f"dc:{dc}:latency", latency)
                r.set(f"dc:{dc}:fan_speed_rpm", fan_speed_rpm)
                r.set(f"dc:{dc}:coolant_temp_out", coolant_temp_out)
                r.set(f"dc:{dc}:power_draw_kw", power_draw_kw)
                r.set(f"dc:{dc}:network_bandwidth_gbps", round(network_bandwidth_gbps, 2))

                # 3. Handle Active Alerts
                if is_incident:
                    r.set(f"alert:{dc}", "CRITICAL: Cooling stress detected. Immediate mitigation required.")
                    r.lpush(f"recent:event:{dc}", f"TEMP_SPIKE: {temp}F at {time.strftime('%H:%M:%S')}")
                    r.ltrim(f"recent:event:{dc}", 0, 99) # Keep last 100
                else:
                    r.delete(f"alert:{dc}") # Clear alert if normal

            # Send data every 3 seconds
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n🛑 Live log simulator stopped.")

if __name__ == "__main__":
    simulate_realtime_data()
