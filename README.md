# 🏠 WFH Job Bot — free work-from-home job alerts on WhatsApp & Telegram

A small, free bot that searches **LinkedIn, Apna and Naukri** (plus free remote-job APIs) for
**work-from-home** jobs in **four** categories —
**AI Testing / QA / AI-training**, **Document Verification / KYC**, **Stock Market / Equity Research**
and **Online Teaching / Tutoring** — scores each job for genuineness, and pings **your phone**.
Stop refreshing job sites and stop falling for fake "work from home" offers.

* **Cost:** ₹0 — runs on GitHub's free cloud schedule.
* **Runs when your PC is off:** yes (GitHub Actions, 6×/day).
* **No repeats:** it remembers every job it has shown you.
* **Scam-aware:** flags registration fees, deposits, MLM, commission-only, WhatsApp-only hiring.
* **Nothing is paid, nothing is auto-applied:** you get a link, you decide.

👉 **Start here: [SETUP-GUIDE.md](SETUP-GUIDE.md)** (30 minutes, one time)
👉 **Then read: [SAFETY-FIRST.md](SAFETY-FIRST.md)** (how to never get scammed)

---

## 60-second summary of how it works

```
GitHub Actions (every 3 hours, free)
        │
        ├── LinkedIn   (remote filter, guest API)
        ├── Apna       (category pages: testing / qa / teaching / tutor / WFH)
        ├── Naukri     (works from home Wi-Fi; says so honestly when blocked)
        ├── Remotive + Jobicy  (free global remote APIs — AI-training gigs)
        └── Jooble     (optional free key)
        │
        ▼  relevance filter  →  WFH hard filter  →  trust score 0-100  →  scam flags
        │
        ├── ntfy push notification  (free, 2-min setup — recommended)
        ├── Telegram alert          (free bot, never rate-limited)
        ├── WhatsApp alert          (Green API free plan, from your own number)
        ├── WhatsApp alert          (CallMeBot — legacy, unreliable since 2025)
        └── data/latest_digest.html  ← full, pretty report you can open any time
```

## Files

| File | Purpose |
|---|---|
| `jobbot/main.py` | the run: fetch → filter → score → alert → save memory |
| `jobbot/sources.py` | LinkedIn, Apna, Naukri, Jooble, Remotive, Jobicy connectors |
| `jobbot/scoring.py` | relevance + trust score + Indian job-scam patterns |
| `jobbot/notify.py` | WhatsApp (CallMeBot), Telegram, optional e-mail |
| `jobbot/digest.py` | the HTML/Markdown report |
| `jobbot/store.py` | "seen jobs" memory so you never see a job twice |
| `jobbot/config.yaml` | **your** keywords, filters, alert settings |
| `secrets.env.example` | copy → `secrets.env`, keep your keys here (PC runs) |
| `run_windows.bat`, `run_mac_linux.sh` | one-click local run |
| `.github/workflows/jobbot.yml` | the free 6×/day cloud schedule |
| `data/` | memory + latest digest (auto-created) |

## Commands (for local runs)

```bash
python -m jobbot.main            # normal run (checks jobs, sends alerts)
python -m jobbot.main --test     # send a test alert to WhatsApp/Telegram only
python -m jobbot.main --dry-run  # check everything, send nothing, don't consume state
```

## FAQ

**Will Naukri work?** From GitHub's servers Naukri answers with a captcha (it blocks all datacentre
IPs). Run the bot occasionally from your home Wi-Fi (`run_windows.bat`) for Naukri, or add the free
Jooble key — same Indian job pool, no captcha.

**Is this against the rules of these sites?** The bot reads only publicly visible search pages at a
polite rate (a few requests every 3 hours) and never logs in, never scrapes personal data, never
auto-applies. You use it for your own personal job search.

**Which alert channel should I use?** **ntfy** is the easiest and most reliable (free app, 2 minutes, no
account, tap the notification to open the job). **Telegram** is the most dependable free bot.
**Green API** gives you a *real WhatsApp message from your own number* on its free plan (unlimited
sends to up to 3 chats) — that's the working WhatsApp route. **CallMeBot** (the old free WhatsApp
gateway) has been unreliable since 2025, so it is switched off by default; turn it back on in
`config.yaml` only if your key still works. See SETUP-GUIDE Part 2.

**Why is a job only 58% rated?** Usually the posting doesn't confirm work-from-home, or mentions
commission/incentives. Open the ⚠ flags and run the 60-second check in SAFETY-FIRST.md.

**Can I change the roles?** Yes — edit the `keywords` in `jobbot/config.yaml`. Nothing else to touch.
