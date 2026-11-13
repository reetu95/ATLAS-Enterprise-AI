"""Initialize ATLAS tables in Render PostgreSQL from infra/schema.sql.

Run from the project root with: python scripts/init_db.py
"""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "infra" / "schema.sql"
REQUIRED = ("documents", "feedback", "audit_events", "approvals", "chat_messages")


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL", "").strip()

    if not url or "YOUR_" in url or "USERNAME:" in url:
        print("ERROR: Set a real DATABASE_URL in the project .env file.")
        return 1

    if not SCHEMA.is_file():
        print(f"ERROR: Schema not found: {SCHEMA}")
        return 1

    print("Connecting to Render PostgreSQL...")

    try:
        schema_sql = SCHEMA.read_text(encoding="utf-8")

        with psycopg.connect(url, connect_timeout=15) as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
                cur.execute("SELECT current_database()")
                dbname = cur.fetchone()[0]

                for table in REQUIRED:
                    cur.execute("SELECT to_regclass(%s)", (f"public.{table}",))
                    if cur.fetchone()[0] is None:
                        raise RuntimeError(f"Missing table: public.{table}")

    except (OSError, psycopg.Error, RuntimeError) as exc:
        print(f"ERROR: Database initialization failed: {type(exc).__name__}: {exc}")
        return 1

    print(f"SUCCESS: Database {dbname} initialized. Verified {len(REQUIRED)} tables.")
    return 0


if __name__ == "__main__":
    sys.exit(main())