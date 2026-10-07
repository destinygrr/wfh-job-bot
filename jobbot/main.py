"""WFH Job Bot — main entry point.

Usage
-----
    python -m jobbot.main              # normal run (checks jobs, alerts you)
    python -m jobbot.main --dry-run    # check jobs, write digest, send NOTHING
    python -m jobbot.main --test       # send a test alert to WhatsApp/Telegram
    python -m jobbot.main --config jobbot/config.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# allow "python jobbot/main.py" too
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from jobbot import digest, notify, scoring, sources, store, settings as cfgmod
else:
    from . import digest, notify, scoring, sources, store, settings as cfgmod


def _age_ok(job, max_days: int) -> bool:
    if not job.posted or max_days <= 0:
        return True
    try:
        d = datetime.fromisoformat(job.posted[:10]).replace(tzinfo=timezone.utc)
    except Exception:                                   # noqa: BLE001
        return True
    return datetime.now(timezone.utc) - d <= timedelta(days=max_days)


def _hard_excluded(job, flt, remote_only: bool = True) -> bool:
    # you asked for WORK FROM HOME: on-site roles are dropped, not just down-ranked
    if remote_only and any("not clearly work-from-home" in f for f in job.red_flags):
        return True
    if flt.get("exclude_fresher_only", True) and any("Freshers-only" in f for f in job.red_flags):
        return True
    if flt.get("exclude_internships", True) and any("Internship" in f for f in job.red_flags):
        return True
    if flt.get("exclude_commission_only", True) and any(
            w in " ".join(job.red_flags).lower() for w in ("commission-only", "mlm", "investment")):
        return True
    return False


def run(config_path: str | None = None, dry_run: bool = False, test: bool = False) -> int:
    t0 = time.time()
    s = cfgmod.load_settings(config_path)

    # ---------------------------------------------------------------- test mode
    if test:
        print("Alert channels — what is set up right now:")
        for k, v in notify.channel_status(s).items():
            print(f"  • {k:<19}: {v}")

        msg = ("✅ <b>WFH Job Bot connected!</b>\n\n"
               "Your bot is wired up correctly. It will now watch LinkedIn, Apna, Naukri "
               "(+ bonus remote boards) for AI Testing / QA and Teaching / Tutoring "
               "work-from-home jobs and ping you here.")
        if s.ntfy_topic:
            print("\n(Sending to ntfy as a test notification...)")
        res = notify.send_all(s, msg)

        print("\nTest alert results:")
        for k, v in res.items():
            print(f"  • {k:<19}: {v}")

        configured = [k for k, v in notify.channel_status(s).items() if v == "configured"]
        sent_ok = [k for k, v in res.items() if v.startswith("OK")]
        if configured and not sent_ok:
            print("\n  A channel IS configured but the test failed — read the error above.")
            print("     • WhatsApp 401  -> wrong idInstance / apiTokenInstance (copy again from console.green-api.com)")
            print("     • WhatsApp 466  -> free plan allows max 3 chats; check GREENAPI_CHAT_ID is your own number")
            print("     • Telegram 401  -> wrong bot token / chat id; send 'hi' to your bot first")
            print("     • ntfy 429      -> rate limit; try again in a minute")
        elif not sent_ok:
            print("\n  Nothing is configured yet. Pick ONE channel (all free) — you do NOT need all of them:")
            print("   1) ntfy      — easiest, 2 minutes, instant phone notification  → SETUP-GUIDE.md Part 2A")
            print("   2) Telegram  — bulletproof, never rate-limited                → SETUP-GUIDE.md Part 2B")
            print("   3) WhatsApp  — Green API free plan, sends from your own number → SETUP-GUIDE.md Part 2C")
        return 0

    st = store.Store(s.path(s.state_file))
    max_per_source = int(s.filters.get("max_jobs_per_source", 200))
    print(f"WFH Job Bot — {datetime.now().strftime('%d %b %Y %I:%M %p')}")
    print(f"Keywords: {', '.join(s.all_keywords[:8])}{' …' if len(s.all_keywords) > 8 else ''}")

    fetched, health = [], {}
    for name, fn in sources.FETCHERS.items():
        if not s.sources.get(name, False):
            continue
        jobs, note = fn(s, max_per_source)
        health[name] = note
        fetched.extend(jobs)
        print(f"  [{name:<9}] {note}")

    # ---------------- evaluate + de-duplicate ----------------
    unique = {}
    for j in fetched:
        if j.key in unique:
            continue
        unique[j.key] = j.evaluate(s, profile_name="")

    fresh, skipped_age, irrelevant = [], 0, 0
    for j in unique.values():
        if not st.is_new(j.key):
            continue
        if not j.relevant:                     # not an AI-Testing / Teaching role
            irrelevant += 1
            continue
        if not _age_ok(j, int(s.filters.get("max_age_days", 30))):
            skipped_age += 1
            continue
        if _hard_excluded(j, s.filters, s.remote_only):
            continue
        fresh.append(j)

    onsite_dropped = sum(
        1 for j in unique.values()
        if j.relevant and any("not clearly work-from-home" in f for f in j.red_flags))

    fresh.sort(key=lambda j: j.sort_key())
    min_trust = int(s.alerts.get("min_trust_score", 0))
    alert_jobs = [j for j in fresh if j.trust >= min_trust]
    cap = int(s.alerts.get("max_jobs_per_alert", 8))
    alert_batch, overflow = alert_jobs[:cap], alert_jobs[cap:]

    # Remember everything we saw, so the next run only alerts NEW jobs.
    # Exception: jobs that were above your threshold but didn't fit in this
    # message (the "overflow") stay unremembered, so they are alerted in the
    # NEXT run instead of being silently skipped. (--dry-run consumes nothing.)
    queued_keys = {j.key for j in overflow}
    if not dry_run:
        st.mark([k for k in unique.keys() if k not in queued_keys])
        st.save()

    # ---------------- report + digest ----------------
    report = {
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": health,
        "fetched": len(fetched),
        "unique": len(unique),
        "new_matching": len(fresh),
        "alerted": len(alert_batch),
        "below_threshold": len(fresh) - len(alert_jobs),
        "too_old": skipped_age,
        "irrelevant": irrelevant,
        "onsite_dropped": onsite_dropped,
        "queued_next": len(overflow),
        "matched_role": sum(1 for j in unique.values() if j.relevant),
        "total_seen": len(st),
        "elapsed": time.time() - t0,
    }

    if not dry_run and alert_batch:
        msg = notify.build_summary_message(s, alert_batch)
        if overflow:
            msg += (f"\n+ {len(overflow)} more good job(s) waiting — you'll get them in "
                    f"the next check, so nothing is lost. (Full list any time: data/latest_digest.html)")
        report["notify"] = notify.notify_new_jobs(s, alert_batch, msg)
    elif not dry_run:
        # heartbeat once a day so you know the bot is alive and free
        hb = st.heartbeat_state()
        today = datetime.now().strftime("%Y-%m-%d")
        if s.alerts.get("heartbeat_daily", True) and hb.get("last") != today:
            report["notify"] = notify.send_all(s, notify.build_heartbeat_message(report))
            hb["last"] = today
            st.set_heartbeat_state(hb)
    else:
        report["notify"] = {"dry-run": "no alerts sent"}

    digest_set = fresh if fresh else alert_batch
    md = digest.build_markdown(digest_set, list(unique.values()), report, min_trust=min_trust)
    html = digest.build_html(digest_set, list(unique.values()), report, min_trust=min_trust)
    if not dry_run:
        digest.write_files(s, html, md)
        rp = s.path("data/last_run.json")
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n──────── RESULT ────────")
    print(f"  fetched      : {report['fetched']}  (unique {report['unique']})")
    print(f"  matched role : {report['matched_role']}")
    if s.remote_only:
        print(f"  ON-SITE DROPPED: {report['onsite_dropped']}  (right role, but not work-from-home)")
    print(f"  NEW matching : {report['new_matching']}   (wrong-role ignored: {report['irrelevant']})")
    if report["queued_next"]:
        print(f"  queued next  : {report['queued_next']}  (above threshold, will be alerted in the NEXT run)")
    print(f"  alerted      : {report['alerted']}   (below threshold: {report['below_threshold']})")
    for k, v in (report.get("notify") or {}).items():
        print(f"  {k:<12} : {v}")
    if alert_batch:
        print("\n  Top new jobs:")
        for j in alert_batch[:5]:
            print(f"   • [{j.trust}] {j.title} — {j.company} ({j.source})")
            print(f"     {j.url}")
    print(f"\n  digest → {s.digest_html}   ({time.time()-t0:.0f}s)")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Checks LinkedIn/Apna/Naukri for WFH jobs and alerts you.")
    ap.add_argument("--config", default=None, help="path to config.yaml")
    ap.add_argument("--dry-run", action="store_true", help="do everything except sending alerts")
    ap.add_argument("--test", action="store_true", help="send a test alert and exit")
    a = ap.parse_args()
    sys.exit(run(a.config, a.dry_run, a.test))


if __name__ == "__main__":
    main()
