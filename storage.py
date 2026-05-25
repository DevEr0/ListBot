"""
Storage layer.
A flat JSON file mapping listing_id -> small metadata blob.
Atomic writes so a crash mid-save won't corrupt the file.
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
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[storage] could not read {SEEN_FILE}: {e}")
        return {}


def save_seen(seen: dict) -> None:
    tmp = SEEN_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SEEN_FILE)  # atomic on POSIX and Windows


def mark_seen(seen: dict, listing: dict) -> None:
    seen[listing["id"]] = {
        "first_seen": datetime.now(timezone.utc).isoformat(),
        "title": listing["title"],
        "price": listing["price"],
    }
