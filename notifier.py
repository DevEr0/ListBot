"""
Notification layer (Telegram).
Tries to send the listing as a photo with caption (nicer UI).
Falls back to plain text if the image URL is missing or refused.
Also exposes send_heartbeat() for periodic "still alive" pings.
"""
import requests
from datetime import datetime, timezone
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_listing(listing: dict) -> bool:
    caption = _format(listing)

    if listing.get("image_url"):
        ok = _send_photo(listing["image_url"], caption)
        if ok:
            return True
        # Fall through to text if Telegram rejected the photo URL.

    return _send_text(caption)


def send_startup(url: str) -> bool:
    """Send a notification when the bot starts up."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"🚀 <b>Bot started</b>\n"
        f"Started at {now}.\n"
        f"Watching: <code>{_esc(url)}</code>"
    )
    return _send_text(text)


def send_heartbeat(cycle: int) -> bool:
    """Send a short status message so you know the bot is alive."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = (
        f"✅ <b>Bot heartbeat</b>\n"
        f"Cycle #{cycle} completed at {now}.\n"
        f"Still watching list.am for new listings."
    )
    return _send_text(text)


def _send_photo(image_url: str, caption: str) -> bool:
    try:
        r = requests.post(
            f"{API_BASE}/sendPhoto",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": image_url,
                "caption": caption,
                "parse_mode": "HTML",
            },
            timeout=15,
        )
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[notifier] sendPhoto failed: {e}")
        return False


def _send_text(text: str) -> bool:
    try:
        r = requests.post(
            f"{API_BASE}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[notifier] sendMessage failed: {e}")
        return False


def _format(listing: dict) -> str:
    return (
        f"🏠 <b>{_esc(listing['title'])}</b>\n"
        f"💰 {_esc(listing['price'])}\n\n"
        f'<a href="{listing["url"]}">View on list.am →</a>'
    )


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
