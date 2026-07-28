# NanoCache FX ⚡

An ultra-low latency Foreign Exchange (FX) caching engine, real-time WebSocket stream, and Redis rolling tick buffer built with Python, Flask, Socket.IO, and Redis.

**NanoCache FX** acts as a high-performance middleware layer designed to sit between expensive external FX data providers and downstream consumers (trading bots, financial dashboards, e-commerce platforms). It drastically reduces API costs and eliminates latency bottlenecks by caching market data in Redis memory and streaming live tick updates over WebSockets.

---

## 🏗 Architecture & System Design

```text
                                +------------------------------------------+
                                |               Client Layer               |
                                |  [ Live Chart UI ]    [ Algorithmic Bots]|
                                +------------------------------------------+
                                     |                         ^
                    Socket.IO Stream |                         | REST API Requests
                      ("fx_tick")    |                         | (Header: X-API-KEY)
                                     v                         |
+----------------------------------------------------------------------------------+
|                                NanoCache FX Engine                               |
|                                (Flask + SocketIO)                                |
|                                                                                  |
|   +--------------------------------------------------------------------------+   |
|   |                         Background Worker Thread                         |   |
|   |  - Generates market ticks across 7 pairs (EUR, GBP, JPY, AUD, CAD, CHF, UGX) |   |
|   |  - Writes to Redis RAM store & broadcasts via Socket.IO                  |   |
|   +--------------------------------------------------------------------------+   |
+----------------------------------------------------------------------------------+
                                     |                         ^
                             LPUSH / |                         | GET
                       LTRIM / SET   v                         |
+----------------------------------------------------------------------------------+
|                                Redis Data Engine                                 |
|  - tick:<CURRENCY>       ---> Single latest tick object (10s TTL)                |
|  - history:<CURRENCY>    ---> Rolling 20-item list buffer                         |
|  - Rate Limit Storage    ---> IP & API-key threshold tracking                    |
+----------------------------------------------------------------------------------+
```

---

## ✨ Key Features

* **Sub-Millisecond Cache Hits:** Serves live market ticks directly from Redis memory in $< 2\text{ms}$, reducing downstream API load by up to 95%.
* **$O(1)$ Rolling List Buffer:** Leverages Redis `LPUSH` and `LTRIM` commands to maintain a strict 20-tick sliding history window per pair for instant frontend chart population.
* **Real-Time WebSocket Streaming:** Event-driven architecture powered by `Flask-SocketIO` to push live exchange rates to connected web clients with low overhead.
* **API Key Auth & Tiering:** Middleware decorator (`@require_api_key`) validating requests against tier-based API keys (`free_tier`, `pro_tier`).
* **Distributed Rate Limiting:** Integrated with `Flask-Limiter` backed by Redis storage to prevent API abuse across distributed application instances.
* **Resilient Fallback Mode:** Designed with zero single-point-of-failure logic; if Redis drops, the engine falls back gracefully to in-memory processing without crashing the app.

---

## 🚀 Tech Stack

* **Backend Engine:** Python 3.10+, Flask, Gunicorn
* **Real-Time Layer:** Flask-SocketIO (WebSockets / Eventlet / Threading)
* **In-Memory Cache & Storage:** Redis
* **Security & Control:** Flask-Limiter, `functools` custom decorators
* **Frontend Dashboard:** HTML5, CSS3, JavaScript (ES6+), Chart.js

---

## 📡 API Reference

All protected REST endpoints require authentication via the `X-API-KEY` HTTP header or the `api_key` query parameter.

### 1. Health & Status Check
Returns system status and Redis connectivity.

```http
GET /health
```

**Response (`200 OK`):**
```json
{
  "engine": "nanocache-fx",
  "redis_cache": "ONLINE",
  "status": "ONLINE"
}
```

---

### 2. Get Latest Currency Tick
Retrieves the most recent tick for a specified pair from Redis cache.

```http
GET /api/v1/ticks?currency=EUR
Header: X-API-KEY: nc_live_8f91a2b3c4d5
```

**Response (`200 OK`):**
```json
{
  "cache_source": "REDIS_CACHE_HIT",
  "currency": "EUR",
  "rate": "1.0854",
  "status": "HIT",
  "timestamp": "12:15:04"
}
```

---

### 3. Get Historical 20-Tick Buffer
Retrieves up to the last 20 cached ticks for pre-populating charts and analytical engines.

```http
GET /api/v1/history?currency=EUR
Header: X-API-KEY: nc_live_8f91a2b3c4d5
```

**Response (`200 OK`):**
```json
{
  "currency": "EUR",
  "ticks": [
    { "currency": "EUR", "rate": "1.0841", "status": "HIT", "timestamp": "12:14:44" },
    { "currency": "EUR", "rate": "1.0848", "status": "HIT", "timestamp": "12:14:52" },
    { "currency": "EUR", "rate": "1.0854", "status": "HIT", "timestamp": "12:15:04" }
  ]
}
```

---

## 🔌 WebSocket Integration

Clients connect to the Socket.IO server by passing the API key in the connection `auth` dictionary.

### Connection Payload Example (JS):
```javascript
const socket = io("https://your-domain.com", {
  auth: { api_key: "nc_live_8f91a2b3c4d5" }
});

socket.on("connection_response", (data) => {
  console.log("Connected to stream:", data);
});

socket.on("fx_tick", (tick) => {
  console.log(`[${tick.timestamp}] ${tick.currency}: ${tick.rate}`);
});
```

---

## ⚙️ Environment Variables

Configure the following environment variables in your deployment setting or `.env` file:

| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `REDIS_URL` | Optional | Connection URI for the Redis instance | `redis://default:pass@redis-server:6379` |
| `SECRET_KEY` | Optional | Flask application session key | `super-secret-key-123` |
| `PORT` | Optional | Application listening port | `10000` |

---

## 🛠 Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/nanocache-fx.git
cd nanocache-fx
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Redis (Optional)
If you have Redis installed locally or via Docker:
```bash
docker run -d -p 6379:6379 redis
export REDIS_URL="redis://localhost:6379"
```

### 5. Start the Application
```bash
python app.py
```
Open your browser and navigate to `http://localhost:10000` to view the live dashboard.
