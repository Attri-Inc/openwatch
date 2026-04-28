from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("OPENWATCH_DB", str(BASE_DIR / "data" / "openwatch.db"))
HOST = os.getenv("OPENWATCH_HOST", "0.0.0.0")
PORT = int(os.getenv("OPENWATCH_PORT", "8788"))
