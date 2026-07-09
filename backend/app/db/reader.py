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
               max_temperature_c, cell_voltage_delta,
               soh_percent, thermal_state
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
        "soh_percent": row[6],
        "thermal_state": row[7],
    }


def get_pack_history(pack_id: str, limit: int = 100) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT time, pack_id, pack_voltage, pack_soc,
               max_temperature_c, cell_voltage_delta,
               soh_percent, thermal_state
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
            "soh_percent": r[6],
            "thermal_state": r[7],
        }
        for r in rows
    ]


def get_latest_cell_status(pack_id: str) -> list:
    """
    Belirli bir pack'in en son zaman damgasindaki tum hucrelerinin
    durumunu (SoC, voltaj, sicaklik, dengeleme aktif mi) doner.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        WITH latest_time AS (
            SELECT MAX(cr.time) AS t
            FROM cell_reading cr
            JOIN session s ON cr.session_id = s.session_id
            WHERE s.pack_id = %s
        )
        SELECT cr.cell_id, cr.soc, cr.voltage, cr.temperature_c, cr.balancing_active
        FROM cell_reading cr
        JOIN session s ON cr.session_id = s.session_id
        CROSS JOIN latest_time
        WHERE s.pack_id = %s AND cr.time = latest_time.t
        ORDER BY cr.cell_id;
        """,
        (pack_id, pack_id),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "cell_id": r[0],
            "soc": r[1],
            "voltage": r[2],
            "temperature_c": r[3],
            "balancing_active": r[4],
        }
        for r in rows
    ]
def get_latest_session_id(pack_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT session_id FROM session
        WHERE pack_id = %s
        ORDER BY started_at DESC
        LIMIT 1;
        """,
        (pack_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return str(row[0]) if row else None


def get_session_current_temp_series(session_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT current_a, max_temperature_c
        FROM pack_reading
        WHERE session_id = %s AND current_a IS NOT NULL
        ORDER BY time ASC;
        """,
        (session_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    currents = [r[0] for r in rows]
    temps = [r[1] for r in rows]
    return currents, temps