import functools
import json
import os
import random
import time
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, disconnect, emit
import redis

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "nanocache-secret-key")

# --- Redis Connection & Fallback ---
REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL:
  redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
  limiter_storage = REDIS_URL
  print("[SYSTEM] Connected to Redis Cache Engine")
else:
  redis_client = None
  limiter_storage = "memory://"
  print("[SYSTEM] REDIS_URL not set — Using in-memory fallback")

# --- Rate Limiter ---
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=limiter_storage,
)

# --- WebSockets Setup ---
socketio = SocketIO(
    app, cors_allowed_origins="*", async_mode="threading", ping_timeout=10
)

# --- Approved API Keys ---
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


bg_task_started = False


def background_tick_stream():
  """Generates mock FX ticks for 6 majors + UGX, caches to Redis, and broadcasts live."""
  currencies = ["EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "UGX"]

  while True:
    socketio.sleep(1.0)
    curr = random.choice(currencies)

    # Realistic rate ranges
    if curr == "EUR":
      rate = round(random.uniform(1.0800, 1.0900), 4)
    elif curr == "GBP":
      rate = round(random.uniform(1.2650, 1.2780), 4)
    elif curr == "JPY":
      rate = round(random.uniform(154.50, 156.20), 2)
    elif curr == "AUD":
      rate = round(random.uniform(0.6600, 0.6720), 4)
    elif curr == "CAD":
      rate = round(random.uniform(1.3580, 1.3700), 4)
    elif curr == "CHF":
      rate = round(random.uniform(0.8880, 0.9020), 4)
    elif curr == "UGX":
      rate = round(random.uniform(3690.00, 3730.00), 2)

    is_hit = random.choice(["HIT", "HIT", "HIT", "MISS"])

    payload = {
        "currency": curr,
        "rate": str(rate),
        "status": is_hit,
        "timestamp": time.strftime("%H:%M:%S"),
    }

    # 1. Store in Redis Cache with a 10-second TTL
    if redis_client:
      try:
        redis_client.set(f"tick:{curr}", json.dumps(payload), ex=10)
      except Exception as e:
        print(f"[REDIS ERROR] {e}")

    # 2. Emit tick via SocketIO
    socketio.emit("fx_tick", payload)


# --- Routes ---
@app.route("/")
def index():
  try:
    return render_template("index.html")
  except Exception:
    return (
        jsonify({
            "service": "nanocache-fx",
            "status": "ONLINE",
            "routes": ["/health", "/api/v1/ticks"],
        }),
        200,
    )


@app.route("/health", methods=["GET"])
@limiter.limit("10 per minute")
def health():
  redis_status = "OFFLINE"
  if redis_client:
    try:
      if redis_client.ping():
        redis_status = "ONLINE"
    except Exception:
      redis_status = "ERROR"

  return (
      jsonify({
          "status": "ONLINE",
          "engine": "nanocache-fx",
          "redis_cache": redis_status,
      }),
      200,
  )


@app.route("/api/v1/ticks", methods=["GET"])
@require_api_key
@limiter.limit("30 per minute")
def get_ticks():
  pair = request.args.get("currency", "EUR").upper()

  # Serve directly from Redis cache if hit
  if redis_client:
    cached_data = redis_client.get(f"tick:{pair}")
    if cached_data:
      tick = json.loads(cached_data)
      tick["cache_source"] = "REDIS_CACHE_HIT"
      return jsonify(tick), 200

  # Memory fallback
  return (
      jsonify({
          "currency": pair,
          "rate": "1.0852",
          "status": "CACHE_MISS",
          "cache_source": "FALLBACK_MEMORY",
      }),
      200,
  )


@socketio.on("connect")
def handle_connect(auth):
  global bg_task_started
  api_key = None
  if isinstance(auth, dict):
    api_key = auth.get("api_key")

  if not api_key or api_key not in VALID_API_KEYS:
    print(f"[AUTH REJECTED] Bad Key: {api_key}")
    disconnect()
    return False

  tier = VALID_API_KEYS[api_key]
  print(f"[AUTH SUCCESS] Connected: {tier}")
  emit("connection_response", {"status": "CONNECTED", "tier": tier})

  if not bg_task_started:
    socketio.start_background_task(target=background_tick_stream)
    bg_task_started = True


if __name__ == "__main__":
  socketio.run(app, debug=True, port=10000)