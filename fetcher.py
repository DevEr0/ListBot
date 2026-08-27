"""
List.am fetcher using Playwright/Chromium.
"""
import random
import time

from playwright.sync_api import sync_playwright
from config import LISTAM_URL, REQUEST_TIMEOUT, USER_AGENT


def fetch_page(url: str = LISTAM_URL) -> str | None:
    time.sleep(random.uniform(2, 5))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=USER_AGENT,
            )

            page = context.new_page()
            page.goto(
                url,
                timeout=REQUEST_TIMEOUT * 1000,
                wait_until="domcontentloaded",
            )

            # Give List.am time to finish rendering dynamic content.
            page.wait_for_timeout(5000)

            html = page.content()

            # Useful when debugging parser changes.
            try:
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except OSError as e:
                print(f"[fetcher] could not write debug.html: {e}")

            context.close()
            browser.close()
            return html

    except Exception as e:
        print(f"[fetcher] error: {type(e).__name__}: {e}")
        return None
