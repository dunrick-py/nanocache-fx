import time
import random

class ForexCacheEngine:
    def __init__(self, cache_duration=10):
        self.cache_duration = cache_duration
        self.cached_rate = None
        self.last_updated_time = 0
        self.total_requests = 0
        self.cache_hits = 0
        self.money_saved = 0.0

    def _fetch_live_rate(self):
        """Simulates a secure, high-cost connection to a liquidity provider."""
        time.sleep(0.4) 
        return round(random.uniform(3745.00, 3755.00), 2)

    def get_rate(self):
        """Handles the whiteboard logic automatically."""
        current_time = time.time()
        self.total_requests += 1
        
        time_elapsed = current_time - self.last_updated_time
        is_valid = self.cached_rate and (time_elapsed < self.cache_duration)
        
        if is_valid:
            self.cache_hits += 1
            self.money_saved = round(self.cache_hits * 0.02, 2)
            return {
                "execution_mode": "CACHE_HIT",
                "rate": self.cached_rate,
                "ttl": round(self.cache_duration - time_elapsed, 1)
            }
            
        # Cache Miss
        self.cached_rate = self._fetch_live_rate()
        self.last_updated_time = current_time
        return {
            "execution_mode": "CACHE_MISS_API_REFRESH",
            "rate": self.cached_rate,
            "ttl": self.cache_duration
        }

    def get_telemetry(self):
        """Returns performance metrics for dashboards."""
        total = self.total_requests
        ratio = round((self.cache_hits / total) * 100, 1) if total > 0 else 0
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "hit_ratio": f"{ratio}%",
            "money_saved_usd": f"${self.money_saved:.2f}"
        }