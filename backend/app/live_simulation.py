"""
Arka planda surekli calisan batarya simulasyonu.
Her adimda: 1) pack fizigini ilerletir 2) WebSocket ile canli yayinlar
3) belirli araliklarla veritabanina toplu yazar.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "simulator"))
sys.path.append(os.path.join(os.path.dirname(__file__), "db"))

from battery_simulator import BatteryPack
from driving_profile import generate_current_profile, DrivingStyle
from writer import create_session, end_session, log_batch

DT_SECONDS = 1.0
DB_FLUSH_EVERY_N_STEPS = 5   # her 5 adimda bir veritabanina toplu yaz


async def run_live_simulation(manager, pack_id: str = "PACK-1", style_value: str = "normal"):
    """
    Sonsuz dongude calisir: simulasyonu ilerletir, WebSocket'e yayinlar,
    periyodik olarak veritabanina yazar. Uygulama calistigi surece devam eder.
    """
    style = DrivingStyle(style_value)
    session_id = create_session(pack_id=pack_id, driving_style=style.value)
    print(f"[LIVE] Oturum baslatildi: {session_id}")

    pack = BatteryPack.create(pack_id=pack_id, cell_count=8)
    pack_rows = []
    cell_rows = []
    step = 0
    profile_iter = iter([])

    try:
        while True:
            try:
                current = next(profile_iter)
            except StopIteration:
                profile_chunk = generate_current_profile(30, style=style)
                profile_iter = iter(profile_chunk)
                current = next(profile_iter)

            pack.step(current_a=current, dt_seconds=DT_SECONDS)
            now = datetime.now(timezone.utc)

            reading = pack.to_dict()
            await manager.broadcast(reading)

            pack_rows.append((now, pack.pack_id, pack.pack_voltage, pack.pack_soc,
                              pack.max_temperature, pack.cell_voltage_delta,
                              pack.soh_estimator.soh_percent,
                              pack.thermal_protection.state.value))
            for cell in pack.cells:
                cell_rows.append((now, cell.cell_id, cell.soc, cell.voltage,
                                   cell.temperature_c, cell.balancing_active))

            step += 1
            if step % DB_FLUSH_EVERY_N_STEPS == 0:
                log_batch(session_id, pack_rows, cell_rows)
                pack_rows, cell_rows = [], []

            await asyncio.sleep(DT_SECONDS)

    except asyncio.CancelledError:
        if pack_rows or cell_rows:
            log_batch(session_id, pack_rows, cell_rows)
        end_session(session_id)
        print(f"[LIVE] Oturum kapatildi: {session_id}")
        raise