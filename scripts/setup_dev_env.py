"""
setup_dev_env.py — Quick development environment setup script.
Run once: python scripts/setup_dev_env.py
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"

env_example = BACKEND / ".env.example"
env_target = BACKEND / ".env"

if env_target.exists():
    print(f"[SKIP] {env_target} already exists.")
else:
    shutil.copy(env_example, env_target)
    # Patch to use SQLite for local dev (no Docker required)
    content = env_target.read_text()
    content = content.replace(
        "DATABASE_URL=postgres://krishilink:krishilink@localhost:5432/krishilink_dev",
        "DATABASE_URL=sqlite:///db.sqlite3",
    )
    env_target.write_text(content)
    print(f"[OK] Created {env_target} (SQLite mode — edit to use PostgreSQL)")

print("\nNext steps:")
print("  1. cd backend")
print("  2. Activate venv:  venv\\Scripts\\activate  (Windows) | source venv/bin/activate (Unix)")
print("  3. python manage.py migrate")
print("  4. python manage.py createsuperuser")
print("  5. python manage.py runserver")
