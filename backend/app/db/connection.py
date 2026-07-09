"""
TimescaleDB baglantisini yoneten merkezi modul.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL ortam degiskeni bulunamadi. "
        "Proje kok klasorunde bir .env dosyasi olusturup "
        "DATABASE_URL=postgresql://... satirini eklediginden emin ol."
    )


def get_connection():
    """Her cagrildiginda yeni bir veritabani baglantisi acar."""
    return psycopg2.connect(DATABASE_URL)