"""
Central configuration. Every other module reads from here.
Secrets come from .env (never commit that file).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- What to monitor ---
# Open list.am in your browser, apply your filters (category, price, rooms,
# district, currency), then copy the URL from the address bar and paste it here.
# Example below is "Houses for sale" in Yerevan with a price range.
LISTAM_URL = os.getenv(
    "LISTAM_URL",
    "https://www.list.am/category/63?price1=50000&price2=200000&n=1",
)

# --- Polling ---
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "900"))  # 15 min
REQUEST_TIMEOUT = 20

# --- Storage ---
# On Railway the container filesystem is ephemeral — seen.json is wiped on every
# redeploy.  To persist it across deploys:
#   1. Create a Volume in your Railway project (dashboard → + New → Volume).
#   2. Mount it to e.g. /data.
#   3. Set SEEN_FILE=/data/seen.json in Railway → Variables.
# Without a volume, the bot auto-seeds on every restart (no notification flood).
SEEN_FILE = os.getenv("SEEN_FILE", "seen.json")

# --- HTTP ---
# Pretend to be a normal browser. Don't change the language unless you also
# update your CSS selectors — list.am serves different DOM in hy/ru/en.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Sanity check at import time so you fail fast instead of mid-loop.
def assert_configured():
    missing = [k for k, v in {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "LISTAM_URL": LISTAM_URL,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing config values: {', '.join(missing)}. Check your .env file.")
