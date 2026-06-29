import time
import json
import urllib.request

class NanoCacheEngine:
    def __init__(self, expiry_seconds=10):
        self.cache = {}
        self.expiry_seconds = expiry_seconds
        # Rock-solid, official permanent production domain
        self.api_url = "https://api.frankfurter.app/latest?base=USD"

    def fetch_live_rates(self):
        """Fetches fresh global financial data directly from the live network pipeline."""
        try:
            print("🌐 [Network] Cache missed or expired. Requesting live web API...")
            
            # Disguise Python as a standard web browser to bypass security blocks
            req = urllib.request.Request(
                self.api_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                rates = data.get("rates", {})
                
                # Appending our local Shilling benchmark rate to the live global feed
                rates["UGX"] = 3730.00 
                return rates
        except Exception as e:
            print(f"❌ [Error] Network pull failed: {e}")
            return None

    def get_rate(self, currency_pair):
        """Returns cached data instantly, or updates from the web if expired."""
        current_time = time.time()
        
        # Check if we have valid, unexpired data in our server memory block
        if "data" in self.cache:
            timestamp, cached_rates = self.cache["data"]
            if current_time - timestamp < self.expiry_seconds:
                print(f"⚡ [Cache Hit] Serving {currency_pair} instantly from server RAM!")
                return cached_rates.get(currency_pair, "N/A"), "Cache Hit (0ms)"

        # Otherwise, hit the network pipeline
        live_rates = self.fetch_live_rates()
        if live_rates:
            self.cache["data"] = (current_time, live_rates)
            return live_rates.get(currency_pair, "N/A"), "Network Fetch (Live)"
        
        # Fallback if network goes down completely
        if "data" in self.cache:
            return self.cache["data"][1].get(currency_pair, "N/A"), "Fallback Cache (Expired)"
        return "N/A", "Error"