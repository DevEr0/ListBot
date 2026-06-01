"""
Fetcher using a headless Playwright browser.

headless=True is required for any server environment (Railway, VPS, Docker,
GitHub Actions, etc.) — there is no display on those machines, so headless=False
crashes immediately and fetch_page() returns None every single cycle, which is
why the heartbeat kept firing but no listings were ever found.
"""
import time
import random
from playwright.sync_api import sync_playwright
from config import LISTAM_URL


def fetch_page(url: str = LISTAM_URL) -> str | None:
    """Return HTML using a headless browser."""

    time.sleep(random.uniform(2, 5))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,          # ← was False; False crashes on any server
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",   # prevents OOM crashes in Docker
                    "--disable-gpu",
                ]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(5)
            html = page.content()
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            browser.close()
            return html
    except Exception as e:
        print(f"[fetcher] error: {e}")
        return None