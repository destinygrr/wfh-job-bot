# ▶️ START HERE — do only this (10 minutes, once)

**Ignore every other file for now.** Just follow these 5 steps in order. At the end, your phone will buzz with work-from-home jobs — automatically, every 3 hours, free, forever.

**The recommendation, in one line:** use **ntfy** (free phone app). It is the fastest to set up and the most reliable. If you *also* want the alerts inside WhatsApp, do the extra page at the bottom **after** this works.

---

## ✅ STEP 1 — Put the ntfy app on your phone (3 minutes)

1. On your phone open the app store: **Play Store** (Android) or **App Store** (iPhone).
2. Search **ntfy** → it's a small free app (open-source, no ads, no account) → **Install**.
3. Open the app → tap the **+** button → it asks for a *topic name*.
4. Type this name, exactly (you can change the last part to something only you know):

   ```
   wfh-jobs-rajesh-7391
   ```

   > This name is the "password" of your alerts. Keep it long and odd, and don't share it.
5. Tap **Subscribe** / **OK**. That's it — your phone is now listening.

**Remember this name.** In STEP 4 you will type the exact same name into GitHub.

---

## ✅ STEP 2 — Create your free GitHub account (3 minutes)

*(GitHub is where the bot runs, so it works even when your computer is off.)*

1. On a computer (easier than phone) open **https://github.com** → **Sign up**.
2. Enter email → password → username → verify the email.
3. When it offers paid plans, just choose **Free**.

---

## ✅ STEP 3 — Put the bot on GitHub (3 minutes)

1. Top-right corner: click **+** → **New repository**.
2. Repository name: `wfh-job-bot` → choose **Public** → click the green **Create repository**.
3. On the next page click **Add file** → **Upload files**.
4. Open your **`wfh-job-bot`** folder on the computer. Select **everything inside it** (the `jobbot` folder, the `.github` folder, `requirements.txt`, the guides — all of it) and **drag it into the browser window**.
5. Wait for the upload to finish → click green **Commit changes**.
6. ✅ Check: in the file list you should see a folder named **`.github`**.
   *Don't see `.github`?* Windows hides folders starting with a dot. Fix: **Add file → Create new file**, type the name exactly as `.github/workflows/jobbot.yml` (the slashes make the folders for you), paste the contents of that file from your PC, and click **Commit changes**.

---

## ✅ STEP 4 — Give the bot your topic name (2 minutes)

1. In your repository, click **Settings** (top menu).
2. Left sidebar: **Secrets and variables** → **Actions**.
3. Click green **New repository secret**.
4. **Name:** type exactly

   ```
   NTFY_TOPIC
   ```
   **Secret:** type the topic name from STEP 1 (e.g. `wfh-jobs-rajesh-7391`) → **Add secret**.

✅ That is the **only secret you need** for this to work.

---

## ✅ STEP 5 — Switch it on and watch your phone (1 minute)

1. Click the **Actions** tab (top menu). If a green button appears — *"I understand my workflows, go ahead and enable them"* — click it.
2. Left side: click **WFH Job Bot**.
3. Right side: **Run workflow ▾** → green **Run workflow** button.
4. Wait 60 seconds → refresh the page. A run appears with a **green ✔**.
5. 🎉 **Your phone buzzes.** You'll get one notification per matching job — **tap the notification and the job page opens on your phone.**

### From now on — nothing to do
The bot runs by itself **6 times a day** (6:30 am, 9:30 am, 12:30 pm, 3:30 pm, 6:30 pm, 9:30 pm IST), completely free. On days with no new jobs you still get one **"🤖 I'm alive"** message so you know it's working.

---

## What the bot is hunting for you (all work-from-home, pan-India)

| # | Job type |
|---|---|
| 1 | AI Testing / QA / AI Trainer / Data Annotation |
| 2 | Document Verification / KYC |
| 3 | Stock Market / Equity Research Analyst |
| 4 | Online Teaching / Tutoring / Faculty |

Every job is scored 0–100 for genuineness: 🟢 75+ = good · 🟡 60–74 = fine · 🟠 below 60 = check carefully. On-site jobs, "freshers only" jobs and internships are thrown away. Anything that smells like a scam (registration fee, deposit, MLM, "commission only") is flagged in the alert.

---

## If something doesn't work (quick fixes)

| Problem | Fix |
|---|---|
| No notification on the phone | Open the ntfy app and check you subscribed to **exactly** the same topic spelling. On Android: phone Settings → Apps → ntfy → Battery → **Unrestricted**. |
| The GitHub run has a red ❌ | Open the run and read the last red lines — 99% of the time a secret name is misspelled. It must be exactly `NTFY_TOPIC`. |
| Log says `ntfy : SKIP` | The secret was not saved. Redo STEP 4. |
| I want to change the job types | Edit `jobbot/config.yaml` in your repo (pencil icon) → change the `keywords` under each job type → Commit. |
| I want to know what it found today | In your repo open `data` → `latest_digest.html` → Download → open it in your browser. Every job with its score. |

**Read `SAFETY-FIRST.md` once** (10 minutes) before you start applying. It is the most valuable page in this whole project — a genuine employer **never** asks you for money.

---

## OPTIONAL EXTRA — also get the alerts inside WhatsApp (10 minutes)

Do this **only after** the 5 steps above work.

1. Open **https://console.green-api.com** → **Sign up** (free).
2. Create an instance → choose the **Developer (free)** plan. You get two codes: `idInstance` and `apiTokenInstance`.
3. A **QR code** appears. Scan it with your phone: **WhatsApp → Settings → Linked devices → Link a device** (same as linking WhatsApp Web).
4. In GitHub: **Settings → Secrets and variables → Actions → New repository secret** — add these three:

   | Name | Value |
   |---|---|
   | `GREENAPI_ID_INSTANCE` | your idInstance (e.g. `1101234567`) |
   | `GREENAPI_API_TOKEN` | your apiTokenInstance |
   | `GREENAPI_CHAT_ID` | your WhatsApp number as `91XXXXXXXXXX@c.us` (no `+`, no spaces) |

5. Run **Actions → WFH Job Bot → Run workflow** again. You'll now get the WhatsApp message **and** the ntfy notifications.

*Free plan: unlimited messages, up to 3 chats — you only need one (yourself). Use it only to message yourself; never for bulk messaging.*
