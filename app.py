from flask import Flask, jsonify, render_template
# IMPORTING YOUR OWN CREATION!
from nanocache_fx.engine import ForexCacheEngine

app = Flask(__name__)

# Initialize your library engine
fx_engine = ForexCacheEngine(cache_duration=10)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/v1/rate')
def get_rate():
    # Calling your library method
    result = fx_engine.get_rate()
    return jsonify({
        "status": "success",
        "execution_mode": result["execution_mode"],
        "data": {
            "pair": "USD/UGX",
            "rate": result["rate"],
            "ttl_seconds": result["ttl"]
        }
    })

@app.route('/api/v1/metrics')
def get_metrics():
    # Calling your library telemetry method
    metrics = fx_engine.get_telemetry()
    return jsonify({
        "total_requests": metrics["total_requests"],
        "cache_hits": metrics["cache_hits"],
        "hit_ratio": metrics["hit_ratio"],
        "money_saved_usd": metrics["money_saved_usd"],
        "server_status": "OPERATIONAL"
    })

if __name__ == '__main__':
    app.run(debug=True)