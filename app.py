from flask import Flask, render_template, jsonify
from nanocache_fx.engine import NanoCacheEngine

app = Flask(__name__)

# Initialize our custom caching architecture (10-second window)
cache_system = NanoCacheEngine(expiry_seconds=10)

@app.route('/')
def index():
    return render_template('dashboard.html')

# We changed this path to match your dashboard's JavaScript fetch target!
@app.route('/api/v1/rate')
def get_default_rate():
    # We default to fetching 'EUR' or whatever currency your dashboard defaults to
    rate, status = cache_system.get_rate("EUR")
    return jsonify({
        "currency": "EUR",
        "rate": rate,
        "status": status
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)