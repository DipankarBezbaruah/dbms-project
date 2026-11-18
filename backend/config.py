import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    _raw_uri = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost/hostelout",
    )
    # Render provides postgres:// but SQLAlchemy 2.x requires postgresql+psycopg2://
    if _raw_uri.startswith("postgres://"):
        _raw_uri = _raw_uri.replace("postgres://", "postgresql+psycopg2://", 1)
    elif _raw_uri.startswith("postgresql://"):
        _raw_uri = _raw_uri.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Add SSL for Render PostgreSQL
    if "postgresql" in _raw_uri:
        if "?" in _raw_uri:
            _raw_uri += "&sslmode=require"
        else:
            _raw_uri += "?sslmode=require"

    SQLALCHEMY_DATABASE_URI = _raw_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())
