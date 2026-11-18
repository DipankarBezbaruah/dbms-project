import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    _raw_uri = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost/hostelout",
    )
    # Render provides postgres:// — use pg8000 pure-Python driver (no SSL issues)
    if _raw_uri.startswith("postgres://"):
        _raw_uri = _raw_uri.replace("postgres://", "postgresql+pg8000://", 1)
    elif _raw_uri.startswith("postgresql://"):
        _raw_uri = _raw_uri.replace("postgresql://", "postgresql+pg8000://", 1)

    SQLALCHEMY_DATABASE_URI = _raw_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(24).hex())

    # pg8000 handles SSL automatically — no extra config needed
