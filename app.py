import functools
import os
import random
import time
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, disconnect, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "nanocache-secret-key")

# 1. Setup Rate Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

socketio = SocketIO(
    app, cors_allowed_origins="*", async_mode="threading", ping_timeout=10
)

# 2. Approved API Keys
VALID_API_KEYS = {
    "nc_live_8f91a2b3c4d5": "free_tier",
    "nc_live_99x88y77z66w": "pro_tier",
}


def require_api_key(f):

  @functools.wraps(f)
  def decorated_function(*args, **kwargs):
    api_key = request.headers.get("X-API-KEY") or request.args.get("api_key")
    if not api_key or api_key not in VALID_API_KEYS:
      return (
          jsonify({
              "error": "Unauthorized",
              "message": "Invalid or missing X-API-KEY header",
          }),
          401,
      )
    return f(*args, **kwargs)

  return decorated_function


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/health", methods=["GET"])
@limiter.limit("10 per minute")
def health():
  return jsonify({"status": "ONLINE", "engine": "nanocache-fx"}), 200


@socketio.on("connect")
def handle_connect(auth):
  api_key = None
  if isinstance(auth, dict):
    api_key = auth.get("api_key")

  # Reject invalid or missing keys
  if not api_key or api_key not in VALID_API_KEYS:
    print(f"[AUTH REJECTED] Bad Key: {api_key}")
    disconnect()
    return False

  tier = VALID_API_KEYS[api_key]
  print(f"[AUTH SUCCESS] Connected: {tier}")
  emit("connection_response", {"status": "CONNECTED", "tier": tier})


# --- Background Thread Stream Matched to Your Dashboard ---
def background_tick_stream():
  pairs = [
      {"currency": "EUR", "base_rate": 1.0850},
      {"currency": "GBP", "base_rate": 1.2720},
      {"currency": "UGX", "base_rate": 3710.00},
      {"currency": "JPY", "base_rate": 155.40},
  ]

  while True:
    time.sleep(0.5)  # 500ms refresh
    for item in pairs:
      # Fluctuate price slightly
      variation = (random.random() - 0.5) * (
          10.0 if item["currency"] == "UGX" else 0.002
      )
      current_rate = item["base_rate"] + variation
      is_hit = random.choice(["HIT", "HIT", "HIT", "MISS"])

      payload = {
          "currency": item["currency"],
          "rate": current_rate,
          "status": is_hit,
          "timestamp": time.strftime("%H:%M:%S"),
      }

      # Broadcast directly to dashboard listener 'ticker_update'
      socketio.emit("ticker_update", payload)


socketio.start_background_task(target=background_tick_stream)
# --- API Endpoint for Ticks ---
@app.route('/api/v1/ticks', methods=['GET'])
def get_ticks():
  api_key = request.headers.get('X-API-KEY') or request.args.get('api_key')

  # Check if key is provided and valid
  if not api_key or api_key != 'nc_live_8f91a2b3c4d5':
    return (
        jsonify({
            'error': 'Unauthorized',
            'message': 'Invalid or missing X-API-KEY header',
        }),
        401,
    )

  return (
      jsonify({
          'pair': 'EUR/USD',
          'bid': 1.0852,
          'ask': 1.0855,
          'status': 'CACHE_HIT',
      }),
      200,
  )
if __name__ == "__main__":
  socketio.run(app, debug=True, port=10000)