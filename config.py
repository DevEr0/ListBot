"""
Central configuration for ListBot.
Secrets should be supplied through Railway environment variables or .env locally.
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LISTAM_URL = os.getenv(
    "LISTAM_URL",
    "https://www.list.am/category/63?price1=50000&price2=200000&n=1",
)

CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "900"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

SEEN_FILE = os.getenv("SEEN_FILE", "seen.json")

# Safety valve: don't flood Telegram after a reset/redeploy.
MAX_NOTIFICATIONS_PER_CYCLE = int(
    os.getenv("MAX_NOTIFICATIONS_PER_CYCLE", "20")
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def assert_configured():
    missing = [
        k for k, v in {
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
            "LISTAM_URL": LISTAM_URL,
        }.items() if not v
    ]
    if missing:
        raise RuntimeError(
            f"Missing config values: {', '.join(missing)}. "
            "Check Railway Variables / .env."
        )
