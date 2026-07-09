"""
TimescaleDB'den okuma yapan sorgu katmani.
"""

from typing import Optional
from connection import get_connection


def get_latest_pack_reading(pack_id: str) -> Optional[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT time, pack_id, pack_voltage, pack_soc,
               max_temperature_c, cell_voltage_delta
        FROM pack_reading
        WHERE pack_id = %s
        ORDER BY time DESC
        LIMIT 1;
        """,
        (pack_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return None

    return {
        "time": row[0].isoformat(),
        "pack_id": row[1],
        "pack_voltage": row[2],
        "pack_soc": row[3],
        "max_temperature_c": row[4],
        "cell_voltage_delta": row[5],
    }


def get_pack_history(pack_id: str, limit: int = 100) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT time, pack_id, pack_voltage, pack_soc,
               max_temperature_c, cell_voltage_delta
        FROM pack_reading
        WHERE pack_id = %s
        ORDER BY time DESC
        LIMIT %s;
        """,
        (pack_id, limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "time": r[0].isoformat(),
            "pack_id": r[1],
            "pack_voltage": r[2],
            "pack_soc": r[3],
            "max_temperature_c": r[4],
            "cell_voltage_delta": r[5],
        }
        for r in rows
    ]