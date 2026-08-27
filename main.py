"""
List.am -> Telegram orchestrator.

A listing is marked as seen ONLY after its Telegram notification succeeds.
A notification cap prevents accidental flooding after a reset.
"""
import argparse
import os
import time

from config import (
    CHECK_INTERVAL_SECONDS,
    LISTAM_URL,
    SEEN_FILE,
    MAX_NOTIFICATIONS_PER_CYCLE,
    assert_configured,
)
from fetcher import fetch_page
from listings import parse_listings
from storage import load_seen, save_seen, mark_seen
from notifier import (
    check_telegram,
    send_listing,
    send_heartbeat,
    send_startup,
)

HEARTBEAT_EVERY = 5
_cycle_count = 0


def run_once(seed: bool = False) -> None:
    html = fetch_page()

    if not html:
        print("[main] ERROR: fetch_page() returned None.")
        return

    found = parse_listings(html)
    print(f"[main] parsed {len(found)} listings from page")

    if not found:
        print("[main] WARNING: parser returned 0 listings.")
        return

    seen = load_seen()
    new = [listing for listing in found if listing["id"] not in seen]

    print(
        f"[main] {len(new)} new vs. {len(seen)} already-seen"
    )

    if seed:
        for listing in new:
            mark_seen(seen, listing)

        save_seen(seen)
        print(f"[main] seeded {len(new)} listings (no notifications sent)")
        return

    if not new:
        save_seen(seen)
        return

    limit = min(len(new), MAX_NOTIFICATIONS_PER_CYCLE)

    if len(new) > limit:
        print(
            f"[main] notification safety limit: sending {limit} of "
            f"{len(new)} new listings this cycle"
        )

    sent = 0
    failed = 0

    for listing in new[:limit]:
        ok = send_listing(listing)

        if not ok:
            failed += 1
            print(
                f"[main] NOT marked seen because notification failed: "
                f"{listing['id']}"
            )
            # If Telegram is unavailable, don't hammer the API with 19 more requests.
            if failed >= 2:
                print(
                    "[main] Telegram notification failures detected; "
                    "stopping this cycle. Unsent listings remain pending."
                )
                break
            continue

        mark_seen(seen, listing)
        sent += 1
        time.sleep(1.0)

    save_seen(seen)

    remaining = sum(
        1 for listing in found if listing["id"] not in seen
    )

    print(
        f"[main] successfully sent {sent}; failed {failed}; "
        f"remaining unseen listings on page: {remaining}"
    )


def auto_seed_if_needed() -> None:
    if os.path.exists(SEEN_FILE):
        return

    print(
        "[main] seen.json not found — auto-seeding current listings "
        "(no notifications)."
    )

    run_once(seed=True)


def run_forever() -> None:
    global _cycle_count

    auto_seed_if_needed()

    print(
        f"[main] polling every {CHECK_INTERVAL_SECONDS}s | "
        f"heartbeat every {HEARTBEAT_EVERY} cycles | "
        f"max {MAX_NOTIFICATIONS_PER_CYCLE} notifications/cycle"
    )

    while True:
        _cycle_count += 1
        print(f"[main] cycle #{_cycle_count}")

        try:
            run_once()
        except Exception as e:
            print(f"[main] cycle error: {type(e).__name__}: {e}")

        if _cycle_count % HEARTBEAT_EVERY == 0:
            print(f"[main] sending heartbeat (cycle {_cycle_count})")
            send_heartbeat(_cycle_count)

        time.sleep(CHECK_INTERVAL_SECONDS)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="list.am -> Telegram new-listing bot"
    )
    ap.add_argument(
        "--seed",
        action="store_true",
        help="Record current listings without notifications.",
    )
    ap.add_argument(
        "--once",
        action="store_true",
        help="Run one cycle and exit.",
    )
    args = ap.parse_args()

    assert_configured()

    # Fail early with a useful diagnostic instead of producing hundreds of
    # identical 403 errors.
    if not check_telegram():
        raise SystemExit(
            "\nTelegram configuration check failed. "
            "Fix TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID and chat permissions."
        )

    send_startup(LISTAM_URL)

    if args.seed:
        run_once(seed=True)
    elif args.once:
        run_once()
    else:
        run_forever()


if __name__ == "__main__":
    main()
