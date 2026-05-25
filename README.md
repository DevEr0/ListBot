# list.am → Telegram bot

Watches a filtered list.am search page and sends new listings to a Telegram chat.

## How the pieces fit

```
main.py
  ├── fetcher.py    → downloads HTML from list.am (Playwright, bypasses Cloudflare)
  ├── listings.py   → parses HTML → [ {id, title, price, url, image_url}, ... ]
  ├── storage.py    → reads/writes seen.json (which IDs you've been notified about)
  ├── notifier.py   → posts to Telegram Bot API (listings + heartbeat)
  └── config.py     → all settings, loaded from .env
```

Per cycle, `main.py` does:
**fetch → parse → diff against `seen.json` → send unseen ones to Telegram → save updated `seen.json` → sleep.**  
Every **5 cycles** it also sends a heartbeat message (`✅ Bot heartbeat`) so you know it's still running.

> **Do new listings appear on page 1?** Yes — list.am sorts newest-first by default. Page 1 is all you need.

---

## Setup

### 1. Create the Telegram bot
1. In Telegram, message **@BotFather**.
2. Send `/newbot`, follow the prompts, pick a name.
3. Copy the bot token it gives you (`123456789:AAA...`).

### 2. Get your chat ID
1. Send any message to your new bot.
2. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser.
3. Find `"chat":{"id": 987654321, ...}`. That number is your chat ID.

### 3. Get your list.am URL
1. Open https://www.list.am, pick a category.
2. Apply filters (price, district, rooms, currency).
3. Copy the URL from the address bar.

### 4. Configure
```bash
cp .env.example .env
# edit .env — paste your token, chat ID, and list.am URL
```

### 5. Install
```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium     # one-time browser download
```

### 6. Seed first, THEN run
```bash
python main.py --seed   # records all current listings, sends nothing
python main.py          # from now on, only NEW listings get sent
```

---

## Deploying (recommended: Railway)

Railway is the easiest zero-ops option — free tier, always-on, deploy from GitHub.

### Railway (free tier, ~2 min setup)

1. Push your project to a **private** GitHub repo (never commit `.env`).
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**.
3. Select your repo.
4. Go to **Variables** and add each key from your `.env`:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `LISTAM_URL`
   - `CHECK_INTERVAL_SECONDS` (optional, default 900)
5. Go to **Settings → Deploy** and set the **Start Command** to:
   ```
   python main.py
   ```
6. Deploy. The bot starts immediately.

> **Persistent storage on Railway:** `seen.json` lives on the container's disk. Railway may reset it on redeploy — if that happens and you get re-notified about old listings, just re-run seed mode or commit an initial `seen.json` to the repo.

### Other options

| Option | Cost | Effort |
|---|---|---|
| Railway | Free tier | ~2 min |
| Fly.io | Free tier | ~10 min |
| Hetzner/DigitalOcean VPS | ~€4/mo | ~20 min + tmux/systemd |
| Raspberry Pi at home | Free (electricity) | Already set up |

For a VPS, use tmux or a systemd unit:
```bash
tmux new -s listam
source .venv/bin/activate
python main.py
# detach: Ctrl+B then D
```

---

## Heartbeat

Every **5 cycles** the bot sends a message like:

```
✅ Bot heartbeat
Cycle #5 completed at 2024-01-15 10:30 UTC.
Still watching list.am for new listings.
```

To change the frequency, edit `HEARTBEAT_EVERY = 5` in `main.py`.

---

## Troubleshooting

- **"parsed 0 listings"** → list.am changed selectors. Open the page, inspect a listing card, update `div.l` (title) and `div.p` (price) selectors in `listings.py`.
- **Telegram errors** → check the token has no spaces; chat ID must be an integer, not `@username`.
- **Getting spammed by re-posts** → same property, new ID. Extend `storage.py` to dedup by `(price, title)`.
- **HTTP 429 / blocks** → increase `CHECK_INTERVAL_SECONDS` to 1800 (30 min).
- **Playwright fails on Railway** → add `playwright install-deps chromium` to a `railway.toml` build command, or switch `fetcher.py` to `headless=True` for server environments.
