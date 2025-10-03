import redis
import json
from typing import Optional

class Cache:
    def __init__(self, host="localhost", port=6379, db=0, ttl=300):
        self.ttl = ttl
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def set(self, key: str, value: dict):
        """Store value in cache with TTL"""
        self.client.setex(key, self.ttl, json.dumps(value))

    def get(self, key: str) -> Optional[dict]:
        """Retrieve value from cache"""
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def invalidate(self, key: str):
        """Remove cache entry"""
        self.client.delete(key)
