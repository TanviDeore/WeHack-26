import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBClientWrapper:
    def __init__(self):
        url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        token = os.getenv("INFLUXDB_TOKEN", "my-super-secret-auth-token")
        self.org = os.getenv("INFLUXDB_ORG", "cbre")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "telemetry")
        
        self.client = InfluxDBClient(url=url, token=token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def write_telemetry(self, dc_id: str, temp: float, cpu: float, pue: float, latency: float, event_type: str = None):
        point = Point("datacenter_metrics") \
            .tag("dc_id", dc_id) \
            .field("temperature", temp) \
            .field("cpu_usage", cpu) \
            .field("pue", pue) \
            .field("latency_ms", latency)
            
        if event_type:
            point = point.field("event_type", event_type)
            
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    def query_recent_telemetry(self, dc_id: str, minutes_ago: int = 60):
        # Queries data from the last hour for the specific DC
        query = f'from(bucket:"{self.bucket}") |> range(start: -{minutes_ago}m) |> filter(fn:(r) => r.dc_id == "{dc_id}")'
        result = self.query_api.query(org=self.org, query=query)
        
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value(), record.get_time()))
        return results

influx_client = InfluxDBClientWrapper()
