"""
check_env.py — Diagnostic script for .env configuration and Supabase connectivity.
Reports ONLY key names and masked connection status. NEVER exposes secret values.
"""
import os
import re
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"


def mask_secrets(text: str) -> str:
    """Mask password or credentials in error messages or URLs."""
    if not text:
        return ""
    # Mask password in URI pattern :password@
    masked = re.sub(r':([^@/:]+)@', r':*****@', text)
    # Mask password=value keyword parameter
    masked = re.sub(r'password=\S+', 'password=*****', masked, flags=re.IGNORECASE)
    return masked


def check():
    print("=== Environment Diagnostics ===")
    
    # 1. Existence
    exists = ENV_PATH.is_file()
    print(f".env exists: {exists} ({ENV_PATH})")
    if not exists:
        print("Status: FAILED (.env file missing in project root)")
        return

    # 2. Key names defined (names ONLY)
    config = dotenv_values(ENV_PATH)
    defined_keys = list(config.keys())
    print(f"Keys defined in .env: {defined_keys}")

    # 3. Load into environment
    load_dotenv(ENV_PATH)
    raw_db_url = os.environ.get("DATABASE_URL", "").strip()

    # 4. Validity checks
    issues = []
    if not raw_db_url:
        issues.append("DATABASE_URL is empty or not set")
    else:
        if not (raw_db_url.startswith("postgresql://") or raw_db_url.startswith("postgres://")):
            issues.append("DATABASE_URL must start with postgresql:// or postgres://")
        if "[" in raw_db_url or "]" in raw_db_url:
            issues.append("DATABASE_URL contains unreplaced brackets '[' or ']'")
        placeholders = ["YOUR_PASSWORD", "YOUR_PROJECT_REF", "YOUR_REGION", "YOUR-PASSWORD", "YOUR-PROJECT-REF"]
        for p in placeholders:
            if p in raw_db_url:
                issues.append(f"DATABASE_URL contains placeholder '{p}'")

    if issues:
        print(f"DATABASE_URL validity: INVALID ({', '.join(issues)})")
        print("Connection check skipped due to invalid connection URL.")
        return
    else:
        print("DATABASE_URL validity: VALID format")

    # 5. Connection test
    try:
        import psycopg2
        conn = psycopg2.connect(raw_db_url, sslmode="require")
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        print("Database connection: Connected successfully")
    except Exception as e:
        err_cls = e.__class__.__name__
        err_msg = mask_secrets(str(e))
        print(f"Database connection: FAILED [{err_cls}]: {err_msg}")


if __name__ == "__main__":
    check()
