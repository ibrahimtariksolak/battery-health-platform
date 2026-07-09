"""
Batarya simulasyonunu calistirir ve sonuclari TimescaleDB'ye yazar.
test_run.py'den farki: konsola yazdirmak yerine gercek veritabanina loglar.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "db"))
from writer import create_session, end_session, log_batch

from battery_simulator import BatteryPack
from driving_profile import generate_current_profile, DrivingStyle

DT_SECONDS = 1.0
DURATION_SECONDS = 600      # 10 dakikalik oturum
LOG_EVERY_N_STEPS = 1       # her adimda logla (istenirse 5 yapip veri hacmini azaltabiliriz


def run_and_log(pack_id: str, style: DrivingStyle, seed: int = 42):
    session_id = create_session(pack_id=pack_id, driving_style=style.value)
    print(f"[BASLADI] session_id={session_id}  stil={style.value}")

    pack = BatteryPack.create(pack_id=pack_id, cell_count=8, seed=seed)
    profile = generate_current_profile(DURATION_SECONDS, style=style, seed=seed)

    start_time = datetime.now(timezone.utc)
    pack_rows = []
    cell_rows = []

    for i, current in enumerate(profile):
        pack.step(current_a=current, dt_seconds=DT_SECONDS)
        current_time = start_time + timedelta(seconds=i)

        if i % LOG_EVERY_N_STEPS == 0:
            pack_rows.append((
                current_time, pack.pack_id, pack.pack_voltage,
                pack.pack_soc, pack.max_temperature, pack.cell_voltage_delta,
            ))
            for cell in pack.cells:
                cell_rows.append((
                    current_time, cell.cell_id, cell.soc,
                    cell.voltage, cell.temperature_c, cell.balancing_active,
                ))

    log_batch(session_id, pack_rows, cell_rows)
    end_session(session_id)

    print(f"[BITTI]   {len(pack_rows)} pack satiri, {len(cell_rows)} cell satiri yazildi.")
    print(f"          Son durum -> SoC: {pack.pack_soc:.4f}  MaxSicaklik: {pack.max_temperature}C")
    return session_id


if __name__ == "__main__":
    run_and_log(pack_id="PACK-1", style=DrivingStyle.AGGRESSIVE)