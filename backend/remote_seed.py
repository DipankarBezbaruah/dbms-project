"""Run this script from your LOCAL machine to seed the Render database."""
import os
import sys

# --- PASTE YOUR EXTERNAL DATABASE URL BELOW ---
# Get it from: Render Dashboard -> hostelout-db -> Connections -> External Database URL
EXTERNAL_DB_URL = input("Paste your Render EXTERNAL Database URL here: ").strip()

if not EXTERNAL_DB_URL:
    print("ERROR: You must paste the External Database URL!")
    sys.exit(1)

# Fix the URL for SQLAlchemy
if EXTERNAL_DB_URL.startswith("postgres://"):
    EXTERNAL_DB_URL = EXTERNAL_DB_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif EXTERNAL_DB_URL.startswith("postgresql://"):
    EXTERNAL_DB_URL = EXTERNAL_DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Add SSL for external connection
if "sslmode" not in EXTERNAL_DB_URL:
    EXTERNAL_DB_URL += "?sslmode=require"

# Set it so config.py picks it up
os.environ["DATABASE_URL"] = EXTERNAL_DB_URL

print(f"Connecting to: {EXTERNAL_DB_URL[:50]}...")

from seed import seed
seed()
print("\nDone! You can now close this window.")
