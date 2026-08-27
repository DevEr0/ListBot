"""
Telegram notification layer.

Important:
- Logs Telegram's JSON error description instead of only HTTP status.
- Treats 403 as a Telegram/chat configuration problem.
- Falls back from photo to text when a photo is rejected.
"""
from datetime import datetime, timezone
from html import escape

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, REQUEST_TIMEOUT

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _request(method: str, payload: dict) -> tuple[bool, dict]:
    try:
        response = requests.post(
            f"{API_BASE}/{method}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "ok": False,
                "description": response.text[:500],
            }

        if response.ok and data.get("ok") is True:
            return True, data

        print(
            f"[notifier] Telegram {method} failed: "
            f"HTTP {response.status_code}; "
            f"error_code={data.get('error_code')}; "
            f"description={data.get('description')}"
        )
        return False, data

    except requests.RequestException as e:
        print(f"[notifier] Telegram {method} request failed: {type(e).__name__}: {e}")
        return False, {}


def check_telegram() -> bool:
    """Check token and target chat before trying to send listings."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[notifier] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return False

    ok, data = _request("getMe", {})
    if not ok:
        print(
            "[notifier] Bot token is invalid/revoked, or Telegram API rejected it."
        )
        return False

    bot = data.get("result", {})
    print(f"[notifier] authenticated as @{bot.get('username', 'unknown')}")

    ok, data = _request(
        "getChat",
        {"chat_id": TELEGRAM_CHAT_ID},
    )

    if not ok:
        print(
            "[notifier] Cannot access TELEGRAM_CHAT_ID. "
            "Check the chat ID and make sure the bot is allowed to access the chat."
        )
        return False

    chat = data.get("result", {})
    print(
        f"[notifier] target chat OK: "
        f"id={chat.get('id')} type={chat.get('type')}"
    )
    return True


def send_listing(listing: dict) -> bool:
    caption = _format(listing)

    image_url = listing.get("image_url")
    if image_url:
        ok = _send_photo(image_url, caption)
        if ok:
            return True

    return _send_text(caption)


def send_message(text: str) -> bool:
    return _send_text(text)


def send_startup(url: str) -> bool:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return _send_text(
        f"🚀 <b>Bot started</b>\n"
        f"Started at {now}.\n"
        f"Watching: <code>{_esc(url)}</code>"
    )


def send_heartbeat(cycle: int) -> bool:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return _send_text(
        f"✅ <b>Bot heartbeat</b>\n"
        f"Cycle #{cycle} completed at {now}.\n"
        f"Still watching list.am for new listings."
    )


def _send_photo(image_url: str, caption: str) -> bool:
    ok, _ = _request(
        "sendPhoto",
        {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML",
        },
    )
    return ok


def _send_text(text: str) -> bool:
    ok, _ = _request(
        "sendMessage",
        {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
    )
    return ok


def _format(listing: dict) -> str:
    title = _esc(listing.get("title", "Listing"))
    price = _esc(listing.get("price", "Price not shown"))
    url = escape(listing.get("url", ""), quote=True)

    return (
        f"🏠 <b>{title}</b>\n"
        f"💰 {price}\n\n"
        f'<a href="{url}">View on list.am →</a>'
    )


def _esc(text: str) -> str:
    return escape(str(text or ""))
