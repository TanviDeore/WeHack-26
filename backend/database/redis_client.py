import os
import redis
import json

class RedisClient:
    def __init__(self):
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        self.r = redis.Redis(host=host, port=port, db=0, decode_responses=True)

    def set_state(self, key: str, value: dict):
        self.r.set(key, json.dumps(value))

    def get_state(self, key: str):
        val = self.r.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        return None

    def push_event(self, q_key: str, event: str):
        self.r.lpush(q_key, event)
        self.r.ltrim(q_key, 0, 99) # keep last 100 events

    def get_recent_events(self, q_key: str):
        return self.r.lrange(q_key, 0, -1)
        
redis_client = RedisClient()
