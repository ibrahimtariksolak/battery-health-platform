"""
Batarya telemetri backend API'si.
FastAPI ile REST endpoint'leri sunar; ileride WebSocket ile canli akis eklenecek.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "db"))
from reader import get_latest_pack_reading, get_pack_history

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(
    title="Batarya Saglik ve Telemetri API",
    description="Savunma sanayii ve IKA uygulamalari icin batarya izleme sistemi",
    version="0.1.0",
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