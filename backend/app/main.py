"""
Batarya telemetri backend API'si.
FastAPI ile hem REST endpoint'leri hem de WebSocket ile canli veri akisi sunar.
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "db"))

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import HTMLResponse

from reader import get_latest_pack_reading, get_pack_history, get_latest_cell_status
from ws_manager import ConnectionManager
from live_simulation import run_live_simulation

manager = ConnectionManager()
simulation_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulation_task
    simulation_task = asyncio.create_task(
        run_live_simulation(manager, pack_id="PACK-1", style_value="normal")
    )
    yield
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Batarya Saglik ve Telemetri API",
    description="Savunma sanayii ve IKA uygulamalari icin batarya izleme sistemi",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Batarya telemetri API calisiyor"}


@app.get("/telemetry/latest")
def telemetry_latest(pack_id: str = Query(..., description="Sorgulanacak pack ID'si, orn. PACK-1")):
    reading = get_latest_pack_reading(pack_id)
    if reading is None:
        raise HTTPException(status_code=404, detail=f"'{pack_id}' icin veri bulunamadi.")
    return reading


@app.get("/telemetry/history")
def telemetry_history(
    pack_id: str = Query(..., description="Sorgulanacak pack ID'si, orn. PACK-1"),
    limit: int = Query(100, ge=1, le=5000, description="Kac satir donsun"),
):
    return get_pack_history(pack_id, limit)

@app.get("/bms/status")
def bms_status(pack_id: str = Query(..., description="Sorgulanacak pack ID'si, orn. PACK-1")):
    reading = get_latest_pack_reading(pack_id)
    if reading is None:
        raise HTTPException(status_code=404, detail=f"'{pack_id}' icin veri bulunamadi.")

    cells = get_latest_cell_status(pack_id)

    return {
        "pack_id": pack_id,
        "time": reading["time"],
        "soh_percent": reading["soh_percent"],
        "thermal_state": reading["thermal_state"],
        "cell_voltage_delta": reading["cell_voltage_delta"],
        "cells": cells,
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


WS_TEST_HTML = """
<!DOCTYPE html>
<html>
<head><title>WebSocket Test</title></head>
<body>
<h2>Canli Batarya Verisi</h2>
<p id="status">Baglaniyor...</p>
<pre id="output"></pre>
<script>
    const wsUrl = "ws://" + window.location.host + "/ws/telemetry";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        document.getElementById("status").textContent = "Baglanti acildi, veri bekleniyor...";
    };
    ws.onerror = (err) => {
        document.getElementById("status").textContent = "HATA: baglanti kurulamadi.";
        console.error("WebSocket hatasi:", err);
    };
    ws.onclose = () => {
        document.getElementById("status").textContent = "Baglanti kapandi.";
    };
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        document.getElementById("status").textContent = "Canli veri aliniyor:";
        document.getElementById("output").textContent =
            `Voltaj: ${data.pack_voltage}V\\nSoC: ${data.pack_soc}\\nSicaklik: ${data.max_temperature_c}C`;
    };
</script>
</body>
</html>
"""


@app.get("/ws-test", response_class=HTMLResponse)
def ws_test_page():
    return WS_TEST_HTML