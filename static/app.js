// static/app.js - Handles WebSockets and UI Updates

// 1. Initialize WebSocket connection automatically on page load
const socket = io({
  auth: {
    api_key: 'nc_live_8f91a2b3c4d5' // Passing our valid API Key
  }
});

// 2. Listen for connection authorization
socket.on('connection_response', (data) => {
  console.log('[NanoCache Engine] Connected:', data);
  const statusBadge = document.getElementById('status-badge');
  if (statusBadge) {
    statusBadge.textContent = `LIVE (${data.tier.toUpperCase()})`;
    statusBadge.style.backgroundColor = '#16a34a'; // Green
  }
});

// 3. Listen for incoming price ticks from Python
socket.on('tick', (data) => {
  const pairElem = document.getElementById('currency-pair');
  const priceElem = document.getElementById('live-price');
  const latencyElem = document.getElementById('system-latency');

  if (pairElem) pairElem.textContent = data.pair;
  if (priceElem) priceElem.textContent = data.rate.toFixed(4);

  // Calculate live end-to-end latency in milliseconds
  if (data.server_ts_ms && latencyElem) {
    const latency = Date.now() - data.server_ts_ms;
    latencyElem.textContent = `${latency} ms`;
  }
});

// 4. Handle Disconnection / Auth Failures
socket.on('disconnect', () => {
  console.warn('[NanoCache Engine] Disconnected or Key Invalid.');
  const statusBadge = document.getElementById('status-badge');
  if (statusBadge) {
    statusBadge.textContent = 'DISCONNECTED / AUTH ERROR';
    statusBadge.style.backgroundColor = '#dc2626'; // Red
  }
});