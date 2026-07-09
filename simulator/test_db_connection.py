"""
Sadece veritabani baglantisinin calistigini dogrulamak icin.
Herhangi bir veri yazmaz/silmez.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "db"))
from connection import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print("[OK] Baglanti basarili.")
    print("PostgreSQL versiyonu:", version[0])
    cur.close()
    conn.close()
except Exception as e:
    print("[HATA] Baglanti kurulamadi:", e)