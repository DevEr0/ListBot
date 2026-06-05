"""
Orchestrator.

Flow per cycle:
    1. fetcher.fetch_page()   -> HTML
    2. listings.parse_listings(html) -> [listing, ...]
    3. storage.load_seen()    -> dict of known IDs
    4. compute new = listings not in seen
    5. notifier.send_listing(l) for each new listing
    6. storage.mark_seen(...) + storage.save_seen(...)
    7. Every 5 cycles, send a heartbeat message to Telegram so you know the bot is alive.

Modes:
    python main.py --seed   # record current listings WITHOUT notifying (run this first!)
    python main.py --once   # one cycle then exit (good for cron)
    python main.py          # loop forever, sleeping CHECK_INTERVAL_SECONDS between cycles
"""
import os
import time
import argparse

from config import CHECK_INTERVAL_SECONDS, LISTAM_URL, SEEN_FILE, assert_configured
from fetcher import fetch_page
from listings import parse_listings
from storage import load_seen, save_seen, mark_seen
from notifier import send_listing, send_heartbeat, send_startup, send_message

# How often to send the "still alive" Telegram message.
HEARTBEAT_EVERY = 5

_cycle_count = 0


def run_once(seed: bool = False) -> None:
    html = fetch_page()
    if not html:
        print(
            "[main] ERROR: fetch_page() returned None.\n"
            "  On Railway: confirm railway.toml has the correct buildCommand.\n"
            "  The build log should contain 'playwright install chromium --with-deps'.\n"
            "  If it does not appear, redeploy after adding railway.toml."
        )
        return

    found = parse_listings(html)
    print(f"[main] parsed {len(found)} listings from page")

    seen = load_seen()
    new = [l for l in found if l["id"] not in seen]
    print(f"[main] {len(new)} new vs. {len(seen)} already-seen")

    for listing in new:
        if not seed:
            ok = send_listing(listing)
            if not ok:
                # Don't mark as seen if we failed to notify — try again next cycle.
                continue
            time.sleep(1.0)  # be gentle with Telegram's rate limits
        mark_seen(seen, listing)

    save_seen(seen)

    if seed:
        print(f"[main] seeded {len(new)} listings (no notifications sent)")
    else:
        print(f"[main] sent {len(new)} notifications")


def auto_seed_if_needed() -> None:
    """
    On Railway, seen.json is wiped on every redeploy.  Without this guard the
    bot treats every existing listing as new on startup and floods Telegram with
    100+ messages, then marks them all seen — so real new listings are never
    found until the next restart wipes seen.json again.

    Fix: if seen.json is absent (first run or post-restart), silently seed the
    current page instead of notifying, then continue with normal polling.
    A Telegram message is sent so you know a re-seed happened.
    """
    if os.path.exists(SEEN_FILE):
        return

    print("[main] seen.json not found — auto-seeding current listings (no notifications).")
    send_message(
        "📋 <b>Bot re-seeded</b>\n"
        "seen.json was missing (first deploy or Railway restart).\n"
        "Current listings recorded silently. "
        "You'll be notified about <b>new</b> listings from here on.\n\n"
        "<i>Tip: add a Railway Volume at /data and set "
        "<code>SEEN_FILE=/data/seen.json</code> to survive restarts.</i>"
    )
    run_once(seed=True)


def run_forever() -> None:
    global _cycle_count
    auto_seed_if_needed()
    print(f"[main] polling every {CHECK_INTERVAL_SECONDS}s  |  heartbeat every {HEARTBEAT_EVERY} cycles")
    while True:
        _cycle_count += 1
        print(f"[main] cycle #{_cycle_count}")
        try:
            run_once()
        except Exception as e:
            print(f"[main] cycle error: {e}")

        if _cycle_count % HEARTBEAT_EVERY == 0:
            print(f"[main] sending heartbeat (cycle {_cycle_count})")
            send_heartbeat(_cycle_count)

        time.sleep(CHECK_INTERVAL_SECONDS)


def main() -> None:
    ap = argparse.ArgumentParser(description="list.am → Telegram new-listing bot")
    ap.add_argument("--seed", action="store_true",
                    help="Record current listings without sending notifications.")
    ap.add_argument("--once", action="store_true",
                    help="Run one cycle and exit (use for cron).")
    args = ap.parse_args()

    assert_configured()
    send_startup(LISTAM_URL)

    if args.seed:
        run_once(seed=True)
    elif args.once:
        run_once()
    else:
        run_forever()


if __name__ == "__main__":
    main()
