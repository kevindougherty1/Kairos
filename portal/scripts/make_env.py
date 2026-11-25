r"""Create portal/.env from portal/.env.example with fresh random secrets.

    .venv\Scripts\python.exe portal\scripts\make_env.py

Never overwrites an existing .env (delete it first if you really want a new one; the database
password inside must match the one the Postgres volume was created with).
"""

import secrets
import sys
from pathlib import Path

PORTAL = Path(__file__).resolve().parent.parent
example, target = PORTAL / ".env.example", PORTAL / ".env"

if target.exists():
    sys.exit(f"{target} already exists; leaving it alone.")

text = example.read_text(encoding="utf-8")
text = text.replace("DJANGO_SECRET_KEY=change-me", "DJANGO_SECRET_KEY=" + secrets.token_urlsafe(50), 1)
text = text.replace("POSTGRES_PASSWORD=change-me", "POSTGRES_PASSWORD=" + secrets.token_hex(16), 1)
if "change-me" in text:
    sys.exit(".env.example has an unexpected placeholder left; fill portal/.env by hand.")
target.write_text(text, encoding="utf-8", newline="\n")
print(f"Wrote {target} with new random secrets (it is gitignored).")
