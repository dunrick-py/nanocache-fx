import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from engine import NanoCacheEngine  # Fixed: Points directly to your root engine.py file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'prop-desk-secret-key'
# Allow cross-origin requests for scaling frontend servers later
socketio = SocketIO(app, cors_allowed_origins="*")

# 500 millisecond expiry threshold for high-frequency precision
cache_system = NanoCacheEngine(expiry_seconds=0.5)

# Track active connections so we don't stream to empty rooms
active_traders = 0
streaming_thread = None
thread_lock = threading.Lock()

def market_data_stream():
    """Background thread that aggregates and pumps real-time price feeds."""
    global active_traders
    monitored_pairs = ['EUR', 'GBP', 'UGX', 'JPY']
    
    while active_traders > 0:
        for currency in monitored_pairs:
            rate, status = cache_system.get_rate(currency)
            
            # Broadcast instantly to all connected terminal screens
            socketio.emit('ticker_update', {
                "currency": currency.upper(),
                "rate": rate,
                "status": status,
                "timestamp": time.strftime('%H:%M:%S')
            })
        time.sleep(0.5) # 500ms heartbeat clock tick

@app.route('/')
def trading_floor():
    return render_template('dashboard.html')

@socketio.on('connect')
def handle_connect():
    global active_traders, streaming_thread
    with thread_lock:
        active_traders += 1
        print(f"📡 Trader Connected. Active Terminals: {active_traders}")
        if streaming_thread is None:
            streaming_thread = socketio.start_background_task(target=market_data_stream)

@socketio.on('disconnect')
def handle_disconnect():
    global active_traders
    with thread_lock:
        if active_traders > 0:
            active_traders -= 1
        print(f"🔌 Trader Disconnected. Active Terminals: {active_traders}")

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)