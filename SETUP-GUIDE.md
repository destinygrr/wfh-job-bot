# 🏠 WFH JOB BOT — Setup Guide
### Free, permanent job alerts for **AI Testing / QA** and **Online Teaching / Tutoring** — work-from-home, pan-India

> **Cost: ₹0.** No subscription, no card, no "premium plan". Ever.
> **Time to set up: about 30 minutes**, once. After that it runs on its own, 6 times a day, for as long as you want.

---

## What you are getting

The bot wakes up by itself, checks these places, throws away anything that is not a good match, scores every job for trustworthiness (scam check) and messages **you** on your phone:

| Source | What it is good for | Works from cloud? |
|---|---|---|
| **LinkedIn** | AI testers, AI trainers, data annotation, online faculty | ✅ Yes |
| **Apna** | India-focused WFH roles (also has a "Work from Home" tag) | ✅ Yes |
| **Naukri** | Biggest Indian job pool | ⚠️ Only when run from your **home Wi-Fi** (Naukri blocks cloud servers) — see Part 5 |
| **Remotive + Jobicy** (bonus, free APIs) | Global remote AI-training & QA gigs that hire in India | ✅ Yes |
| **Jooble** (optional, free key) | Extra Indian listings — a good stand-in when Naukri blocks | ✅ Yes, after you add the free key |

It remembers every job it has shown you, so **you never get the same job twice**.
If there are no new jobs, it sends one "🤖 I'm alive" message a day, so you always know it is working.

---

## Part 1 · You already have the bot

The folder **`wfh-job-bot`** is the whole bot. Nothing else to buy.

```
wfh-job-bot/
├── jobbot/main.py          ← the bot itself
├── jobbot/config.yaml      ← YOUR settings (roles, keywords, filters, channels)
├── jobbot/sources.py       ← LinkedIn / Apna / Naukri / bonus connectors
├── jobbot/notify.py        ← phone alert senders (ntfy / Telegram / WhatsApp)
├── jobbot/scoring.py       ← the "is this a genuine job or a scam?" brain
├── secrets.env.example     ← copy → secrets.env, keep your keys here (PC runs)
├── run_windows.bat         ← double-click to run on Windows
├── SETUP-GUIDE.md          ← this file
└── SAFETY-FIRST.md         ← read this once before applying anywhere
```

**Order of work:** Part 2 (alerts) → Part 3 (free cloud) → Part 4 (test) → keep Part 5 for Naukri days → Part 6 tuning → Part 7 if something misbehaves.

---

## Part 2 · Switch on your alerts — pick one or more (all free)

| Channel | Setup time | Reliability | What it feels like |
|---|---|---|---|
| **A. ntfy** ⭐ recommended | 2 min | ★★★★★ | Instant notification on your phone. **Tap it → the job page opens** (one notification per job). No account, open-source. |
| **B. Telegram** | 5 min | ★★★★★ | One tidy message listing the best jobs. Never rate-limited. |
| **C. WhatsApp via Green API** | 10 min | ★★★★ | A real WhatsApp message, sent from your own number. Free plan = unlimited sends to up to 3 chats. |
| **D. CallMeBot** (legacy) | 5 min | ★★ | The old free WhatsApp gateway — unreliable since 2025. Only if you already have a working key. |

You can switch each one on/off any time in `jobbot/config.yaml` (`ntfy: true`, `telegram: true`, `greenapi: true`, `whatsapp: false`).

> **Why is there no "free unlimited official WhatsApp"?** WhatsApp itself doesn't offer one: Meta's official API needs a business account and charges per message. Green API (option C) is a hosted, paid-service-with-a-free-tier bridge that drives **your own** WhatsApp — that's why it can be free at your volume.

---

### 2A ⭐ ntfy — the easiest, most reliable option (2 minutes)

1. Install the free **ntfy** app on your phone — Android: Play Store · iPhone: App Store.
2. Open the app → tap **＋** (Subscribe to topic).
3. Type a **secret topic name you invent** — e.g. `wfh-rajesh-7k2p9x`. This name works like a password, so make it long and odd (not `rajesh123`).
4. Tap **Subscribe**. Your phone is now listening.
5. Put that same name into the bot as the secret **`NTFY_TOPIC`** (GitHub: Settings → Secrets and variables → Actions → New repository secret → Name `NTFY_TOPIC`, Value `wfh-rajesh-7k2p9x`).
6. Test it: **Actions → WFH Job Bot → Run workflow.** Your phone buzzes within a minute.

**How it looks:** title `93% | AI Test Engineer` · body `EY | Remote, India | ₹8-12 LPA` · **tap the notification and the job page opens**. On Android, also turn off battery optimisation for ntfy (Settings → Apps → ntfy → Battery → Unrestricted), else notifications can be delayed.

*(Optional: set `NTFY_SERVER` only if you self-host ntfy. Leave it empty otherwise.)*

---

### 2B · Telegram — bulletproof and free (5 minutes)

1. Install **Telegram**, open it. Search **@BotFather** → tap START.
2. Send `/newbot` → give it a name (e.g. *My WFH Bot*) → give it a username ending in `bot` (e.g. *my_wfh_alerts_bot*).
3. BotFather replies with a token like `8123456789:AAF-xxxxxxxxxxxxxxxxx` → that's **`TELEGRAM_BOT_TOKEN`**.
4. Open **your** new bot (BotFather gives the link) → tap START → send `hi`.
5. In your phone browser open: `https://api.telegram.org/bot<PASTE_TOKEN_HERE>/getUpdates`
6. You'll see `"chat":{"id":123456789, ...}` → that number is **`TELEGRAM_CHAT_ID`**.

---

### 2C · WhatsApp via Green API — free, from your own number (10 minutes)

1. Go to **https://console.green-api.com** → **Sign up** (free, email only).
2. Create an instance → choose the **Developer (free)** plan → you get:
   * **`idInstance`** — a number like `1101234567`
   * **`apiTokenInstance`** — a long code
3. The console shows a **QR code**. Scan it with your phone:
   **WhatsApp → Settings → Linked devices → Link a device.**
   (Exactly like linking WhatsApp Web. You can unlink any time from your phone.)
4. Add three secrets (same place as before):

   | Name | Value |
   |---|---|
   | `GREENAPI_ID_INSTANCE` | your idInstance |
   | `GREENAPI_API_TOKEN` | your apiTokenInstance |
   | `GREENAPI_CHAT_ID` | `91XXXXXXXXXX@c.us` — your own WhatsApp number, country code, no `+`, then `@c.us` |

5. Run the test (Part 4) — you'll receive a WhatsApp message **from your own number** (a safe "message to yourself" alert).
6. Free plan facts: **unlimited messages per month, up to 3 chats** (you only need one — yourself). The counter resets on the 1st of each month.

**Honest cautions:** this is *not* Meta's official Business API — it's a hosted bridge over WhatsApp Web, so use it **only to message yourself** with a handful of alerts a day. Never use it for bulk messaging strangers: that is what gets numbers banned. If WhatsApp logs the device out, open the console and scan the QR again.

---

### 2D · CallMeBot (legacy — retry only if you want to)

If your old key stopped working, CallMeBot's phone number changes from time to time and the service goes down for days. To retry:

1. Open **https://www.callmebot.com/blog/free-api-whatsapp-messages/**
2. Copy the **bot number currently shown on that page** (do not use an old number from a screenshot or blog).
3. Save it as a WhatsApp contact → send: `I allow callmebot to send me messages`
4. Wait for the reply with your APIKEY. No reply in 2 minutes? CallMeBot's own rule: **try again after 24 hours.**
5. Then set the secrets `CALLMEBOT_PHONE` (`919876543210`) and `CALLMEBOT_APIKEY`, and turn it on in `config.yaml` (`whatsapp: true`).

If it still doesn't answer, it is a service-side outage — nothing is wrong with your bot. Use 2A, 2B or 2C instead (they are more dependable anyway).

---

## Part 3 · Put the bot on free cloud (GitHub) — recommended (15 minutes)

**GitHub runs your bot every 3 hours on their servers, free, even when your computer is off.**

### 3.1 Create the account & repo
1. Go to **https://github.com** → Sign up (free). Verify your email.
2. Top-right **+** → **New repository**.
3. Repository name `wfh-job-bot` · choose **Public** · **Create repository**.
   *(Public repos get unlimited free automation. **Private** is also free — your usage is ~180 of the 2,000 free minutes/month.)*

### 3.2 Upload the bot
1. On the repo page: **Add file → Upload files**.
2. Open your `wfh-job-bot` folder, select **all files and folders inside it** (`jobbot`, `.github`, `requirements.txt`, the run files, the guides) and **drag them into the browser window**.
3. Type `first upload` → **Commit changes**.
4. **Check:** a folder `.github` must appear in the list. If it doesn't (Windows hides it sometimes): **Add file → Create new file**, type the file name as `.github/workflows/jobbot.yml` (the `/` characters create the folders automatically), paste the file's contents, commit.

### 3.3 Give the bot your alert keys (they stay encrypted)
**Settings → Secrets and variables → Actions → New repository secret** — add the ones for the channels you chose in Part 2:

| Secret name | For which channel | Example value |
|---|---|---|
| `NTFY_TOPIC` | 2A ntfy ⭐ | `wfh-rajesh-7k2p9x` |
| `TELEGRAM_BOT_TOKEN` | 2B Telegram | `8123456789:AAF-xxxx` |
| `TELEGRAM_CHAT_ID` | 2B Telegram | `123456789` |
| `GREENAPI_ID_INSTANCE` | 2C WhatsApp | `1101234567` |
| `GREENAPI_API_TOKEN` | 2C WhatsApp | `d75b3a66374942c5b3c019c698abc2...` |
| `GREENAPI_CHAT_ID` | 2C WhatsApp | `919876543210@c.us` |
| `CALLMEBOT_PHONE` / `CALLMEBOT_APIKEY` | 2D legacy | `919876543210` / `123456` |
| `JOOBLE_API_KEY` | optional (Part 6) | free key from jooble.org |

### 3.4 Switch it on and test it
1. **Actions** tab → if there's a green **"I understand my workflows, go ahead and enable them"** button, click it.
2. Left side: **WFH Job Bot** → right side **Run workflow** → **Run workflow**.
3. Wait ~60 seconds, refresh. You'll see a run with a green ✅ — click it → **Run the bot** to read the log (jobs found per site, and each alert channel's result).
4. **Check your phone.** The first run alerts the best matching jobs (up to 6). If nothing matched that minute, you get the "🤖 I'm alive" message instead.

From now on it runs by itself **6 times a day — 6:30 am, 9:30 am, 12:30 pm, 3:30 pm, 6:30 pm, 9:30 pm IST**. (GitHub's free scheduler can be a few minutes late at busy times — harmless.)

---

## Part 4 · Prove the alerts work right now (2 minutes)

**On GitHub:** repo → **Actions** → **WFH Job Bot** → **Run workflow**. The log ends with something like:

```
  ntfy               : OK — 3 separate job notification(s) sent
  telegram           : OK — true
  whatsapp_greenapi  : OK — 3EB0C767D097B7C7C030
```

**On your PC** (Part 5), open the folder, double-click `run_windows.bat` — it prints the same lines, and to test alerts on their own:

```
python -m jobbot.main --test
```

`--test` also prints a **channel checklist** showing which keys are detected and which are missing:

```
Alert channels — what is set up right now:
  • ntfy               : configured
  • telegram           : NOT SET (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)
```

---

## Part 5 · Optional: run it on your Windows PC (this is what makes NAUKRI work)

Naukri uses a captcha to block cloud servers, so your GitHub bot will honestly report:
`naukri : blocked by Naukri (captcha) — normal from cloud IPs; works from your home Wi-Fi`.
From **your home internet**, Naukri lets the bot in. So run this occasionally:

1. Install Python (free): https://www.python.org/downloads/ → **tick "Add python.exe to PATH"** during setup.
2. Download your bot: on GitHub click **Code → Download ZIP** → right-click the ZIP → **Extract All**.
3. Copy **`secrets.env.example`** → rename the copy to **`secrets.env`** → open with Notepad → fill in the values for your channels (same names as the secrets: `NTFY_TOPIC=...`, `GREENAPI_ID_INSTANCE=...`, etc.) → save.
4. Double-click **`run_windows.bat`** — the first time it installs two free Python pieces (~1 min), then it runs:

   ```
   [linkedin ] 60 jobs
   [apna     ] 75 jobs
   [naukri   ] 45 jobs          ← this line only works from home Wi-Fi
   ntfy      : OK — 2 separate job notification(s) sent
   ```

   A full report opens at **`data\latest_digest.html`** — double-click it to see every job with its trust score.

---

## Part 6 · Tuning it to suit you (all in `jobbot/config.yaml`, edit in Notepad)

```yaml
profiles:
  - name: "AI Testing & QA"
    keywords: [ "AI testing", "AI trainer", ... ]     # add/remove search words
  - name: "Teaching & Tutoring"
    keywords: [ "online tutor", "faculty", ... ]

alerts:
  max_jobs_per_alert: 6        # how many jobs per message
  min_trust_score: 55          # raise to 65-70 to get only the best jobs
  heartbeat_daily: true        # daily "I'm alive" message
  ntfy: true
  telegram: true
  greenapi: true
  whatsapp: false              # CallMeBot legacy
```

* **Too many alerts?** → `min_trust_score: 68`
* **Wrong kind of jobs?** → tune the `keywords` lists; that's the only change needed
* **No repeats:** the bot remembers every job across runs (`data/seen_jobs.json`)

### Optional: the free Jooble key (more Indian jobs, no captcha)
1. **https://jooble.org/api/about** → get a free API key (no card).
2. Add it as the secret `JOOBLE_API_KEY`, and set `jooble: true` in `config.yaml`.

---

## Part 7 · Troubleshooting

| What you see | What it means / what to do |
|---|---|
| `ntfy : OK` but no notification on the phone | In the ntfy app, make sure you subscribed to **exactly** the same topic spelling. On Android, set ntfy battery usage to **Unrestricted**. |
| `ntfy : FAIL — HTTP 429` | ntfy's public rate limit — rare (the bot already pauses 1 second between notifications). It resolves on the next run. |
| `telegram : FAIL — chat not found` | Send `hi` to your bot first, then re-check the chat id from `getUpdates`. |
| `whatsapp_greenapi : FAIL — HTTP 401` | Wrong `idInstance`/token — copy them again from console.green-api.com. |
| Green API `466` error | Free plan chat limit (3 chats). Make sure the bot only ever messages **your own** number. |
| WhatsApp stopped arriving | The linked device logged out — open the Green API console and scan the QR again. |
| `whatsapp_callmebot : FAIL` | CallMeBot is down or the number changed. Official advice: retry after 24h with the number shown on their page — or simply move to ntfy/Telegram/Green API (Part 2). |
| `naukri : blocked by Naukri (captcha)` | Expected on cloud. Run from home Wi-Fi (Part 5) or turn on Jooble (Part 6). |
| No message for a long time | With 0 new jobs you only get the daily "I'm alive" message — check that one arrived. |
| `matched role : 0` | Your saved keywords are too narrow today — add a few words in `config.yaml`. |
| GitHub emails about a failed run | Open the run → read the red step → usually a typo in a secret name. |

---

## Part 8 · Bonus: where these jobs actually live (so you also apply directly)

The bot covers the platforms you asked for. These are the same kind of roles on the employer's own site — worth a weekly 10-minute visit:

**AI training / data-annotation gigs (pay in USD, hire remotely in India):** Appen, TELUS International AI, Outlier / Scale AI, iMerit, Innodata, Sigma AI, Encord, Remotasks, DataAnnotation, Alignerr.
**QA / testing WFH roles in India:** TCS, Cognizant, Capgemini, Accenture, Wipro, Tech Mahindra, HCL, Genpact, WNS, plus product companies' careers pages.
**Online teaching / tutoring (age is not a barrier, subject expertise matters):** Vedantu, PlanetSpark, Cuemath, UpGrad, Unacademy, Chegg Tutors, UrbanPro, Superprof, LearnPick, Preply, PhysicsWallah — plus school/college "Online Faculty" posts on LinkedIn.
**Non-voice WFH (good for stability):** Concentrix, Teleperformance, Foundever, TaskUs, Startek, [24]7.ai, HGS, Firstsource — ask specifically for "work-from-home / remote chat-email support".

**Your 50-year-old advantage:** for AI-training, tutoring, QA-lead and "subject matter expert" roles, experience is the *product*. Put your years of experience in the first line of your CV — bots filter for it, humans pay for it.

---

## Part 9 · Rules built into the bot so it protects you

* **Only WFH jobs** — on-site roles are dropped, not merely down-ranked.
* **Age-friendly** — "Freshers only", internships and stipend-only posts are removed.
* **Scam scanner** — anything mentioning registration fee, security deposit, joining kit, refundable deposit, investment, MLM/network marketing, "commission only", daily payouts or WhatsApp-only hiring is penalised hard and flagged with ⚠ in your alert.
* **Trust score** — every job gets 0-100. Green 🟢 ≥75, Yellow 🟡 60-74, Orange 🟠 <60. Alerts only carry jobs above your threshold (default 55).
* **Well-known employer bonus** — verified, registered companies (Accenture, TCS, EY, Sandisk, Vedantu, Appen, TELUS…) get +10; unknown names do not.
* **No repeats, ever** — seen jobs are remembered across runs.
* **Nothing is paid, nothing is auto-applied** — the bot only *tells* you. You decide what to apply to, always using the official link.

Read **SAFETY-FIRST.md** once before you start applying — it is the single most valuable page here, and it's how you stay out of the 99% of fake "work from home" offers in India.
