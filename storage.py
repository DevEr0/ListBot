"""
Persistent storage for listing IDs.

Only successfully notified listings are marked as seen.
"""
import json
import os
from datetime import datetime, timezone

from config import SEEN_FILE


def load_seen() -> dict:
    if not os.path.exists(SEEN_FILE):
        return {}

    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            print(f"[storage] {SEEN_FILE} is not a JSON object; starting empty.")
            return {}

        return data

    except (json.JSONDecodeError, OSError) as e:
        print(f"[storage] could not read {SEEN_FILE}: {e}")
        return {}


def save_seen(seen: dict) -> None:
    directory = os.path.dirname(os.path.abspath(SEEN_FILE))
    os.makedirs(directory, exist_ok=True)

    tmp = SEEN_FILE + ".tmp"

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)

    os.replace(tmp, SEEN_FILE)


def mark_seen(seen: dict, listing: dict) -> None:
    seen[listing["id"]] = {
        "first_seen": datetime.now(timezone.utc).isoformat(),
        "title": listing.get("title", ""),
        "price": listing.get("price", ""),
    }
