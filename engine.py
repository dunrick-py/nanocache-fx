import time
import requests

class NanoCacheEngine:
    def __init__(self, expiry_seconds=0.5):
        self.cache = {}
        self.expiry_seconds = expiry_seconds
        # Using a reliable free exchange rate API endpoint
        self.api_url = "https://open.er-api.com/v6/latest/USD"

    def fetch_live_rates(self):
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:  # Fixed: Clean response checking
                return response.json().get("rates", {})
        except Exception as e:
            print(f"⚠️ Network error fetching rates: {e}")
        return {}

    def get_rate(self, currency):
        currency = currency.upper()
        now = time.time()

        # Check if we have a fresh hit in RAM
        if currency in self.cache:
            data, timestamp = self.cache[currency]
            if now - timestamp < self.expiry_seconds:
                return data, "HIT"

        # Cache Miss: Fetch fresh data from the global pipeline
        live_rates = self.fetch_live_rates()
        if currency in live_rates:
            rate = live_rates[currency]
            self.cache[currency] = (rate, now)
            return rate, "MISS"
        
        return 1.0, "MISS"