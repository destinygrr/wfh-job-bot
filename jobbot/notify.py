"""Notifiers: WhatsApp (CallMeBot, free), Telegram (free), Email (optional).

CallMeBot is a free personal-use WhatsApp gateway. Setup (2 minutes):
  1. Save the bot number shown on https://www.callmebot.com/blog/free-api-whatsapp-messages/
     as a WhatsApp contact on your phone (the number on that page changes - always
     double-check it there).
  2. Send it this exact message from your WhatsApp:
        I allow callmebot to send me messages
  3. It replies with your personal APIKEY.
  4. Put your number and key in secrets.env / GitHub Secrets:
        CALLMEBOT_PHONE=919876543210      (country code + number, no + and no spaces)
        CALLMEBOT_APIKEY=1234567
"""
from __future__ import annotations

import smtplib
import time
import urllib.parse
from email.message import EmailMessage
from typing import List, Tuple

import requests


def _digits(text: str) -> str:
    return "".join(ch for ch in (text or "") if ch.isdigit())


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 20].rstrip() + "\n... (truncated)"


# --------------------------------------------------------------------------- #
def send_whatsapp(s, message: str) -> Tuple[bool, str]:
    if not (s.callmebot_phone and s.callmebot_apikey):
        return False, "skipped (CALLMEBOT_PHONE / CALLMEBOT_APIKEY not set)"
    try:
        r = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={"phone": s.callmebot_phone,
                    "text": _short(message, 2400),
                    "apikey": s.callmebot_apikey},
            timeout=30,
        )
        body = r.text.strip().replace("\n", " ")[:160]
        ok = r.status_code == 200 and ("message queued" in body.lower()
                                       or "message sent" in body.lower()
                                       or "queued" in body.lower())
        return ok, body or f"HTTP {r.status_code}"
    except Exception as exc:                      # noqa: BLE001
        return False, f"error: {type(exc).__name__}"


# --------------------------------------------------------------------------- #
def send_telegram(s, message: str) -> Tuple[bool, str]:
    if not (s.telegram_token and s.telegram_chat_id):
        return False, "skipped (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set)"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{s.telegram_token}/sendMessage",
            json={"chat_id": s.telegram_chat_id, "text": _short(message, 4000),
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=30,
        )
        data = r.json()
        if not data.get("ok"):                    # retry once without HTML
            r = requests.post(
                f"https://api.telegram.org/bot{s.telegram_token}/sendMessage",
                json={"chat_id": s.telegram_chat_id, "text": _short(message, 4000),
                      "disable_web_page_preview": True}, timeout=30)
            data = r.json()
        return bool(data.get("ok")), str(data.get("description", data.get("ok")))
    except Exception as exc:                      # noqa: BLE001
        return False, f"error: {type(exc).__name__}"


# --------------------------------------------------------------------------- #
# ntfy.sh — FREE instant push notification to your phone (no account, no signup)
#   Setup: install the "ntfy" app (Android/iPhone) -> subscribe to a secret topic
#   name you invent, e.g. wfh-rajesh-7k2p9 -> put that name in NTFY_TOPIC.
#   Tapping a notification opens the job's apply page (we send one per job).
# --------------------------------------------------------------------------- #
def send_ntfy(s, message: str, title: str = "WFH Job Bot", priority: str = "default",
              click: str | None = None, tags: str = "house,briefcase") -> Tuple[bool, str]:
    if not s.ntfy_topic:
        return False, "skipped (NTFY_TOPIC not set)"
    server = (s.ntfy_server or "https://ntfy.sh").rstrip("/")
    # HTTP headers must be ASCII-safe -> strip emoji/non-latin from the title,
    # ntfy shortcodes (heavy_check_mark, warning...) give you the emoji instead.
    ascii_title = (title or "").encode("ascii", "ignore").decode("ascii").strip() or "WFH Job Bot"
    headers = {"Title": ascii_title, "Priority": priority, "Tags": tags}
    if click:
        headers["Click"] = click
    try:
        r = requests.post(f"{server}/{s.ntfy_topic}",
                          data=message.encode("utf-8"), headers=headers, timeout=30)
        if r.status_code == 200:
            return True, "delivered"
        return False, f"HTTP {r.status_code}: {r.text.strip()[:110]}"
    except Exception as exc:                      # noqa: BLE001
        return False, f"error: {type(exc).__name__}"


def send_ntfy_jobs(s, jobs) -> dict:
    """One phone notification per job - tap it and the job page opens."""
    if not s.ntfy_topic:
        return {"ntfy": "SKIP — skipped (NTFY_TOPIC not set)"}
    sent, first_err, last = 0, "", ""
    for j in jobs:
        title = f"{j.trust}% | {j.title[:60]}"
        bits = " | ".join(b for b in [j.company, j.location, j.salary] if b)
        flags = ("\n⚠ " + "; ".join(j.red_flags[:2])) if j.red_flags else ""
        body = f"{bits}{flags}\nTap to open this job and apply."
        tags = ("heavy_check_mark" if j.trust >= 75 else
                "warning" if j.trust >= 55 else "skull")
        ok, info = send_ntfy(s, body, title=title, click=app_link(s, j),
                             priority="high" if j.trust >= 75 else "default",
                             tags=f"house,{tags}")
        last = info
        if ok:
            sent += 1
        elif not first_err:
            first_err = info
        time.sleep(1.1)                            # stay inside ntfy's rate limit
    if sent:
        return {"ntfy": f"OK — {sent} separate job notification(s) sent"}
    return {"ntfy": f"{'OK' if sent else 'FAIL'} — {first_err or last}"}


# --------------------------------------------------------------------------- #
# Green API — sends WhatsApp from YOUR OWN number. Free "Developer" plan:
#   unlimited messages/month to up to 3 chats (you only need 1: yourself).
#   Setup: console.green-api.com -> free account -> create instance (Developer)
#   -> scan the QR with WhatsApp (Linked devices) -> copy idInstance +
#   apiTokenInstance -> put them in GREENAPI_ID_INSTANCE / GREENAPI_API_TOKEN.
# --------------------------------------------------------------------------- #
def send_greenapi(s, message: str) -> Tuple[bool, str]:
    if not (s.greenapi_id and s.greenapi_token):
        return False, "skipped (GREENAPI_ID_INSTANCE / GREENAPI_API_TOKEN not set)"
    chat = s.greenapi_chat_id or _digits(s.callmebot_phone)
    if not chat:
        return False, "skipped (set GREENAPI_CHAT_ID, e.g. 919876543210@c.us)"
    if not chat.endswith("@c.us"):
        chat = f"{chat}@c.us"
    try:
        r = requests.post(
            f"https://api.green-api.com/waInstance{s.greenapi_id}/sendMessage/{s.greenapi_token}",
            json={"chatId": chat, "message": _short(message, 18000)}, timeout=40)
        try:
            data = r.json()
        except Exception:                         # noqa: BLE001
            data = {}
        ok = r.status_code == 200 and bool(data.get("idMessage"))
        info = data.get("idMessage") or data.get("message") or f"HTTP {r.status_code}"
        return ok, str(info)[:150]
    except Exception as exc:                      # noqa: BLE001
        return False, f"error: {type(exc).__name__}"


# --------------------------------------------------------------------------- #
def send_email(s, subject: str, body: str, html: str | None = None) -> Tuple[bool, str]:
    if not (s.smtp_host and s.smtp_user and s.smtp_pass and s.mail_to):
        return False, "skipped (SMTP settings not set)"
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = s.smtp_user, s.mail_to, subject
        msg.set_content(body)
        if html:
            msg.add_alternative(html, subtype="html")
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30) as srv:
            srv.starttls()
            srv.login(s.smtp_user, s.smtp_pass)
            srv.send_message(msg)
        return True, "sent"
    except Exception as exc:                      # noqa: BLE001
        return False, f"error: {type(exc).__name__}"


# --------------------------------------------------------------------------- #
TRACKABLE_HOSTS = ("linkedin.com", "naukri.com", "apna.co", "jooble.org")


def app_link(s, job) -> str:
    """One-tap apply link. A tracker tag is added only on job-portal hosts
    (adding it to ATS links like Greenhouse/Lever can break them)."""
    if not any(h in job.url for h in TRACKABLE_HOSTS):
        return job.url
    sep = "&" if "?" in job.url else "?"
    return f"{job.url}{sep}utm_source=wfh_job_bot&bot_score={job.trust}&src=wfhbot"


def build_summary_message(s, new_jobs: List, run_note: str = "") -> str:
    """Short WhatsApp-friendly alert."""
    lines = [f"🔔 WFH JOB BOT — {len(new_jobs)} new job(s)", ""]
    for i, j in enumerate(new_jobs, 1):
        badge = "🟢" if j.trust >= 75 else ("🟡" if j.trust >= 60 else "🟠")
        lines.append(f"{badge} {i}) {j.title[:62]}")
        bits = [b for b in [j.company, j.location or "", j.salary] if b]
        lines.append("   " + " | ".join(bits)[:105])
        warn = ("  ⚠ " + "; ".join(j.red_flags[:2])) if j.red_flags else ""
        lines.append(f"   Trust {j.trust}/100{warn}")
        lines.append(f"   👉 {app_link(s, j)}")
        lines.append("")
    if run_note:
        lines.append(run_note)
    lines.append("⚠ Never pay any registration/training/deposit fee — a real employer never asks.")
    return "\n".join(lines)


def build_heartbeat_message(report: dict) -> str:
    src = report.get("sources", {})
    lines = ["🤖 WFH JOB BOT is alive — 0 new jobs since the last check.", ""]
    for name, status in src.items():
        lines.append(f"• {name}: {status}")
    lines.append("")
    lines.append("If a source says 'blocked', that site is refusing cloud IPs — "
                 "run the bot on your home Wi-Fi for that one.")
    return "\n".join(lines)


def _tag(ok: bool, info: str) -> str:
    if info.startswith("skipped"):
        return f"SKIP — {info}"
    return f"{'OK' if ok else 'FAIL'} — {info}"


def send_all(s, message: str, html: str | None = None) -> dict:
    results = {}
    if s.alerts.get("whatsapp", True):
        ok, info = send_whatsapp(s, _strip_markup(message))
        results["whatsapp"] = _tag(ok, info)
    if s.alerts.get("greenapi", True):
        ok, info = send_greenapi(s, _strip_markup(message))
        results["whatsapp_greenapi"] = _tag(ok, info)
    if s.alerts.get("telegram", True):
        ok, info = send_telegram(s, message)
        results["telegram"] = _tag(ok, info)
    if s.alerts.get("ntfy", True):
        ok, info = send_ntfy(s, _strip_markup(message))
        results["ntfy"] = _tag(ok, info)
    if s.alerts.get("email", False):
        ok, info = send_email(s, "WFH Job Bot alert", _strip_markup(message), html)
        results["email"] = _tag(ok, info)
    return results


def channel_status(s) -> dict:
    """What is configured, for --test and the run report."""
    return {
        "ntfy":            "configured" if s.ntfy_topic else "NOT SET (NTFY_TOPIC)",
        "telegram":        "configured" if (s.telegram_token and s.telegram_chat_id)
                           else "NOT SET (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)",
        "whatsapp_greenapi": "configured" if (s.greenapi_id and s.greenapi_token)
                           else "NOT SET (GREENAPI_ID_INSTANCE / GREENAPI_API_TOKEN)",
        "whatsapp_callmebot": "configured" if (s.callmebot_phone and s.callmebot_apikey)
                           else "NOT SET (CALLMEBOT_PHONE / CALLMEBOT_APIKEY)",
        "email":           "configured" if (s.smtp_host and s.smtp_user)
                           else "NOT SET (SMTP_*)",
    }


def notify_new_jobs(s, jobs, message: str, html: str | None = None) -> dict:
    """Job alerts: ntfy gets one notification per job, everything else gets the summary."""
    results = {}
    if s.alerts.get("whatsapp", False):
        ok, info = send_whatsapp(s, _strip_markup(message))
        results["whatsapp_callmebot"] = _tag(ok, info)
    if s.alerts.get("greenapi", True):
        ok, info = send_greenapi(s, _strip_markup(message))
        results["whatsapp_greenapi"] = _tag(ok, info)
    if s.alerts.get("telegram", True):
        ok, info = send_telegram(s, message)
        results["telegram"] = _tag(ok, info)
    if s.alerts.get("ntfy", True):
        results.update(send_ntfy_jobs(s, jobs))
    if s.alerts.get("email", False):
        ok, info = send_email(s, "WFH Job Bot alert", _strip_markup(message), html)
        results["email"] = _tag(ok, info)
    return results


def _strip_markup(text: str) -> str:
    """Remove HTML tags for plain-text channels."""
    import re

    return re.sub(r"<[^>]+>", "", text)
