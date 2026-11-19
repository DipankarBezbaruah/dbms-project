import os
import ssl
from dotenv import load_dotenv

load_dotenv()


class Config:
    _raw_uri = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost/hostelout",
    )

    _is_postgres = _raw_uri.startswith("postgres://") or _raw_uri.startswith("postgresql://")

    # Fix driver prefix for Render PostgreSQL
    if _raw_uri.startswith("postgres://"):
        _raw_uri = _raw_uri.replace("postgres://", "postgresql+psycopg2://", 1)
    elif _raw_uri.startswith("postgresql://") and "+psycopg2" not in _raw_uri:
        _raw_uri = _raw_uri.replace("postgresql://", "postgresql+psycopg2://", 1)

    SQLALCHEMY_DATABASE_URI = _raw_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())

    if _is_postgres:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {
                "sslmode": "disable",
            },
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
