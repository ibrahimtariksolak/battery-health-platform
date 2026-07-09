"""
Simulator'den gelen batarya verisini TimescaleDB'ye yazan modul.
Performans icin tekil INSERT yerine toplu (batch) INSERT kullanir.
"""

from connection import get_connection


def create_session(pack_id: str, driving_style: str) -> str:
    """Yeni bir suruş oturumu baslatir, session_id doner."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO session (pack_id, driving_style)
        VALUES (%s, %s)
        RETURNING session_id;
        """,
        (pack_id, driving_style),
    )
    session_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return str(session_id)


def end_session(session_id: str):
    """Oturumu bitis zamaniyla kapatir."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE session SET ended_at = now() WHERE session_id = %s;",
        (session_id,),
    )
    conn.commit()
    cur.close()
    conn.close()


def log_batch(session_id: str, pack_rows: list, cell_rows: list):
    """
    Birikmis pack ve cell okumalarini tek seferde veritabanina yazar.
    pack_rows: (time, pack_id, pack_voltage, pack_soc, max_temp, cell_delta) listesi
    cell_rows: (time, cell_id, soc, voltage, temp, balancing_active) listesi
    """
    conn = get_connection()
    cur = conn.cursor()

    if pack_rows:
        cur.executemany(
            """
            INSERT INTO pack_reading
                (time, session_id, pack_id, pack_voltage, pack_soc,
                 max_temperature_c, cell_voltage_delta)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            [(t, session_id, pid, v, soc, temp, delta) for
             (t, pid, v, soc, temp, delta) in pack_rows],
        )

    if cell_rows:
        cur.executemany(
            """
            INSERT INTO cell_reading
                (time, session_id, cell_id, soc, voltage,
                 temperature_c, balancing_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            [(t, session_id, cid, soc, v, temp, bal) for
             (t, cid, soc, v, temp, bal) in cell_rows],
        )

    conn.commit()
    cur.close()
    conn.close()